"""Geração determinística de trechos dos documentos a partir do formulário (especificacao.prumo.json).

Cada trecho gerado fica entre marcadores com o hash do que o Prumo escreveu:

    <!-- prumo:gerado:contexto h=3f9a21c0 -->
    ...
    <!-- prumo:gerado:fim -->

Regras (docs/formulario-de-especificacao.md, seção 5.1):
- conteúdo bate com o hash (ninguém mexeu): reescrito a partir do formulário;
- editado depois (pelo Claude ou por você): não é tocado;
- seção sem marcador: só é preenchida se ainda tem apenas lacunas [PREENCHER] (texto seu nunca é apagado);
- bloco editado: itens do formulário cujo ID ainda não aparece no bloco são acrescentados (linha ou subseção);
- documento aprovado: não é tocado.
O briefing não tem marcadores no modelo (regra da seção sem marcador). Os demais modelos trazem os marcadores sem
hash; `selar` grava o hash quando o Prumo cria o documento. O conteúdo de cada bloco está em geradores.py.
"""

import re

from . import formulario, geradores, i18n
from .util import (LACUNA_EN, MARCADOR_LACUNA, ErroPrumo, gravar, hash_texto, ler, renderizar, sem_comentarios,
                   tabela_markdown, tem_lacuna)

BRIEFING = "docs/00-briefing.md"
INICIO = re.compile(r"<!-- prumo:gerado:([a-z0-9-]+)(?: h=([0-9a-f]{8}))? -->\n(.*?)<!-- prumo:gerado:fim -->", re.S)
SECAO = re.compile(r"^## (\d+)\. .*$", re.M)
CELULAS_EN = {"Primário": "Primary", "Secundário": "Secondary", "Sim": "Yes", "Não": "No", "sim": "yes", "não": "no",
              "aberta": "open", "pública": "public", "Identificador": "Identifier", "Usabilidade": "Usability",
              "Privacidade": "Privacy", "Segurança": "Security", "Desempenho": "Performance",
              "Disponibilidade": "Availability", "Acessibilidade": "Accessibility", "Compatibilidade": "Compatibility"}
ROTULOS_DE_LINHA = {"Ator principal", "Atores secundários", "Requisitos atendidos", "Regras de negócio", "Telas",
                    "Pré-condições", "Pós-condições", "Gatilho", "Arquivo do Figma", "Biblioteca de componentes",
                    "Tipografia", "Paleta / tokens", "Convenção de nomes", "ORM / migrações", "Versão"}
DICAS_EN = {"marco": "milestone", "benefício": "benefit", "contexto": "context", "ação": "action", "resultado": "result",
            "perfil": "profile", "quem": "who", "O ator...": "The actor...", "O sistema...": "The system..."}  # dicas de uma palavra nas lacunas (fora do catálogo: "contexto" é comando)
ROTULOS_EN = {"Validade da proposta": "Proposal valid for"}  # rótulo da linha no modelo em inglês
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
CONTATO = re.compile(r"^\| (?:Contato principal|Main contact) \| (.*) \|$", re.M)


def _contato(d):
    c = d["contato"]
    return ", ".join(v.strip() for v in (c["nome"], c["email"], c["telefone"]) if v.strip())


# ---------------------------------------------------------------- aplicação

def selar(texto):
    """Grava o hash nos marcadores sem hash (os dos modelos), para `gerar` saber que ninguém mexeu neles."""
    return INICIO.sub(lambda m: m.group(0) if m.group(2) else
                      f"<!-- prumo:gerado:{m.group(1)} h={_h(m.group(3))} -->\n{m.group(3)}<!-- prumo:gerado:fim -->", texto)


def selar_arquivo(caminho):
    texto = ler(caminho)
    novo = selar(texto)
    if novo != texto:
        gravar(caminho, novo)


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


def _traduzir_gerado(texto, idioma):
    """Texto gerado no idioma do projeto. Os geradores escrevem em português e misturam rótulos fixos com dados do
    formulário e dos catálogos; por isso palavra solta só é traduzida em cabeçalho de tabela ou como primeira
    célula inteira (rótulo de linha). O resto usa só as frases do catálogo."""
    cat = i18n.catalogo(idioma)
    texto = re.sub(re.escape(MARCADOR_LACUNA) + r": ([^\]\n]*)\]",
                   lambda m: f"{LACUNA_EN}: {DICAS_EN.get(m.group(1)) or i18n.traduzir(m.group(1), idioma)}]", texto)  # dica: texto nosso
    linhas = texto.split("\n")
    for i, linha in enumerate(linhas):
        if linha.startswith("|") and i + 1 < len(linhas) and SEPARADOR.match(linhas[i + 1]):
            linhas[i] = i18n.traduzir(linha, idioma)
        elif linha.startswith("|"):
            celulas = linha.split("|")
            for j, c in enumerate(celulas):
                fixo = CELULAS_EN.get(c.strip()) or (cat.get(c.strip()) if c.strip() in ROTULOS_DE_LINHA else None)
                celulas[j] = f" {fixo} " if fixo else i18n.traduzir(c, idioma, frases=True)
            linhas[i] = "|".join(celulas)
        else:
            linhas[i] = i18n.traduzir(linha, idioma, frases=True)
    return "\n".join(linhas).replace(MARCADOR_LACUNA, LACUNA_EN)


def _no_idioma(idioma):
    """Função que passa o texto gerado (em português) para o idioma do projeto, com a lacuna [FILL]."""
    if not str(idioma or "").lower().startswith("en"):
        return lambda texto: texto
    return lambda texto: _traduzir_gerado(texto, "en") if texto else texto


def _traduzido(funcao, traduzir):
    def gerar_no_idioma(*args):
        novo = funcao(*args)
        if isinstance(novo, geradores.Bloco):
            return geradores.Bloco(traduzir(novo.texto), [(c, traduzir(f)) for c, f in novo.itens], novo.modo)
        return traduzir(novo)
    return gerar_no_idioma


def gerar_briefing(texto, dados, catalogos=None, idioma=None):
    """(texto novo, {bloco: estado}) do briefing preenchido com o formulário."""
    catalogos = catalogos or formulario.carregar_catalogos()
    traduzir = _no_idioma(idioma)
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
            corpo, estados[nome] = _secao(corpo, nome, traduzir(funcao(dados, catalogos)))
        saida += [cabecalhos[i], corpo]
    return "".join(saida), estados


def _acrescentar(conteudo, bloco):
    """(conteúdo com os itens que faltam, IDs acrescentados). Um item está presente se a chave aparece no bloco."""
    faltam = [(c, f) for c, f in bloco.itens if not re.search(rf"(?<![\w-]){re.escape(c)}(?![\w-])", conteudo)]
    if not faltam:
        return conteudo, []
    if bloco.modo == "linhas":
        linhas = conteudo.rstrip("\n").split("\n")
        ultima = max((i for i, l in enumerate(linhas) if l.lstrip().startswith("|")), default=len(linhas) - 1)
        linhas[ultima + 1:ultima + 1] = [f for _, f in faltam]
        return "\n".join(linhas) + "\n", [c for c, _ in faltam]
    return conteudo.rstrip("\n") + "\n\n" + "\n\n".join(f for _, f in faltam) + "\n", [c for c, _ in faltam]


def aplicar_blocos(texto, geradores_doc, dados, catalogos, ctx, modelo=None, sobrescrever=()):
    """(texto novo, {bloco: estado}, {bloco: [IDs acrescentados]}) de um documento com marcadores.

    Estados: gerado (era o exemplo do modelo), atualizado, igual, limpo (formulário esvaziado: volta o exemplo do
    modelo), vazio (sem dados no formulário), editado (mexeram no bloco; nada a acrescentar), acrescentado.
    `modelo` é {bloco: marcador completo} do modelo selado, para restaurar o exemplo e reconhecer o estado inicial.
    """
    modelo = modelo or {}
    estados, acrescentados = {}, {}

    def trocar(m):
        nome = m.group(1)
        if nome not in geradores_doc or nome in estados:
            return m.group(0)
        novo = geradores_doc[nome](dados, catalogos, ctx)
        bloco = novo if isinstance(novo, geradores.Bloco) else geradores.Bloco(novo or "")
        intacto = m.group(2) is not None and _h(m.group(3)) == m.group(2)
        if intacto or nome in sobrescrever:
            if not bloco.texto.strip():
                original = modelo.get(nome)
                if original and original != m.group(0) and not (intacto and m.group(0) == original):
                    estados[nome] = "limpo"
                    return original
                estados[nome] = "vazio"
                return m.group(0)
            gerado = _bloco(nome, bloco.texto)
            estados[nome] = "igual" if gerado == m.group(0) else (
                "gerado" if m.group(0) == modelo.get(nome) else "atualizado")
            return gerado
        conteudo, novos = _acrescentar(m.group(3), bloco)
        if novos:
            acrescentados[nome] = novos
            estados[nome] = "acrescentado"
            return f"<!-- prumo:gerado:{nome} h={m.group(2)} -->\n{conteudo}<!-- prumo:gerado:fim -->" if m.group(2) else \
                f"<!-- prumo:gerado:{nome} h=00000000 -->\n{conteudo}<!-- prumo:gerado:fim -->"
        estados[nome] = "editado"
        return m.group(0)

    texto = INICIO.sub(trocar, texto)
    return texto, estados, acrescentados


def _preencher_linhas(texto, linhas, dados):
    """Linhas `| Rótulo | valor |` de cabeçalho: preenchidas só enquanto o valor ainda é lacuna."""
    estados = {}
    for rotulo, funcao in linhas:
        valor = funcao(dados)
        rotulos = "|".join(re.escape(r) for r in (rotulo, ROTULOS_EN.get(rotulo, rotulo)))
        m = re.search(rf"^\| (?:{rotulos}) \| (.*) \|$", texto, re.M)
        if not m or not valor:
            continue
        nome = geradores.identificador(rotulo, "tabela").replace("_", "-")
        if tem_lacuna(m.group(1)):
            texto = texto[:m.start(1)] + _cel(valor) + texto[m.end(1):]
            estados[nome] = "gerado"
        else:
            estados[nome] = "igual" if m.group(1) == _cel(valor) else "editado"
    return texto, estados


def _inventario(texto, dados, catalogos, ctx, traduzir=lambda x: x):
    """Inventário de telas (bloco prumo:figma): acrescenta as telas do formulário que ainda não estão lá.

    Enquanto o inventário só tem a linha de exemplo, ela sai. Linhas do Figma e manuais nunca são reescritas.
    """
    from .figma import FIM as FIG_FIM, INICIO as FIG_INICIO
    itens = geradores.interface_inventario(dados, catalogos, ctx)
    if not itens or FIG_INICIO not in texto or FIG_FIM not in texto:
        return texto, None
    antes, resto = texto.split(FIG_INICIO, 1)
    trecho, depois = resto.split(FIG_FIM, 1)
    linhas = trecho.strip("\n").split("\n")
    exemplo = [l for l in linhas[2:] if tem_lacuna(l.split("|")[2])] if len(linhas) > 2 else []
    reais = [l for l in linhas[2:] if l not in exemplo]
    if not reais:
        linhas = linhas[:2]
    presentes = "\n".join(linhas)
    novos = [traduzir(l) for tl, l in itens if not re.search(rf"\| {tl} \|", presentes)]
    if not novos:
        return texto, "igual"
    linhas += novos
    return f"{antes}{FIG_INICIO}\n" + "\n".join(linhas) + f"\n{FIG_FIM}{depois}", "acrescentado"


def _modelo(projeto, rel):
    """{bloco: marcador} do modelo do documento, renderizado e selado como na criação."""
    caminho = projeto.modelo("documentos/" + rel[len("docs/"):])
    if not caminho.is_file():
        return {}
    texto = selar(renderizar(ler(caminho), projeto.contexto()))
    return {m.group(1): m.group(0) for m in INICIO.finditer(texto)}


def gerar(projeto, simular=False, sobrescrever=()):
    """Aplica o formulário aos documentos. Devolve {documento: {bloco: estado}}, os alterados e os IDs acrescentados.

    `sobrescrever`: ["docs/02-requisitos.md:rf", ...] reescreve esses blocos mesmo editados.
    """
    dados, existe = formulario.carregar(projeto)
    if not existe:
        return {"existe": False, "documentos": {}, "alterados": [], "acrescentados": {}}
    erros = formulario.estrutura(dados)
    if erros:
        raise ErroPrumo("Formulário com erro de estrutura:\n  " + "\n  ".join(erros))
    catalogos = formulario.carregar_catalogos(projeto.idioma)
    ctx = geradores.Contexto(projeto.config.get("documentos"), projeto.config.get("projeto", ""))
    forcar = {}
    for item in sobrescrever or ():
        doc, _, bloco = item.rpartition(":")
        if not doc or not bloco:
            raise ErroPrumo(f"Use <documento>:<bloco> em --sobrescrever (ex.: docs/02-requisitos.md:rf), não '{item}'.")
        forcar.setdefault(doc if doc.startswith("docs/") else f"docs/{doc}", set()).add(bloco)
    aprovados = projeto.config.get("aprovados") or {}
    traduzir = _no_idioma(projeto.idioma)
    resultado, alterados, acrescentados = {}, [], {}
    for rel in [BRIEFING] + list(geradores.DOCUMENTOS):
        caminho = projeto.raiz / rel
        if not caminho.is_file():
            continue
        if rel in aprovados:
            resultado[rel] = {"documento": "aprovado"}
            continue
        antes = ler(caminho)
        if rel == BRIEFING:
            depois, estados = gerar_briefing(antes, dados, catalogos, projeto.idioma)
        else:
            docs = {k: _traduzido(f, traduzir) for k, f in geradores.DOCUMENTOS[rel].items()}
            depois, estados, novos = aplicar_blocos(antes, docs, dados, catalogos, ctx,
                                                    _modelo(projeto, rel), forcar.get(rel, ()))
            linhas_doc = [(r, _traduzido(f, traduzir)) for r, f in geradores.LINHAS.get(rel, [])]
            depois, linhas = _preencher_linhas(depois, linhas_doc, dados)
            estados.update(linhas)
            if rel == "docs/05-interface.md":
                depois, inv = _inventario(depois, dados, catalogos, ctx, traduzir)
                if inv:
                    estados["inventario"] = inv
            if novos:
                acrescentados[rel] = novos
        if not estados:
            continue
        resultado[rel] = estados
        if depois != antes:
            alterados.append(rel)
            if not simular:
                gravar(caminho, depois)
    return {"existe": True, "documentos": resultado, "alterados": alterados, "acrescentados": acrescentados,
            "simulado": simular}
