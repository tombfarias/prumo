"""Status, validação, contexto compacto e extração de diagramas."""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import estilo, rastreio
from .util import contar_lacunas, gravar, hash_conteudo, ler, sem_comentarios

TIPOS_MERMAID = {
    "graph", "flowchart", "sequenceDiagram", "classDiagram", "stateDiagram", "stateDiagram-v2", "erDiagram",
    "journey", "gantt", "pie", "quadrantChart", "requirementDiagram", "gitGraph", "mindmap", "timeline",
    "C4Context", "C4Container", "C4Component", "C4Dynamic", "C4Deployment", "sankey-beta", "xychart-beta",
    "block-beta", "packet-beta", "kanban", "architecture-beta", "radar-beta", "treemap-beta",
}
BLOCO_MERMAID = re.compile(r"^```mermaid[ \t]*\n(.*?)^```", re.S | re.M)


def blocos_mermaid(texto):
    """[(numero_da_linha, codigo)] dos blocos ```mermaid de um texto."""
    saida = []
    for m in BLOCO_MERMAID.finditer(texto):
        linha = texto.count("\n", 0, m.start()) + 2
        saida.append((linha, m.group(1)))
    return saida


def checar_mermaid(codigo):
    """Verificação leve (sem navegador): tipo do diagrama e blocos abertos/fechados. Retorna mensagens de erro."""
    linhas = [l.strip() for l in codigo.splitlines()]
    if linhas and linhas[0] == "---":  # frontmatter de configuração
        try:
            linhas = linhas[linhas.index("---", 1) + 1:]
        except ValueError:
            return ["frontmatter '---' sem fechamento"]
    uteis = [l for l in linhas if l and not l.startswith("%%")]
    if not uteis:
        return ["bloco vazio"]
    tipo = uteis[0].split()[0]
    if tipo not in TIPOS_MERMAID:
        return [f"tipo de diagrama desconhecido: '{tipo}'"]
    erros = []
    if tipo in ("flowchart", "graph"):
        abertos = sum(1 for l in uteis if re.match(r"subgraph\b", l))
        fechados = sum(1 for l in uteis if l == "end")
        if abertos != fechados:
            erros.append(f"{abertos} subgraph para {fechados} end")
        for l in uteis[1:]:
            if re.search(r"(^|[\s>-])end\s*(\[|\(|\{|-->|---)", l):
                erros.append("'end' usado como nome de nó (palavra reservada); use outro nome, como 'fim'")
                break
    if tipo == "sequenceDiagram":
        abertos = sum(1 for l in uteis if re.match(r"(alt|opt|loop|par|critical|break|rect|box)\b", l))
        fechados = sum(1 for l in uteis if l == "end")
        if abertos != fechados:
            erros.append(f"{abertos} blocos (alt/opt/loop...) para {fechados} end")
    for i, l in enumerate(uteis if tipo in ("flowchart", "graph") else [], 1):
        for a, f in ("[]", "()", "{}"):
            if l.count(a) != l.count(f) and '"' not in l:
                erros.append(f"linha {i}: '{a}' e '{f}' desbalanceados: {l[:60]}")
                break
    return erros


def checar_mermaid_mmdc(codigo):
    """Validação completa com o mermaid-cli (mmdc), se estiver instalado."""
    exe = shutil.which("mmdc")
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        entrada = Path(tmp) / "d.mmd"
        entrada.write_text(codigo, encoding="utf-8")
        r = subprocess.run([exe, "-i", str(entrada), "-o", str(Path(tmp) / "d.svg")], capture_output=True, text=True)
        if r.returncode != 0:
            linhas = [l.strip() for l in (r.stderr or r.stdout).splitlines() if l.strip()]
            msg = next((l for l in linhas if re.search(r"(parse error|error:|expecting|syntax)", l, re.I)
                        and not l.startswith("at ")), linhas[0] if linhas else "erro no mermaid-cli")
            return [msg[:200]]
    return []


def status(projeto):
    aprovados = projeto.config.get("aprovados") or {}
    linhas = []
    for arq in projeto.arquivos_docs():
        rel = projeto.rel(arq)
        lacunas = contar_lacunas(ler(arq))
        if rel in aprovados:
            estado = "aprovado" + (" (ALTERADO)" if hash_conteudo(arq) != aprovados[rel].get("sha256") else "")
        else:
            estado = "completo" if lacunas == 0 else "em andamento"
        linhas.append({"documento": rel, "lacunas": lacunas, "estado": estado})
    analise = rastreio.analisar_projeto(projeto)
    contagem = {t: len(analise.do_tipo(t)) for t in rastreio.PREFIXOS if analise.do_tipo(t)}
    return linhas, contagem


def validar(projeto, estrito=False, mmdc=False):
    """Retorna lista de (gravidade, mensagem)."""
    resultado = []
    aprovados = projeto.config.get("aprovados") or {}
    for rel, info in sorted(aprovados.items()):
        caminho = projeto.raiz / rel
        if not caminho.exists():
            resultado.append(("erro", f"{rel} está aprovado mas o arquivo não existe"))
        elif hash_conteudo(caminho) != info.get("sha256"):
            resultado.append(("erro", f"{rel} foi alterado depois de aprovado em {info.get('data', '?')} "
                                      "(registre um pedido de mudança e reaprove)"))
    for doc in projeto.config.get("documentos") or []:
        if not (projeto.raiz / doc).exists():
            resultado.append(("aviso", f"{doc} está listado em projeto.prumo.json mas não existe"))

    for arq in projeto.arquivos_docs():
        rel = projeto.rel(arq)
        texto = ler(arq)
        lacunas = contar_lacunas(texto)
        if lacunas:
            resultado.append(("erro" if estrito else "aviso", f"{rel}: {lacunas} lacuna(s) [PREENCHER]"))
        restos = set(re.findall(r"\{\{\w+\}\}", sem_comentarios(texto)))
        if restos:
            resultado.append(("aviso", f"{rel}: marcadores de modelo não substituídos: {', '.join(sorted(restos))}"))
        for linha, codigo in blocos_mermaid(texto):
            erros = checar_mermaid(codigo)
            if not erros and mmdc:
                erros = checar_mermaid_mmdc(codigo) or []
            for e in erros:
                resultado.append(("erro", f"{rel}:{linha}: Mermaid: {e}"))
        resultado.extend(_avisos_de_estilo(rel, texto, idioma=projeto.idioma))

    analise = rastreio.analisar_projeto(projeto)
    for gravidade, msg in rastreio.problemas(analise, projeto):
        resultado.append(("erro" if estrito and gravidade == "aviso" else gravidade, msg))
    return resultado


def _avisos_de_estilo(rel, texto, limite=8, idioma="pt-BR"):
    """Avisos de concisão (docs/guia-de-escrita.md). O briefing guarda as palavras do cliente: sem checar termos vagos."""
    achados = estilo.checar(texto, vagos=not rel.endswith("00-briefing.md"), idioma=idioma)
    avisos = [("aviso", f"{rel}:{linha}: estilo: {msg}") for linha, msg in achados[:limite]]
    if len(achados) > limite:
        avisos.append(("aviso", f"{rel}: estilo: mais {len(achados) - limite} aviso(s) neste documento"))
    return avisos


# ---------------------------------------------------------------- contexto compacto

ORDEM_CONTEXTO = ("EP", "HU", "UC", "RF", "RNF", "RN", "TL", "CT", "SEG", "ADR", "CM")


def contexto(projeto, ids, profundidade=1):
    """Texto com os blocos do(s) item(ns) e dos itens ligados (citados por ele ou que o citam)."""
    analise = rastreio.analisar_projeto(projeto)
    faltando = [i for i in ids if i not in analise.itens]
    if faltando:
        from .util import ErroPrumo
        raise ErroPrumo(f"ID não encontrado: {', '.join(faltando)}")
    selecionados = set(ids)
    fronteira = set(ids)
    for _ in range(max(1, profundidade)):
        proxima = set()
        for ident in fronteira:
            item = analise.itens[ident]
            proxima |= {r for r in item.refs if r in analise.itens}
            proxima |= {i.id for i in analise.itens.values() if ident in i.refs}
        proxima -= selecionados
        selecionados |= proxima
        fronteira = proxima
    # Para histórias, inclua também os requisitos e regras dos casos de uso (a trilha completa).
    for ident in list(selecionados):
        if rastreio.tipo_de(ident) == "UC" and any(rastreio.tipo_de(i) == "HU" for i in ids):
            selecionados |= {r for r in analise.itens[ident].refs if r in analise.itens}

    def chave(ident):
        t = rastreio.tipo_de(ident)
        return (0 if ident in ids else 1, ORDEM_CONTEXTO.index(t) if t in ORDEM_CONTEXTO else 99, rastreio.numero_de(ident))

    partes = [f"<!-- prumo contexto {' '.join(ids)}: {len(selecionados)} itens ligados -->"]
    for ident in sorted(selecionados, key=chave):
        item = analise.itens[ident]
        corpo = "\n".join(l for l in item.texto).strip()
        corpo = re.sub(r"\n{3,}", "\n\n", corpo)
        partes.append(f"\n<!-- {item.arquivo}:{item.linha} -->\n{corpo}")
    codigo = set()
    for ident in selecionados:
        codigo |= analise.codigo.get(ident, set())
    if codigo:
        partes.append("\n<!-- arquivos de código que citam estes IDs -->\n" + "\n".join(f"- {a}" for a in sorted(codigo)))
    return "\n".join(partes) + "\n"


# ---------------------------------------------------------------- diagramas

def extrair_diagramas(projeto):
    destino = projeto.docs / "diagramas"
    if destino.exists():
        for antigo in destino.glob("*.mmd"):
            antigo.unlink()
    gerados = []
    for arq in projeto.arquivos_docs():
        texto = ler(arq)
        base = projeto.rel(arq)[len("docs/"):-3].replace("/", "-")
        for n, (_linha, codigo) in enumerate(blocos_mermaid(texto), 1):
            caminho = destino / f"{base}-{n}.mmd"
            gravar(caminho, codigo)
            gerados.append(projeto.rel(caminho))
    return gerados
