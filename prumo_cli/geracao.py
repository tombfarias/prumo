"""Geração determinística de trechos dos documentos a partir do formulário (especificacao.prumo.json).

Cada trecho gerado fica entre marcadores com o hash do que o Prumo escreveu:

    <!-- prumo:gerado:contexto h=3f9a21c0 -->
    ...
    <!-- prumo:gerado:fim -->

Regras (docs/formulario-de-especificacao.md, seção 5.1):
- conteúdo bate com o hash (ninguém mexeu): reescrito a partir do formulário;
- editado depois (pelo Claude ou por você): não é tocado;
- seção sem marcador: só é preenchida se ainda tem apenas lacunas [PREENCHER] (texto seu nunca é apagado);
- documento aprovado: não é tocado.
Por enquanto gera o briefing (docs/00-briefing.md); os demais documentos chegam nas próximas fases.
"""

import re

from . import formulario
from .util import MARCADOR_LACUNA, ErroPrumo, tem_lacuna, gravar, hash_texto, ler, sem_comentarios, tabela_markdown

BRIEFING = "docs/00-briefing.md"
INICIO = re.compile(r"<!-- prumo:gerado:([a-z0-9-]+) h=([0-9a-f]{8}) -->\n(.*?)<!-- prumo:gerado:fim -->", re.S)
SECAO = re.compile(r"^## (\d+)\. .*$", re.M)
SEPARADOR = re.compile(r"^\|(\s*:?-{3,}:?\s*\|)+\s*$")


def _h(texto):
    return hash_texto(texto)[:8]


def _bloco(nome, conteudo):
    conteudo = conteudo.strip("\n") + "\n"
    return f"<!-- prumo:gerado:{nome} h={_h(conteudo)} -->\n{conteudo}<!-- prumo:gerado:fim -->"


def _cel(texto):
    return str(texto or "").replace("|", "\\|").replace("\n", " ").strip()


def _so_lacunas(corpo):
    """True se a seção ainda é o modelo: toda linha com conteúdo é lacuna [PREENCHER] ou cabeçalho de tabela."""
    linhas = [l.strip() for l in sem_comentarios(corpo).splitlines()]
    for i, linha in enumerate(linhas):
        if not linha or tem_lacuna(linha) or SEPARADOR.match(linha):
            continue
        if linha.startswith("|") and i + 1 < len(linhas) and SEPARADOR.match(linhas[i + 1]):
            continue  # cabeçalho da tabela
        return False
    return True


# ---------------------------------------------------------------- conteúdo de cada seção do briefing

def _contexto(d):
    return d["negocio"]["contexto"].strip()


def _problema(d):
    p, n = d["negocio"]["problema"], d["negocio"]
    partes = [("Problema", p["problema"]), ("Afeta", p["afeta"]), ("Impacto", p["impacto"]),
              ("Solução esperada", p["solucao"]), ("Propósito", n["proposito"])]
    return "\n".join(f"- **{r}:** {v.strip()}" for r, v in partes if v.strip())


def _objetivos(d):
    linhas = []
    for o in d["negocio"]["objetivos"]:
        if not str(o.get("descricao", "")).strip():
            continue
        extra = "; ".join(x for x in (f"medida: {o['medida']}" if o.get("medida") else "",
                                      f"meta: {o['meta']}" if o.get("meta") else "") if x)
        linhas.append(f"- {o['descricao'].strip()}" + (f" ({extra})" if extra else ""))
    return "\n".join(linhas)


def _usuarios(d):
    linhas = []
    for a in d["atores"]:
        if not str(a.get("nome", "")).strip():
            continue
        extra = [a.get("descricao", "").strip()]
        if a.get("tipo") == "sistema":
            extra.append("sistema externo")
        if a.get("dispositivos"):
            extra.append("usa " + ", ".join(a["dispositivos"]))
        extra = "; ".join(x for x in extra if x)
        linhas.append(f"- **{a['nome'].strip()}**" + (f": {extra}" if extra else ""))
    perfis = [p for p in d["tecnico"]["perfis_acesso"] if p.strip()]
    if perfis:
        linhas.append(f"- **Perfis de acesso:** {', '.join(perfis)}")
    return "\n".join(linhas)


def _funcionalidades(d):
    linhas = []
    for f in d["funcionalidades"]:
        if not str(f.get("acao", "")).strip():
            continue
        quem = f"{f['ator']}: " if f.get("ator") else ""
        extra = ", ".join(x for x in (f.get("prioridade", ""), f.get("grupo", "")) if x)
        linhas.append(f"- {quem}{f['acao'].strip()}" + (f" ({extra})" if extra else "")
                      + (f". Para {f['beneficio'].strip()}." if f.get("beneficio") else ""))
    regras = [r for r in d["regras"] if str(r.get("regra", "")).strip()]
    if regras:
        linhas += ["", "**Regras citadas:**", ""]
        linhas += [f"- {r['regra'].strip()}" + (f" (ex.: {r['exemplo'].strip()})" if r.get("exemplo") else "") for r in regras]
    fora = [x for x in d["fora_do_escopo"] if x.strip()]
    if fora:
        linhas += ["", "**Fora do escopo:**", ""] + [f"- {x.strip()}" for x in fora]
    glossario = [g for g in d["glossario"] if str(g.get("termo", "")).strip()]
    if glossario:
        linhas += ["", "**Termos do cliente:**", ""]
        linhas += [f"- **{g['termo'].strip()}:** {g.get('definicao', '').strip() or MARCADOR_LACUNA + ']'}" for g in glossario]
    return "\n".join(linhas).strip()


def _restricoes(d):
    r = d["restricoes"]
    if not any(str(v).strip() for v in r.values()):
        return ""
    lac = MARCADOR_LACUNA + "]"
    return tabela_markdown(["Tipo", "Descrição"], [
        ["Prazo", _cel(r["prazo"]) or lac], ["Orçamento", _cel(r["orcamento_cliente"]) or lac],
        ["Tecnologia", _cel(r["tecnologia"]) or lac], ["Legal / LGPD", _cel(r["legal"]) or lac]])


def _escolhidos(d, catalogos):
    login = formulario.indice(catalogos, "logins").get(d["tecnico"]["login"])
    integ = formulario.indice(catalogos, "integracoes")
    return login, [integ.get(i) or {"id": i, "nome": i} for i in d["tecnico"]["integracoes"] if i.strip()]


def _integracoes(d, catalogos):
    login, integracoes = _escolhidos(d, catalogos)
    linhas = [f"- {i['nome']}" + (f" (ator: {i['ator']})" if i.get("ator") else "") for i in integracoes]
    if login:
        linhas.append(f"- Login: {login['nome']}")
    return "\n".join(linhas)


def _referencias(d):
    return "\n".join(f"- {r.strip()}" for r in d["negocio"]["referencias"] if r.strip())


def _perguntas(d, catalogos):
    login, integracoes = _escolhidos(d, catalogos)
    itens = [(p["pergunta"], p.get("bloqueia"), p.get("impacta", "")) for p in d["perguntas"]
             if str(p.get("pergunta", "")).strip()]
    vistas = {_cel(p).casefold() for p, _, _ in itens}
    for origem in ([login] if login else []) + integracoes:
        for p in origem.get("perguntas") or []:
            if _cel(p["pergunta"]).casefold() not in vistas:
                vistas.add(_cel(p["pergunta"]).casefold())
                itens.append((p["pergunta"], p.get("bloqueia"), origem["nome"]))
    if not itens:
        return ""
    return tabela_markdown(["ID", "Pergunta", "Bloqueia", "Impacta", "Status / resposta"], [
        [f"P-{n:02d}", _cel(p), "Sim" if b else "Não", _cel(i), "aberta"] for n, (p, b, i) in enumerate(itens, 1)])


SECOES_BRIEFING = {  # número da seção em 00-briefing.md -> (bloco, função)
    1: ("contexto", lambda d, c: _contexto(d)),
    2: ("problema", lambda d, c: _problema(d)),
    3: ("objetivos", lambda d, c: _objetivos(d)),
    4: ("usuarios", lambda d, c: _usuarios(d)),
    5: ("funcionalidades", lambda d, c: _funcionalidades(d)),
    6: ("restricoes", lambda d, c: _restricoes(d)),
    7: ("integracoes", _integracoes),
    8: ("referencias", lambda d, c: _referencias(d)),
    9: ("perguntas", _perguntas),
}
CONTATO = re.compile(r"^\| Contato principal \| (.*) \|$", re.M)


def _contato(d):
    c = d["contato"]
    return ", ".join(v.strip() for v in (c["nome"], c["email"], c["telefone"]) if v.strip())


# ---------------------------------------------------------------- aplicação

def _secao(corpo, nome, novo):
    """(novo corpo, estado) de uma seção. Estados: gerado, atualizado, igual, limpo, editado, vazio."""
    m = INICIO.search(corpo)
    if m:
        if m.group(1) != nome or _h(m.group(3)) != m.group(2):
            return corpo, "editado"
        if not novo:  # campo apagado no formulário: volta a ser lacuna
            return corpo[:m.start()] + MARCADOR_LACUNA + "]" + corpo[m.end():], "limpo"
        bloco = _bloco(nome, novo)
        return (corpo, "igual") if bloco == m.group(0) else (corpo[:m.start()] + bloco + corpo[m.end():], "atualizado")
    if not novo:
        return corpo, "vazio"
    if not _so_lacunas(corpo):
        return corpo, "editado"
    comentarios = "\n\n".join(re.findall(r"<!--.*?-->", corpo, re.S))
    return "\n\n" + (comentarios + "\n\n" if comentarios else "") + _bloco(nome, novo) + "\n\n", "gerado"


def gerar_briefing(texto, dados, catalogos=None):
    """(texto novo, {bloco: estado}) do briefing preenchido com o formulário."""
    catalogos = catalogos or formulario.carregar_catalogos()
    estados = {}
    contato = _contato(dados)
    m = CONTATO.search(texto)
    if m and contato:
        if tem_lacuna(m.group(1)):
            texto = texto[:m.start(1)] + _cel(contato) + texto[m.end(1):]
            estados["contato"] = "gerado"
        else:
            estados["contato"] = "igual" if m.group(1) == _cel(contato) else "editado"
    partes = SECAO.split(texto)  # [antes, n1, corpo1, n2, corpo2, ...]
    saida = [partes[0]]
    titulos = SECAO.findall(texto)
    cabecalhos = [x.group(0) for x in SECAO.finditer(texto)]
    for i, (num, corpo) in enumerate(zip(titulos, partes[2::2])):
        n = int(num)
        if n in SECOES_BRIEFING:
            nome, funcao = SECOES_BRIEFING[n]
            corpo, estados[nome] = _secao(corpo, nome, funcao(dados, catalogos))
        saida += [cabecalhos[i], corpo]
    return "".join(saida), estados


def gerar(projeto, simular=False):
    """Aplica o formulário aos documentos. Devolve {documento: {bloco: estado}} e se algo mudou."""
    dados, existe = formulario.carregar(projeto)
    if not existe:
        return {"existe": False, "documentos": {}, "alterados": []}
    erros = formulario.estrutura(dados)
    if erros:
        raise ErroPrumo("Formulário com erro de estrutura:\n  " + "\n  ".join(erros))
    resultado, alterados = {}, []
    caminho = projeto.raiz / BRIEFING
    if caminho.is_file():
        if BRIEFING in (projeto.config.get("aprovados") or {}):
            resultado[BRIEFING] = {"documento": "aprovado"}
        else:
            antes = ler(caminho)
            depois, estados = gerar_briefing(antes, dados)
            resultado[BRIEFING] = estados
            if depois != antes:
                alterados.append(BRIEFING)
                if not simular:
                    gravar(caminho, depois)
    return {"existe": True, "documentos": resultado, "alterados": alterados, "simulado": simular}
