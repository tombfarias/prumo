"""Conteúdo dos blocos `prumo:gerado` de cada documento, derivado do formulário (especificacao.prumo.json).

Cada gerador recebe (formulário normalizado, catálogos, contexto) e devolve um `Bloco` ou texto. Texto vazio = sem
dados: o bloco fica como está no modelo. Regras de derivação em docs/formulario-de-especificacao.md, seção 5.3.
"""

import re
import unicodedata

from . import formulario
from .util import MARCADOR_LACUNA, config_freelancer, formatar_horas, tabela_markdown

LAC = MARCADOR_LACUNA + "]"


def lac(dica):
    return f"{MARCADOR_LACUNA}: {dica}]"


class Bloco:
    """Texto do bloco e, para semear um bloco já editado, os itens (chave, fragmento).

    modo 'linhas': fragmento é uma linha de tabela (entra depois da última linha da tabela);
    modo 'secoes': fragmento é uma subseção (entra no fim do bloco). A chave é o ID que, presente no bloco, indica
    que o item já está lá.
    """

    def __init__(self, texto, itens=(), modo="linhas"):
        self.texto, self.itens, self.modo = texto, list(itens), modo


class Contexto:
    """O que os geradores precisam além do formulário: documentos do projeto e tabela de horas."""

    def __init__(self, documentos=None, projeto="", tamanhos=None):
        self.documentos = set(documentos or [])
        self.projeto = projeto
        self.tamanhos = tamanhos or formulario.opcoes()["tamanhos"]

    def tem(self, doc_id):
        return not self.documentos or f"docs/{doc_id}.md" in self.documentos

    def cita(self, lista):
        """Só os IDs cujo documento de definição existe no projeto (evita ID citado e não definido)."""
        return [i for i in lista or [] if self.tem(_DEFINE.get(re.sub(r"[-\d]+$", "", i), "02-requisitos"))]


_DEFINE = {"RF": "02-requisitos", "RN": "02-requisitos", "UC": "03-casos-de-uso", "TL": "05-interface", "M": "08-backlog"}


# ---------------------------------------------------------------- utilitários

def cel(texto):
    return str(texto if texto is not None else "").replace("\n", " ").strip()


def tabela(cabecalho, linhas):
    return tabela_markdown(cabecalho, [[cel(c) for c in linha] for linha in linhas])


def linha_tabela(celulas):
    return tabela(["x"] * len(celulas), [celulas]).splitlines()[2]


def maiuscula(texto):
    texto = texto.strip()
    return texto[:1].upper() + texto[1:]


def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def identificador(nome, estilo="classe"):
    """Nome de classe (PascalCase), de tabela (snake_case) ou de entidade ER (MAIÚSCULAS)."""
    partes = re.findall(r"[A-Za-z0-9]+", sem_acento(nome)) or ["Item"]
    if estilo == "classe":
        nome = "".join(p[:1].upper() + p[1:] for p in partes)
    else:
        nome = "_".join(p.lower() for p in partes)
        nome = nome.upper() if estilo == "er" else nome
    return ("_" + nome) if nome[0].isdigit() else nome


def rotulo_mermaid(texto):
    return cel(texto).replace('"', "'").replace("[", "(").replace("]", ")")


def ids(lista):
    return ", ".join(lista)


def funcionalidades(d):
    return [f for f in d["funcionalidades"] if str(f.get("acao", "")).strip() and f.get("id")]


def prioridade(f):
    return f.get("prioridade") or ""


def escopo_base(f):
    return prioridade(f) in ("Must", "Should", "")


def grupos(d):
    """[(grupo, [funcionalidades])] na ordem em que aparecem; sem grupo vai para 'Funcionalidades principais'."""
    saida = {}
    for f in funcionalidades(d):
        if prioridade(f) == "Won't":
            continue
        saida.setdefault(f.get("grupo", "").strip() or "Funcionalidades principais", []).append(f)
    return list(saida.items())


def ucs_por_rf(d):
    saida = {}
    for uc in d["casos_de_uso"]:
        for rf in uc.get("requisitos") or []:
            if uc.get("id"):
                saida.setdefault(rf, []).append(uc["id"])
    return saida


def horas(f, ctx):
    valor = ctx.tamanhos.get(f.get("tamanho") or "")
    return formatar_horas(valor) if isinstance(valor, (int, float)) else None


def escolhidos(d, cat):
    """(login do catálogo ou None, [integrações do catálogo]); 'nenhum' conta como sem login."""
    login = formulario.indice(cat, "logins").get(d["tecnico"]["login"])
    if login and login["id"] == "nenhum":
        login = None
    integ = formulario.indice(cat, "integracoes")
    return login, [integ.get(i) or {"id": i, "nome": i} for i in d["tecnico"]["integracoes"] if i.strip()]


def stack_nome(d, cat, camada):
    valor = d["tecnico"]["stack"].get(camada, "").strip()
    item = formulario.indice(cat, "stacks").get(valor)
    return item["nome"] if item else valor


_USUARIO = {"usuario", "usuarios", "user", "users", "conta", "contas"}


def entidades(d, cat):
    """Entidades do formulário; com login e sem entidade de usuário, acrescenta `Usuario` (seção 5.3)."""
    ents = [e for e in d["entidades"] if str(e.get("nome", "")).strip()]
    login, _ = escolhidos(d, cat)
    if login and not any(identificador(e["nome"], "tabela") in _USUARIO for e in ents):
        campos = [{"nome": "email", "tipo": "email", "obrigatorio": True, "unico": True}]
        if login["id"] == "email-senha":
            campos.append({"nome": "senha_hash", "tipo": "senha", "obrigatorio": True})
        ents.append({"nome": "Usuario", "descricao": f"Conta de acesso ({login['nome']})", "campos": campos,
                     "relacoes": [], "automatica": True})
    return ents


def campos(ent):
    return [c for c in ent.get("campos") or [] if str(c.get("nome", "")).strip()]


def relacoes(ent):
    return [r for r in ent.get("relacoes") or [] if str(r.get("com", "")).strip()]


def pessoal(campo, cat):
    tipo = formulario.indice(cat, "tipos-de-campo").get(campo.get("tipo") or "")
    return bool(campo.get("pessoal")) or bool(tipo and tipo["pessoal"])


def dados_pessoais(d, cat):
    """[(entidade, campo)] com dado pessoal."""
    return [(e, c) for e in entidades(d, cat) for c in campos(e) if pessoal(c, cat)]


def tipo_diagrama(campo, cat):
    tipo = formulario.indice(cat, "tipos-de-campo").get(campo.get("tipo") or "")
    return tipo["diagrama"] if tipo else "string"


_SQL = {"string": "text", "text": "text", "int": "integer", "decimal": "numeric(12,2)", "boolean": "boolean",
        "date": "date", "datetime": "timestamp", "json": "jsonb"}


def rnfs(d, cat):
    """RNFs marcados + os das integrações e do login + LGPD automático, sem repetir descrição."""
    login, integracoes = escolhidos(d, cat)
    indice = formulario.indice(cat, "rnf")
    marcados = list(d["tecnico"]["rnf"])
    if dados_pessoais(d, cat) and "lgpd" not in marcados and "lgpd" in indice:
        marcados.append("lgpd")
    itens = [indice[i] for i in marcados if i in indice]
    for origem in ([login] if login else []) + integracoes:
        itens += origem.get("rnf") or []
    saida, vistos = [], set()
    for item in itens:
        chave = item["descricao"].casefold()
        if chave not in vistos:
            vistos.add(chave)
            saida.append(item)
    return saida


def perguntas(d, cat):
    """[(pergunta, bloqueia, impacta)] do formulário e dos catálogos escolhidos, sem repetir."""
    login, integracoes = escolhidos(d, cat)
    itens = [(p["pergunta"].strip(), bool(p.get("bloqueia")), p.get("impacta", "")) for p in d["perguntas"]
             if str(p.get("pergunta", "")).strip()]
    vistas = {cel(p).casefold() for p, _, _ in itens}
    rnf = formulario.indice(cat, "rnf")
    origens = ([login] if login else []) + integracoes + [rnf[i] for i in d["tecnico"]["rnf"] if i in rnf]
    for origem in origens:
        for p in origem.get("perguntas") or []:
            if cel(p["pergunta"]).casefold() not in vistas:
                vistas.add(cel(p["pergunta"]).casefold())
                itens.append((p["pergunta"], bool(p.get("bloqueia")), origem.get("nome") or origem.get("categoria", "")))
    return itens


# ---------------------------------------------------------------- 01-visao

def visao_proposito(d, cat, ctx):
    return d["negocio"]["proposito"].strip()


def visao_problema(d, cat, ctx):
    p = d["negocio"]["problema"]
    if not any(v.strip() for v in p.values()):
        return ""
    return tabela(["", ""], [["**O problema de**", p["problema"] or LAC], ["**afeta**", p["afeta"] or lac("quem")],
                             ["**cujo impacto é**", p["impacto"] or LAC],
                             ["**uma solução bem-sucedida seria**", p["solucao"] or LAC]])


def visao_partes(d, cat, ctx):
    linhas = [[a["nome"], a.get("descricao") or LAC, "sistema externo" if a.get("tipo") == "sistema" else LAC]
              for a in d["atores"] if str(a.get("nome", "")).strip()]
    if not linhas:
        return ""
    return tabela(["Parte interessada / usuário", "Descrição", "Responsabilidades ou interesses"], linhas)


def visao_capacidades(d, cat, ctx):
    return "\n".join(f"- **{g}:** " + "; ".join(f["acao"].strip() for f in fs) for g, fs in grupos(d))


def visao_dentro(d, cat, ctx):
    return "\n".join(f"- {maiuscula(f['acao'])} ({f['id']})" for f in funcionalidades(d) if escopo_base(f))


def visao_fora(d, cat, ctx):
    itens = [f"{maiuscula(f['acao'])} ({f['id']})" for f in funcionalidades(d) if prioridade(f) == "Won't"]
    itens += [x.strip() for x in d["fora_do_escopo"] if x.strip()]
    opcionais = [f"{maiuscula(f['acao'])} ({f['id']}, opcional: orçado à parte)" for f in funcionalidades(d)
                 if prioridade(f) == "Could"]
    return "\n".join(f"- {x}" for x in itens + opcionais)


def visao_restricoes(d, cat, ctx):
    r = d["restricoes"]
    nomes = (("prazo", "Prazo"), ("orcamento_cliente", "Orçamento"), ("tecnologia", "Tecnologia"), ("legal", "Legal / LGPD"))
    return "\n".join(f"- **{rot}:** {r[k].strip()}" for k, rot in nomes if r[k].strip())


def visao_criterios(d, cat, ctx):
    linhas = [[o["descricao"], o.get("medida") or LAC, o.get("meta") or LAC] for o in d["negocio"]["objetivos"]
              if str(o.get("descricao", "")).strip()]
    return tabela(["Critério", "Como medir", "Meta"], linhas) if linhas else ""


# ---------------------------------------------------------------- 02-requisitos

def _descricao_rf(f):
    texto = f"O sistema deve permitir {f['acao'].strip().rstrip('.')}"
    texto += f" ({f['ator'].strip()})." if str(f.get("ator", "")).strip() else "."
    if f.get("regras"):
        texto += f" Regras: {ids(f['regras'])}."  # RN é definida no mesmo documento
    return texto


def requisitos_rf(d, cat, ctx):
    linhas = [[f["id"], _descricao_rf(f), prioridade(f) or lac("MoSCoW"), f.get("origem") or "Pedido"]
              for f in funcionalidades(d)]
    if not linhas:
        return ""
    return Bloco(tabela(["ID", "Descrição", "Prioridade", "Origem"], linhas),
                 [(l[0], linha_tabela(l)) for l in linhas])


def requisitos_rnf(d, cat, ctx):
    linhas = [[f"RNF-{n:03d}", r["categoria"], r["descricao"], r.get("metrica") or LAC]
              for n, r in enumerate(rnfs(d, cat), 1)]
    if not linhas:
        return ""
    return tabela(["ID", "Categoria", "Descrição", "Métrica / critério"], linhas)


def requisitos_rn(d, cat, ctx):
    linhas = [[r["id"], r["regra"], r.get("exemplo") or LAC] for r in d["regras"]
              if str(r.get("regra", "")).strip() and r.get("id")]
    if not linhas:
        return ""
    return Bloco(tabela(["ID", "Regra", "Exemplo"], linhas), [(l[0], linha_tabela(l)) for l in linhas])


def requisitos_glossario(d, cat, ctx):
    linhas = [[g["termo"], g.get("definicao") or LAC] for g in d["glossario"] if str(g.get("termo", "")).strip()]
    return tabela(["Termo", "Definição"], linhas) if linhas else ""


# ---------------------------------------------------------------- 03-casos-de-uso

def _ucs(d):
    return [uc for uc in d["casos_de_uso"] if str(uc.get("nome", "")).strip() and uc.get("id")]


def _atores_uc(d, cat):
    """[(nome, tipo, descrição)]: atores do formulário e os sistemas das integrações escolhidas."""
    principais = {formulario._chave(uc.get("ator")) for uc in _ucs(d)}
    saida = []
    for a in d["atores"]:
        if not str(a.get("nome", "")).strip():
            continue
        tipo = "Secundário (sistema)" if a.get("tipo") == "sistema" else (
            "Primário" if formulario._chave(a["nome"]) in principais or not principais else "Secundário")
        saida.append((a["nome"].strip(), tipo, a.get("descricao") or LAC))
    nomes = {formulario._chave(n) for n, _, _ in saida}
    login, integracoes = escolhidos(d, cat)
    for i in integracoes + ([login] if login else []):
        if i.get("ator") and formulario._chave(i["ator"]) not in nomes:
            nomes.add(formulario._chave(i["ator"]))
            saida.append((i["ator"], "Secundário (sistema)", i["nome"]))
    return saida


def uc_atores(d, cat, ctx):
    linhas = [list(a) for a in _atores_uc(d, cat)]
    return tabela(["Ator", "Tipo", "Descrição"], linhas) if linhas else ""


def uc_diagrama(d, cat, ctx):
    ucs = _ucs(d)
    if not ucs:
        return ""
    atores = {}
    for uc in ucs:
        if str(uc.get("ator", "")).strip():
            atores.setdefault(formulario._chave(uc["ator"]), (f"a{len(atores) + 1}", uc["ator"].strip()))
    linhas = ["```mermaid", "flowchart LR"]
    linhas += [f'    {n}(["{rotulo_mermaid(nome)}"])' for n, nome in atores.values()]
    linhas.append(f'    subgraph sistema["{rotulo_mermaid(ctx.projeto or "Sistema")}"]')
    linhas += [f'        uc{i}(("{uc["id"]} {rotulo_mermaid(uc["nome"])}"))' for i, uc in enumerate(ucs, 1)]
    linhas.append("    end")
    for i, uc in enumerate(ucs, 1):
        a = atores.get(formulario._chave(uc.get("ator")))
        if a:
            linhas.append(f"    {a[0]} --- uc{i}")
    return "\n".join(linhas + ["```"])


def uc_especificacoes(d, cat, ctx):
    regras_rf = {f["id"]: f.get("regras") or [] for f in funcionalidades(d)}
    secoes = []
    for uc in _ucs(d):
        regras = list(uc.get("regras") or [])
        for rf in uc.get("requisitos") or []:
            regras += [r for r in regras_rf.get(rf, []) if r not in regras]
        telas = ids(ctx.cita(uc.get("telas"))) or (lac("TL-xxx ou —") if ctx.tem("05-interface") else "—")
        secoes.append((uc["id"], "\n".join([
            f"### {uc['id']} — {maiuscula(uc['nome'])}", "",
            tabela(["Item", "Descrição"], [
                ["Ator principal", uc.get("ator") or LAC], ["Atores secundários", lac('ou "—"')],
                ["Requisitos atendidos", ids(ctx.cita(uc.get("requisitos"))) or lac("RF-xxx")],
                ["Regras de negócio", ids(ctx.cita(regras)) or "—"], ["Telas", telas],
                ["Pré-condições", LAC], ["Pós-condições", LAC], ["Gatilho", LAC]]), "",
            "#### Fluxo principal", "", f"1. {lac('O ator...')}", f"2. {lac('O sistema...')}", "",
            "#### Fluxos alternativos", "", f"- **FA-01 (passo 2):** {LAC}", "",
            "#### Fluxos de exceção", "", f"- **FE-01:** {lac('o que acontece em caso de erro')}"])))
    if not secoes:
        return ""
    return Bloco("\n\n".join(s for _, s in secoes), secoes, "secoes")


# ---------------------------------------------------------------- 04-uml/classes

_MULT = {"1:1": ('"1"', "--", '"1"'), "1:N": ('"1"', "-->", '"0..*"'), "N:1": ('"0..*"', "-->", '"1"'),
         "N:N": ('"0..*"', "--", '"0..*"')}


def classes_diagrama(d, cat, ctx):
    ents = entidades(d, cat)
    if not ents:
        return ""
    linhas = ["```mermaid", "classDiagram", "    direction LR"]
    for e in ents:
        corpo = [f"        +{tipo_diagrama(c, cat)} {identificador(c['nome'], 'tabela')}" for c in campos(e)]
        linhas += [f"    class {identificador(e['nome'])} {{"] + corpo + ["    }"] if corpo else [
            f"    class {identificador(e['nome'])}"]
    for e in ents:
        for r in relacoes(e):
            a, seta, b = _MULT.get(r.get("cardinalidade") or "", ("", "-->", ""))
            verbo = f" : {rotulo_mermaid(r['verbo'])}" if str(r.get("verbo", "")).strip() else ""
            partes = [identificador(e["nome"]), a, seta, b, identificador(r["com"])]
            linhas.append("    " + " ".join(x for x in partes if x) + verbo)
    return "\n".join(linhas + ["```"])


def classes_responsabilidades(d, cat, ctx):
    linhas = [[identificador(e["nome"]), e.get("descricao") or LAC, lac("UC-xxx") if ctx.tem("03-casos-de-uso") else "—"]
              for e in entidades(d, cat)]
    return tabela(["Classe", "Responsabilidade", "Casos de uso relacionados"], linhas) if linhas else ""


# ---------------------------------------------------------------- 05-interface

def _telas(d):
    return [t for t in d["interface"]["telas"] if str(t.get("nome", "")).strip() and t.get("id")]


def interface_design(d, cat, ctx):
    i = d["interface"]
    if not any(str(i[k]).strip() for k in ("figma", "biblioteca", "tipografia", "paleta", "breakpoints")):
        return ""
    return tabela(["Item", "Valor"], [
        ["Arquivo do Figma", i["figma"] or lac("URL")], ["Biblioteca de componentes", i["biblioteca"] or LAC],
        ["Tipografia", i["tipografia"] or LAC], ["Paleta / tokens", i["paleta"] or LAC],
        ["Breakpoints", i["breakpoints"] or lac("ex.: 640 / 768 / 1024 / 1280 px")]])


def interface_navegacao(d, cat, ctx):
    telas = _telas(d)
    if not telas:
        return ""
    nos = {t["id"]: f"tl{n}" for n, t in enumerate(telas, 1)}
    destinos = {v for t in telas for v in t.get("vai_para") or []}
    linhas = ["```mermaid", "flowchart LR", '    entrada(["Entrada"])']
    linhas += [f'    {nos[t["id"]]}["{t["id"]} {rotulo_mermaid(t["nome"])}"]' for t in telas]
    linhas += [f"    entrada --> {nos[t['id']]}" for t in telas if t["id"] not in destinos] or [
        f"    entrada --> {nos[telas[0]['id']]}"]
    for t in telas:
        linhas += [f"    {nos[t['id']]} --> {nos[v]}" for v in t.get("vai_para") or [] if v in nos]
    return "\n".join(linhas + ["```"])


def interface_telas(d, cat, ctx):
    nomes = {t["id"]: t["nome"] for t in _telas(d)}
    ucs = {}
    for uc in _ucs(d):
        for tl in uc.get("telas") or []:
            ucs.setdefault(tl, []).append(uc["id"])
    secoes = []
    for t in _telas(d):
        acoes = "; ".join(f"ir para {v} ({nomes.get(v, '')})".replace(" ()", "") for v in t.get("vai_para") or [])
        atende = ids(ctx.cita((t.get("atende") or []) + ucs.get(t["id"], []))) or lac("RF/RNF/UC")
        secoes.append((t["id"], "\n".join([
            f"### Tela {t['id']} — {maiuscula(t['nome'])}", "",
            f"- **Objetivo:** {t.get('objetivo') or LAC}" + (f" (ator: {t['ator']})" if t.get("ator") else ""),
            f"- **Conteúdo, na ordem:** {lac('blocos da tela')}",
            f"- **Ações:** " + (f"{acoes}; {lac('botões e formulários')}" if acoes else lac("botões e formulários e para onde levam")),
            f"- **Estados:** {lac('vazio, carregando, erro, sucesso, quando se aplicam')}",
            f"- **Atende:** {atende}"])))
    if not secoes:
        return ""
    return Bloco("\n\n".join(s for _, s in secoes), secoes, "secoes")


def interface_inventario(d, cat, ctx):
    """Linhas do inventário (bloco prumo:figma): [(TL, linha)]. Casos de uso vêm dos UCs que citam a tela."""
    ucs = {}
    for uc in _ucs(d):
        for tl in uc.get("telas") or []:
            ucs.setdefault(tl, []).append(uc["id"])
    padrao = lac("UC-xxx") if ctx.tem("03-casos-de-uso") else "—"
    return [(t["id"], linha_tabela([t["id"], t["nome"], "—", lac("link do frame") if d["interface"]["figma"] else "—",
                                    ids(ctx.cita(ucs.get(t["id"], []))) or padrao, "—"])) for t in _telas(d)]


# ---------------------------------------------------------------- 06-banco-de-dados

def banco_cabecalho(d, cat, ctx):
    sgbd, orm = stack_nome(d, cat, "banco"), stack_nome(d, cat, "orm")
    if not sgbd and not orm:
        return ""
    return tabela(["Campo", "Valor"], [
        ["SGBD", sgbd or lac("PostgreSQL 16, MySQL 8, SQLite...")],
        ["ORM / migrações", orm or lac("Prisma, Drizzle, SQLAlchemy + Alembic, EF Core...")],
        ["Convenção de nomes", "snake_case, tabelas no singular, chave primária `id`"], ["Versão", "0.1"]])


def _tabelas(d, cat):
    """{entidade: {'colunas': [(nome, tipo, nulo, restrições, descrição)], 'associativa': bool}} e ligações do ER."""
    ents = entidades(d, cat)
    nomes = {formulario._chave(e["nome"]): e for e in ents}
    saida, ligacoes = {}, []
    for e in ents:
        cols = [("id", "uuid", "não", "PK", "Identificador")]
        for c in campos(e):
            restr = "UK" if c.get("unico") else ""
            desc = "dado pessoal" if pessoal(c, cat) else ""
            cols.append((identificador(c["nome"], "tabela"), tipo_diagrama(c, cat), "não" if c.get("obrigatorio") else "sim",
                         restr, desc))
        saida[e["nome"]] = {"colunas": cols, "associativa": False}
    for e in ents:
        for r in relacoes(e):
            outra = nomes.get(formulario._chave(r["com"]))
            if not outra:
                continue
            card, verbo = r.get("cardinalidade") or "N:1", r.get("verbo") or "relaciona"
            a, b = e["nome"], outra["nome"]
            if card == "N:N":
                assoc = f"{identificador(a, 'tabela')}_{identificador(b, 'tabela')}"
                saida[assoc] = {"colunas": [("id", "uuid", "não", "PK", "Identificador"),
                                            (f"{identificador(a, 'tabela')}_id", "uuid", "não", "FK", f"→ {identificador(a, 'tabela')}"),
                                            (f"{identificador(b, 'tabela')}_id", "uuid", "não", "FK", f"→ {identificador(b, 'tabela')}")],
                                "associativa": True}
                ligacoes += [(a, "||--o{", assoc, verbo), (b, "||--o{", assoc, verbo)]
                continue
            dono, alvo, seta = (b, a, "||--o{") if card == "1:N" else (a, b, "}o--||") if card == "N:1" else (a, b, "||--||")
            col = f"{identificador(alvo, 'tabela')}_id"
            restr = "FK, UK" if card == "1:1" else "FK"
            if all(c[0] != col for c in saida[dono]["colunas"]):
                saida[dono]["colunas"].append((col, "uuid", "sim", restr, f"→ {identificador(alvo, 'tabela')}"))
            ligacoes.append((a, seta, b, verbo))
    return saida, ligacoes


def banco_er(d, cat, ctx):
    tabelas, ligacoes = _tabelas(d, cat)
    if not tabelas:
        return ""
    linhas = ["```mermaid", "erDiagram"]
    for a, seta, b, verbo in ligacoes:
        linhas.append(f'    {identificador(a, "er")} {seta} {identificador(b, "er")} : "{rotulo_mermaid(verbo)}"')
    for nome, t in tabelas.items():
        linhas.append(f"    {identificador(nome, 'er')} {{")
        for col, tipo, _nulo, restr, _desc in t["colunas"]:
            chaves = ",".join(x.strip() for x in restr.split(",") if x.strip())
            linhas.append(f"        {tipo} {col}" + (f" {chaves}" if chaves else ""))
        linhas.append("    }")
    return "\n".join(linhas + ["```"])


def banco_dicionario(d, cat, ctx):
    tabelas, _ = _tabelas(d, cat)
    ents = {e["nome"]: e for e in entidades(d, cat)}
    secoes = []
    for nome, t in tabelas.items():
        desc = (ents.get(nome) or {}).get("descricao") or ("tabela associativa (relação N:N)" if t["associativa"] else "")
        linhas = [[col, _SQL.get(tipo, tipo), nulo, "gen_random_uuid()" if col == "id" else "", restr,
                   "Identificador" if col == "id" else descr] for col, tipo, nulo, restr, descr in t["colunas"]]
        secoes.append(f"### Tabela `{identificador(nome, 'tabela')}`" + (f"\n\n{maiuscula(desc)}." if desc else "") + "\n\n"
                      + tabela(["Coluna", "Tipo", "Nulo", "Padrão", "Restrições", "Descrição"], linhas))
    return "\n\n".join(secoes)


def banco_lgpd(d, cat, ctx):
    nomes = {c["id"]: c["nome"] for c in cat.get("tipos-de-campo", [])}
    linhas = [[nomes.get(c.get("tipo"), c["nome"]), f"{identificador(e['nome'], 'tabela')}.{identificador(c['nome'], 'tabela')}",
               LAC, lac("consentimento, contrato..."), LAC, LAC] for e, c in dados_pessoais(d, cat)]
    if not linhas:
        return ""
    return tabela(["Dado pessoal", "Tabela.coluna", "Finalidade", "Base legal", "Retenção", "Proteção"], linhas)


# ---------------------------------------------------------------- 07-arquitetura

_CAMADAS = {"frontend": "Frontend", "backend": "Backend", "mobile": "Mobile", "banco": "Banco de dados",
            "orm": "ORM / migrações", "autenticacao": "Autenticação", "hospedagem": "Hospedagem", "testes": "Testes"}


def arquitetura_stack(d, cat, ctx):
    linhas = [[_CAMADAS.get(c, c), stack_nome(d, cat, c), LAC, LAC] for c in formulario.CAMADAS if stack_nome(d, cat, c)]
    return tabela(["Camada", "Tecnologia", "Versão", "Justificativa"], linhas) if linhas else ""


def arquitetura_integracoes(d, cat, ctx):
    login, integracoes = escolhidos(d, cat)
    linhas = []
    for i in integracoes + ([login] if login else []):
        variaveis = ", ".join(f"`{v}`" for v in i.get("variaveis") or [])
        auth = "; ".join(s["autenticacao"] for s in i.get("superficie") or []) or LAC
        linhas.append([i.get("ator") or i["nome"], i["nome"], auth + (f" (chaves: {variaveis})" if variaveis else ""),
                       "; ".join(a["controle"] for a in i.get("ameacas") or []) or lac("retry, fila, fallback")])
    if not linhas:
        return ""
    return tabela(["Sistema", "Finalidade", "Protocolo / autenticação", "Tratamento de falhas"], linhas)


def arquitetura_seguranca(d, cat, ctx):
    login, _ = escolhidos(d, cat)
    perfis = [p for p in d["tecnico"]["perfis_acesso"] if p.strip()]
    pessoais = [f"{identificador(e['nome'], 'tabela')}.{identificador(c['nome'], 'tabela')}" for e, c in dados_pessoais(d, cat)]
    if not login and not perfis and not pessoais and not d["tecnico"]["login"]:
        return ""
    auth = stack_nome(d, cat, "autenticacao")
    autenticacao = (login["nome"] + (f" ({auth})" if auth else "")) if login else (
        "sem login" if d["tecnico"]["login"] == "nenhum" else LAC)
    return "\n".join([
        f"- **Autenticação:** {autenticacao}",
        f"- **Autorização / perfis de acesso:** " + (", ".join(perfis) + "; " + lac("o que cada perfil pode fazer")
                                                    if perfis else LAC),
        "- **Segredos:** variáveis de ambiente; nunca versionadas (`.env` fica fora do git, `.env.example` documenta as chaves).",
        "- **Dados sensíveis:** " + (f"dados pessoais em {', '.join(pessoais)} (ver 06-banco-de-dados.md, seção 8); "
                                     + lac("criptografia, mascaramento em logs") if pessoais
                                     else lac("criptografia, mascaramento em logs"))])


# ---------------------------------------------------------------- 08-backlog

def _epicos(d):
    return [(f"EP-{n:02d}", g, fs) for n, (g, fs) in enumerate(grupos(d), 1)]


def backlog_epicos(d, cat, ctx):
    marco = _marcos(d)[0]["id"] if len(_marcos(d)) == 1 else ""
    linhas = [[ep, g, LAC, marco or lac("marco")] for ep, g, _ in _epicos(d)]
    return tabela(["ID", "Épico", "Objetivo", "Marco de entrega"], linhas) if linhas else ""


def _marcos(d):
    return [m for m in d["comercial"]["marcos"] if str(m.get("conteudo", "")).strip() and m.get("id")]


def _percentual(m):
    p = m.get("percentual")
    return f"{p:g}%" if isinstance(p, (int, float)) and not isinstance(p, bool) else LAC


def backlog_marcos(d, cat, ctx):
    linhas = [[m["id"], m["conteudo"], m.get("data") or LAC, _percentual(m)] for m in _marcos(d)]
    if not linhas:
        return ""
    return Bloco(tabela(["Marco", "Conteúdo", "Data prevista", "% do pagamento"], linhas),
                 [(l[0], linha_tabela(l)) for l in linhas])


def backlog_historias(d, cat, ctx):
    ucs = ucs_por_rf(d)
    secoes = []
    for ep, _g, fs in _epicos(d):
        for f in fs:
            hu = f"HU-{formulario._numero(f['id']):03d}"
            casos = ids(ctx.cita(ucs.get(f["id"], []))) or (lac("UC-xxx") if ctx.tem("03-casos-de-uso") else "—")
            beneficio = f.get("beneficio", "").strip().rstrip(".") or lac("benefício")
            h = horas(f, ctx)
            secoes.append((f["id"], "\n".join([
                f"### {hu} — {maiuscula(f['acao']).rstrip('.')}", "",
                f"**Épico:** {ep} · **Casos de uso:** {casos} · **Requisitos:** {f['id']}", "",
                f"**Como** {f.get('ator') or lac('perfil')}, **quero** {f['acao'].strip().rstrip('.')} **para** {beneficio}.", "",
                "**Critérios de aceite:**", "",
                f"- **Dado** {lac('contexto')}, **quando** {lac('ação')}, **então** {lac('resultado')}.", "",
                f"**Estimativa:** {h or LAC + 'h'} · **Prioridade:** {prioridade(f) or 'Must'} · **Status:** a fazer"])))
    if not secoes:
        return ""
    return Bloco("\n\n".join(s for _, s in secoes), secoes, "secoes")


# ---------------------------------------------------------------- 10-proposta-comercial

def proposta_validade(d):
    validade = d["comercial"]["validade_dias"]
    return "" if validade in (None, "") else f"{validade} dias"


def proposta_incluido(d, cat, ctx):
    return "\n".join(f"- **{g}:** " + "; ".join(f["acao"].strip() for f in fs if prioridade(f) != "Could")
                     for g, fs in grupos(d) if any(prioridade(f) != "Could" for f in fs))


def proposta_opcionais(d, cat, ctx):
    return "\n".join(f"- {maiuscula(f['acao'])} — {horas(f, ctx) or LAC + ' h'}" for f in funcionalidades(d)
                     if prioridade(f) == "Could")


def proposta_nao_incluido(d, cat, ctx):
    itens = [maiuscula(f["acao"]) for f in funcionalidades(d) if prioridade(f) == "Won't"]
    itens += [x.strip() for x in d["fora_do_escopo"] if x.strip()]
    return "\n".join(f"- {x}" for x in itens)


def proposta_cronograma(d, cat, ctx):
    linhas = [[m["id"], m["conteudo"], m.get("data") or LAC, _percentual(m)] for m in _marcos(d)]
    return tabela(["Marco", "Entregas", "Prazo", "Pagamento"], linhas) if linhas else ""


def proposta_condicoes(d, cat, ctx):
    c = d["comercial"]["condicoes"].strip()
    return f"**Condições de pagamento:** {c}" if c else ""


def proposta_perguntas(d, cat, ctx):
    return "\n".join(f"- {p.strip().rstrip('?')}? — {lac('efeito no escopo ou no preço')}"
                     for p, bloqueia, _ in perguntas(d, cat) if bloqueia)


def proposta_garantia(d, cat, ctx):
    dias = d["comercial"]["garantia_dias"]
    if dias in (None, ""):
        return ""
    return f"{dias} dias de correção de defeitos após a entrega final; {lac('suporte posterior por hora ou mensalidade')}"


# ---------------------------------------------------------------- 12-seguranca

def seguranca_superficie(d, cat, ctx):
    login, integracoes = escolhidos(d, cat)
    linhas = [[s["ponto"], s["exposicao"], s["autenticacao"], LAC]
              for i in ([login] if login else []) + integracoes for s in i.get("superficie") or []]
    return tabela(["Ponto de entrada", "Exposição", "Autenticação", "Dados tratados"], linhas) if linhas else ""


def seguranca_ameacas(d, cat, ctx):
    login, integracoes = escolhidos(d, cat)
    linhas = [[a["ameaca"], i["nome"], a["controle"], lac("CT-xxx")]
              for i in ([login] if login else []) + integracoes for a in i.get("ameacas") or []]
    return tabela(["Ameaça", "Onde", "Controle adotado", "Verificado em"], linhas) if linhas else ""


# documento -> {bloco: gerador}
DOCUMENTOS = {
    "docs/01-visao.md": {"proposito": visao_proposito, "problema": visao_problema, "partes-interessadas": visao_partes,
                         "capacidades": visao_capacidades, "dentro-do-escopo": visao_dentro,
                         "fora-do-escopo": visao_fora, "restricoes": visao_restricoes,
                         "criterios-de-sucesso": visao_criterios},
    "docs/02-requisitos.md": {"rf": requisitos_rf, "rnf": requisitos_rnf, "rn": requisitos_rn,
                              "glossario": requisitos_glossario},
    "docs/03-casos-de-uso.md": {"atores": uc_atores, "diagrama": uc_diagrama, "especificacoes": uc_especificacoes},
    "docs/04-uml/classes.md": {"diagrama": classes_diagrama, "responsabilidades": classes_responsabilidades},
    "docs/05-interface.md": {"design-system": interface_design, "navegacao": interface_navegacao,
                             "telas": interface_telas},
    "docs/06-banco-de-dados.md": {"cabecalho": banco_cabecalho, "er": banco_er, "dicionario": banco_dicionario,
                                  "lgpd": banco_lgpd},
    "docs/07-arquitetura.md": {"stack": arquitetura_stack, "integracoes": arquitetura_integracoes,
                               "seguranca": arquitetura_seguranca},
    "docs/08-backlog.md": {"epicos": backlog_epicos, "marcos": backlog_marcos, "historias": backlog_historias},
    "docs/10-proposta-comercial.md": {"incluido": proposta_incluido, "opcionais": proposta_opcionais,
                                      "nao-incluido": proposta_nao_incluido, "cronograma": proposta_cronograma,
                                      "condicoes": proposta_condicoes, "perguntas-valor": proposta_perguntas,
                                      "garantia": proposta_garantia},
    "docs/12-seguranca.md": {"superficie": seguranca_superficie, "ameacas": seguranca_ameacas},
}

# linhas de tabela de cabeçalho preenchidas só enquanto são lacuna: documento -> [(rótulo, função)]
LINHAS = {"docs/10-proposta-comercial.md": [("Validade da proposta", proposta_validade)]}
