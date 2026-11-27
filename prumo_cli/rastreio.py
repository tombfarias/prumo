"""Leitura dos IDs da especificação (RF, UC, HU...) e montagem da matriz de rastreabilidade."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .util import formatar_horas, gravar, hoje_br, ler, sem_comentarios, tabela_markdown

PREFIXOS = ("RNF", "RN", "RF", "UC", "HU", "CT", "TL", "EP", "SEG", "ADR", "CM")
PADRAO_ID = re.compile(r"\b(" + "|".join(PREFIXOS) + r")-(\d{2,4})\b")
TITULO = re.compile(r"^(#{1,6})\s+(.*)$")
CERCA = re.compile(r"^\s*(```|~~~)")
ID_SOZINHO = re.compile(r"^[*_`\s]*((?:" + "|".join(PREFIXOS) + r")-\d{2,4})[*_`\s]*(.*)$")
# Título que detalha um item já definido em outro lugar: uma palavra e o ID ("### Tela TL-001 — Home",
# "## Épico EP-01 — Cadastro"). O bloco soma texto e referências ao item, sem redefini-lo.
ID_DETALHADO = re.compile(r"^[*_`\s]*[^\W\d_]+\s+((?:" + "|".join(PREFIXOS) + r")-\d{2,4})\b")
NOMES = {
    "RF": "Requisito funcional", "RNF": "Requisito não funcional", "RN": "Regra de negócio",
    "UC": "Caso de uso", "HU": "História", "CT": "Caso de teste", "TL": "Tela", "EP": "Épico",
    "SEG": "Achado de segurança", "ADR": "Decisão arquitetural", "CM": "Mudança",
}
EXT_CODIGO = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro", ".java", ".kt",
    ".cs", ".go", ".rb", ".php", ".rs", ".dart", ".swift", ".sql", ".feature", ".html", ".css", ".scss",
}
IGNORAR_PASTAS = {"node_modules", ".git", "dist", "build", ".next", ".astro", ".venv", "venv", "__pycache__",
                  "coverage", ".prumo", "vendor", "target", ".dart_tool", "Pods"}


def tipo_de(ident):
    return ident.split("-")[0]


def numero_de(ident):
    return int(ident.split("-")[1])


def ordenar(ids):
    return sorted(ids, key=lambda i: (PREFIXOS.index(tipo_de(i)), numero_de(i)))


@dataclass
class Item:
    id: str
    titulo: str
    arquivo: str
    linha: int
    refs: set = field(default_factory=set)
    texto: list = field(default_factory=list)

    @property
    def tipo(self):
        return tipo_de(self.id)


@dataclass
class Analise:
    itens: dict = field(default_factory=dict)
    duplicados: list = field(default_factory=list)      # (id, arquivo, linha, arquivo_original)
    ocorrencias: dict = field(default_factory=dict)     # id -> [(arquivo, linha)]
    codigo: dict = field(default_factory=dict)          # id -> {arquivos}

    def do_tipo(self, *tipos):
        return [self.itens[i] for i in ordenar(i for i in self.itens if tipo_de(i) in tipos)]

    def citam(self, alvos, *tipos):
        """IDs dos itens dos tipos dados que citam algum dos alvos."""
        alvos = set(alvos)
        return {i.id for i in self.do_tipo(*tipos) if i.refs & alvos}

    def indefinidos(self):
        return {i: locais for i, locais in self.ocorrencias.items() if i not in self.itens}


def _limpar_titulo(texto):
    texto = re.sub(r"^[\s—–\-:·|]+", "", texto).strip()
    return texto.strip("*_` ")


def analisar_arquivo(analise, caminho, rel):
    texto = sem_comentarios(ler(caminho))
    pilha = []  # (nivel, item ou None)
    em_cerca = False

    def bloco_atual():
        for _nivel, item in reversed(pilha):
            if item is not None:
                return item
        return None

    def definir(ident, titulo, num_linha):
        if ident in analise.itens:
            original = analise.itens[ident]
            analise.duplicados.append((ident, rel, num_linha, f"{original.arquivo}:{original.linha}"))
            return None
        item = Item(ident, _limpar_titulo(titulo), rel, num_linha)
        analise.itens[ident] = item
        return item

    for num, linha in enumerate(texto.splitlines(), start=1):
        if CERCA.match(linha):
            em_cerca = not em_cerca
        ids_linha = [m.group(0) for m in PADRAO_ID.finditer(linha)]
        for ident in ids_linha:
            analise.ocorrencias.setdefault(ident, []).append((rel, num))

        if not em_cerca and (m := TITULO.match(linha)):
            nivel = len(m.group(1))
            while pilha and pilha[-1][0] >= nivel:
                pilha.pop()
            mid = ID_SOZINHO.match(m.group(2))
            item = definir(mid.group(1), mid.group(2), num) if mid else None
            if item is None and not mid:
                detalhe = ID_DETALHADO.match(m.group(2))
                item = analise.itens.get(detalhe.group(1)) if detalhe else None
            pilha.append((nivel, item))
            if item:
                item.texto.append(linha)
                item.refs.update(i for i in ids_linha if i != item.id)
                continue

        if not em_cerca and linha.strip().startswith("|") and not re.match(r"^\s*\|[\s:|-]+\|\s*$", linha):
            celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
            mid = ID_SOZINHO.match(celulas[0]) if celulas else None
            if mid and not mid.group(2):
                item = definir(mid.group(1), celulas[1] if len(celulas) > 1 else "", num)
                if item:
                    item.texto.append(linha)
                    item.refs.update(i for i in ids_linha if i != item.id)
                    continue

        atual = bloco_atual()
        if atual is not None:
            atual.texto.append(linha)
            atual.refs.update(i for i in ids_linha if i != atual.id)


def varrer_codigo(analise, raiz, pastas):
    for pasta in pastas:
        base = Path(raiz) / pasta
        if not base.is_dir():
            continue
        for dirpath, dirnames, arquivos in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in IGNORAR_PASTAS]
            for nome in arquivos:
                caminho = Path(dirpath) / nome
                if caminho.suffix.lower() not in EXT_CODIGO:
                    continue
                try:
                    if caminho.stat().st_size > 1_000_000:
                        continue
                    conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                rel = caminho.relative_to(raiz).as_posix()
                for m in PADRAO_ID.finditer(conteudo):
                    analise.codigo.setdefault(m.group(0), set()).add(rel)


def analisar_projeto(projeto):
    analise = Analise()
    for arq in projeto.arquivos_docs():
        analisar_arquivo(analise, arq, projeto.rel(arq))
    varrer_codigo(analise, projeto.raiz, projeto.config.get("pastas_codigo") or ["src", "tests"])
    return analise


# ---------------------------------------------------------------- problemas de cobertura

def _wont(item):
    return bool(re.search(r"\bWon'?t\b", " ".join(item.texto), re.I))


_PRIORIDADE = re.compile(r"Prioridade\W{0,4}\s*(Must|Should|Could|Won'?t)\b", re.I)


def prioridade(item):
    """Prioridade MoSCoW declarada no bloco (`**Prioridade:** Could`): 'must', 'should', 'could', 'wont' ou None."""
    m = _PRIORIDADE.search(" ".join(item.texto))
    return m.group(1).lower().replace("'", "") if m else None


def problemas(analise, projeto):
    """Lista de (gravidade, mensagem). gravidade: 'erro' ou 'aviso'."""
    saida = []
    for ident, locais in sorted(analise.indefinidos().items()):
        onde = ", ".join(f"{a}:{l}" for a, l in locais[:3])
        saida.append(("erro", f"{ident} é citado mas não está definido em lugar nenhum ({onde})"))
    for ident, arq, linha, original in analise.duplicados:
        saida.append(("erro", f"{ident} definido de novo em {arq}:{linha} (já definido em {original})"))

    existe = lambda nome: (projeto.docs / nome).exists()
    tem_uc, tem_hu, tem_ct, tem_tl = (existe("03-casos-de-uso.md"), existe("08-backlog.md"),
                                      existe("09-plano-de-testes.md"), existe("05-interface.md"))
    if tem_uc or tem_hu:
        for rf in analise.do_tipo("RF"):
            if _wont(rf):
                continue
            if not analise.citam([rf.id], "UC", "HU"):
                saida.append(("aviso", f"{rf.id} não é atendido por nenhum caso de uso ou história"))
    if tem_uc and tem_hu:
        for uc in analise.do_tipo("UC"):
            if not analise.citam([uc.id], "HU"):
                saida.append(("aviso", f"{uc.id} não tem história no backlog"))
    if tem_hu and tem_ct:
        for hu in analise.do_tipo("HU"):
            if prioridade(hu) in ("could", "wont"):  # opcionais e fora da entrega só ganham CT se entrarem no escopo
                continue
            if not analise.citam([hu.id], "CT"):
                saida.append(("aviso", f"{hu.id} não tem caso de teste"))
    if tem_tl and tem_uc:
        for tl in analise.do_tipo("TL"):
            ucs = {r for r in tl.refs if tipo_de(r) == "UC"} | analise.citam([tl.id], "UC")
            if not ucs:
                saida.append(("aviso", f"{tl.id} não está ligada a nenhum caso de uso"))
    return saida


# ---------------------------------------------------------------- matriz

def _lista(ids):
    return ", ".join(ordenar(ids)) if ids else "—"


def _arquivos(arquivos, limite=4):
    arquivos = sorted(arquivos)
    if not arquivos:
        return "—"
    texto = ", ".join(f"`{a}`" for a in arquivos[:limite])
    return texto + (f" (+{len(arquivos) - limite})" if len(arquivos) > limite else "")


def _codigo_de(analise, ids):
    arquivos = set()
    for i in ids:
        arquivos |= analise.codigo.get(i, set())
    return arquivos


def gerar_matriz(projeto, analise=None):
    analise = analise or analisar_projeto(projeto)
    partes = [
        f"# Matriz de Rastreabilidade — {projeto.config.get('projeto')}",
        "",
        f"> Gerado por `prumo rastreabilidade` em {hoje_br()}. Não edite à mão: rode o comando de novo.",
        "",
    ]
    contagem = [(NOMES[t], len(analise.do_tipo(t))) for t in PREFIXOS if analise.do_tipo(t)]
    partes += ["## Resumo", "", tabela_markdown(["Tipo", "Quantidade"], contagem), ""]

    linhas = []
    for req in analise.do_tipo("RF", "RNF"):
        ucs = analise.citam([req.id], "UC")
        telas = analise.citam([req.id] + list(ucs), "TL") | {
            r for i in [req.id, *ucs] for r in analise.itens[i].refs if tipo_de(r) == "TL"}
        # Ligações diretas primeiro; o caminho pelo caso de uso só entra quando nenhuma história cita o requisito.
        # Sem isso, toda história de um UC herdaria todos os requisitos dele e a matriz viraria ruído.
        hus = analise.citam([req.id], "HU") or analise.citam(list(ucs), "HU")
        cts = analise.citam([req.id] + list(hus), "CT")
        codigo = _codigo_de(analise, {req.id} | ucs | hus | cts)
        linhas.append([req.id, req.titulo[:80], _lista(ucs), _lista(telas), _lista(hus), _lista(cts), _arquivos(codigo)])
    if linhas:
        partes += ["## Requisitos → casos de uso → telas → histórias → testes → código", "",
                   tabela_markdown(["Requisito", "Descrição", "Casos de uso", "Telas", "Histórias", "Testes", "Código"],
                                   linhas), ""]

    linhas = []
    for rn in analise.do_tipo("RN"):
        citantes = analise.citam([rn.id], "UC", "HU")
        cts = analise.citam([rn.id], "CT")
        linhas.append([rn.id, rn.titulo[:80], _lista(citantes), _lista(cts), _arquivos(analise.codigo.get(rn.id, set()))])
    if linhas:
        partes += ["## Regras de negócio", "",
                   tabela_markdown(["Regra", "Descrição", "Aplicada em", "Testes", "Código"], linhas), ""]

    linhas = []
    for uc in analise.do_tipo("UC"):
        telas = {r for r in uc.refs if tipo_de(r) == "TL"} | analise.citam([uc.id], "TL")
        hus = analise.citam([uc.id], "HU")
        linhas.append([uc.id, uc.titulo[:60], _lista(telas), _lista(hus), _arquivos(_codigo_de(analise, {uc.id} | hus))])
    if linhas:
        partes += ["## Casos de uso", "", tabela_markdown(["Caso de uso", "Nome", "Telas", "Histórias", "Código"], linhas), ""]

    linhas = []
    for hu in analise.do_tipo("HU"):
        status = re.search(r"Status:\**\s*([^·|\n]+)", "\n".join(hu.texto))  # por linha: o texto seguinte não vaza
        horas = estimativa_horas(hu)
        cts = analise.citam([hu.id], "CT")
        linhas.append([hu.id, hu.titulo[:60], status.group(1).strip() if status else "—",
                       formatar_horas(horas) if horas is not None else "—", _lista(cts),
                       _arquivos(_codigo_de(analise, {hu.id} | cts))])
    if linhas:
        partes += ["## Histórias", "", tabela_markdown(["História", "Título", "Status", "Estimativa", "Testes", "Código"], linhas), ""]

    lista = problemas(analise, projeto)
    partes += ["## Problemas encontrados", ""]
    partes += [f"- **{g}:** {m}" for g, m in lista] if lista else ["Nenhum problema de rastreabilidade."]
    partes.append("")
    destino = projeto.docs / "rastreabilidade.md"
    gravar(destino, "\n".join(partes))
    return destino, lista


_ESTIMATIVA = re.compile(r"Estimativa\W{0,4}\s*(\d+(?:[.,]\d+)?)\s*(h|hs|horas?|d|dias?)\b", re.I)


def estimativa_horas(item, horas_dia=8):
    m = _ESTIMATIVA.search(" ".join(item.texto))
    if not m:
        return None
    valor = float(m.group(1).replace(",", "."))
    return valor * horas_dia if m.group(2).lower().startswith("d") else valor
