"""Formulário de especificação (especificacao.prumo.json): catálogos, validação e atribuição de IDs.

O formulário guarda **o que** o cliente quer em campos estruturados; `projeto.prumo.json` continua guardando **como**
o Prumo e os agentes se comportam. Tudo é opcional: campo vazio deixa a lacuna [PREENCHER] do modelo onde está.
IDs (RF, RN, UC, TL) são atribuídos ao salvar, depois do maior número já usado no formulário e nos documentos,
e nunca renumerados. Desenho completo em docs/formulario-de-especificacao.md.
"""

import copy
import re

from . import rastreio
from .util import MARCADOR_LACUNA, TEMPLATES, ErroPrumo, config_freelancer, gravar_json, ler_json

ARQUIVO = "especificacao.prumo.json"
VERSAO_FORMULARIO = 1
PASTA_CATALOGOS = TEMPLATES / "catalogos"
CATALOGOS = ("integracoes", "logins", "rnf", "stacks", "tipos-de-campo")
CAMADAS = ("frontend", "backend", "mobile", "banco", "orm", "autenticacao", "hospedagem", "testes")
PRIORIDADES = ("Must", "Should", "Could", "Won't")
TIPOS_ATOR = ("humano", "sistema")
CARDINALIDADES = ("1:1", "1:N", "N:1", "N:N")
TAMANHOS_PADRAO = {"P": 4, "M": 12, "G": 32}
_PRIORIDADE = dict({p.casefold(): p for p in PRIORIDADES}, wont="Won't")


def vazio():
    """Formulário sem nada preenchido: a forma completa de especificacao.prumo.json."""
    return {
        "versao": VERSAO_FORMULARIO,
        "contato": {"nome": "", "email": "", "telefone": ""},
        "negocio": {
            "contexto": "",
            "problema": {"problema": "", "afeta": "", "impacto": "", "solucao": ""},
            "proposito": "",
            "objetivos": [],
            "referencias": [],
        },
        "restricoes": {"prazo": "", "orcamento_cliente": "", "tecnologia": "", "legal": ""},
        "atores": [],
        "funcionalidades": [],
        "fora_do_escopo": [],
        "regras": [],
        "glossario": [],
        "perguntas": [],
        "casos_de_uso": [],
        "entidades": [],
        "interface": {"biblioteca": "", "tipografia": "", "paleta": "", "breakpoints": "", "figma": "", "telas": []},
        "tecnico": {"stack": {}, "login": "", "perfis_acesso": [], "integracoes": [], "rnf": []},
        "comercial": {"validade_dias": None, "condicoes": "", "garantia_dias": None, "marcos": []},
        "ultimo_id": {},  # maior número já usado por prefixo: ID apagado não volta a ser usado
    }


class Lista:
    """Uma lista de itens do formulário: rótulo nas mensagens, prefixo do ID, campo obrigatório e campos conhecidos."""

    def __init__(self, rotulo, prefixo, obrigatorio, campos, listas=()):
        self.rotulo, self.prefixo, self.obrigatorio = rotulo, prefixo, obrigatorio
        self.campos = set(campos) | set(listas) | ({"id"} if prefixo else set())
        self.listas = listas  # campos que são listas de textos


LISTAS = {
    "negocio.objetivos": Lista("Objetivo", None, "descricao", ("descricao", "medida", "meta")),
    "atores": Lista("Ator", None, "nome", ("nome", "tipo", "descricao"), ("dispositivos",)),
    "funcionalidades": Lista("Funcionalidade", "RF", "acao",
                             ("acao", "ator", "beneficio", "grupo", "prioridade", "tamanho", "origem"), ("regras",)),
    "regras": Lista("Regra", "RN", "regra", ("regra", "exemplo")),
    "glossario": Lista("Termo", None, "termo", ("termo", "definicao")),
    "perguntas": Lista("Pergunta", None, "pergunta", ("pergunta", "bloqueia", "impacta")),
    "casos_de_uso": Lista("Caso de uso", "UC", "nome", ("nome", "ator"), ("requisitos", "regras", "telas")),
    "entidades": Lista("Entidade", None, "nome", ("nome", "descricao", "campos", "relacoes")),
    "interface.telas": Lista("Tela", "TL", "nome", ("nome", "objetivo", "ator"), ("atende", "vai_para")),
    "comercial.marcos": Lista("Marco", "M", "conteudo", ("conteudo", "data", "percentual")),
}
SUBLISTAS = {  # listas dentro de cada entidade
    "campos": Lista("Campo", None, "nome", ("nome", "tipo", "obrigatorio", "unico", "pessoal")),
    "relacoes": Lista("Relação", None, "com", ("com", "cardinalidade", "verbo")),
}
LISTAS_TEXTO = ("negocio.referencias", "fora_do_escopo", "tecnico.perfis_acesso", "tecnico.integracoes", "tecnico.rnf")

# Passos do formulário na interface e os campos que contam para o indicador de preenchimento.
PASSOS = (
    ("negocio", "Negócio", ("negocio.contexto", "negocio.problema", "negocio.proposito", "negocio.objetivos",
                            "negocio.referencias", "restricoes")),
    ("usuarios", "Usuários", ("atores", "tecnico.perfis_acesso")),
    ("funcionalidades", "Funcionalidades", ("funcionalidades", "fora_do_escopo", "regras", "glossario")),
    ("casos_de_uso", "Casos de uso", ("casos_de_uso",)),
    ("dados", "Dados", ("entidades",)),
    ("telas", "Telas", ("interface.telas", "interface.biblioteca", "interface.tipografia", "interface.paleta",
                        "interface.breakpoints", "interface.figma")),
    ("tecnico", "Técnico", ("tecnico.stack", "tecnico.login", "tecnico.integracoes", "tecnico.rnf")),
    ("comercial", "Comercial", ("comercial.validade_dias", "comercial.condicoes", "comercial.garantia_dias",
                                "comercial.marcos")),
)


# ---------------------------------------------------------------- utilitários

def _no(dados, caminho):
    atual = dados
    for parte in caminho.split("."):
        if not isinstance(atual, dict):
            return None
        atual = atual.get(parte)
    return atual


def _preenchido(valor):
    if isinstance(valor, str):
        return bool(valor.strip())
    if isinstance(valor, dict):
        return any(_preenchido(v) for v in valor.values())
    if isinstance(valor, list):
        return any(_preenchido(v) for v in valor)
    if isinstance(valor, bool):
        return valor
    return valor is not None


def _chave(nome):
    return nome.strip().casefold() if isinstance(nome, str) else ""


def _lista_de_textos(valor):
    return isinstance(valor, list) and all(isinstance(v, str) for v in valor)


def _padrao_id(prefixo):
    return r"M\d{1,3}" if prefixo == "M" else prefixo + r"-\d{2,4}"


def _formatar_id(prefixo, numero):
    return f"M{numero}" if prefixo == "M" else f"{prefixo}-{numero:03d}"


def _numero(ident):
    return int(re.sub(r"\D", "", ident))


def _rotulo(lista, item, n):
    if item.get("id"):
        return f"{lista.rotulo} {item['id']}"
    nome = item.get(lista.obrigatorio)
    if isinstance(nome, str) and nome.strip():
        return f"{lista.rotulo} '{nome[:40]}'"
    return f"{lista.rotulo} {n}"


def _itens(dados, caminho):
    """Itens (objetos) de uma lista do formulário, com a posição, ignorando o que não é objeto."""
    valor = _no(dados, caminho)
    return [(n, i) for n, i in enumerate(valor, 1) if isinstance(i, dict)] if isinstance(valor, list) else []


# ---------------------------------------------------------------- catálogos

def carregar_catalogos():
    """{nome: [itens]} de templates/catalogos/*.json."""
    saida = {}
    for nome in CATALOGOS:
        dados = ler_json(PASTA_CATALOGOS / f"{nome}.json", None)
        if not isinstance(dados, dict) or not isinstance(dados.get("itens"), list):
            raise ErroPrumo(f"Catálogo ausente ou inválido: templates/catalogos/{nome}.json")
        saida[nome] = dados["itens"]
    return saida


def indice(catalogos, nome):
    return {i["id"]: i for i in catalogos.get(nome, []) if isinstance(i, dict) and "id" in i}


_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_VARIAVEL = re.compile(r"^[A-Z][A-Z0-9_]*$")
_PERMISSAO = re.compile(r"^\w+\(.+\)$")
_OBRIGATORIOS_CATALOGO = {
    "integracoes": ("id", "nome", "ator"),
    "logins": ("id", "nome"),
    "rnf": ("id", "categoria", "descricao", "metrica"),
    "stacks": ("id", "nome", "camadas"),
    "tipos-de-campo": ("id", "nome", "diagrama", "pessoal"),
}
_SUBITENS_CATALOGO = {"rnf": ("categoria", "descricao", "metrica"), "ameacas": ("ameaca", "controle"),
                      "superficie": ("ponto", "exposicao", "autenticacao"), "perguntas": ("pergunta",)}


def problemas_catalogos(catalogos=None):
    """Confere se os catálogos estão bem formados (usado pelos testes ao editar os JSON)."""
    catalogos = catalogos or carregar_catalogos()
    problemas = []
    for nome, itens in catalogos.items():
        vistos = set()
        for n, item in enumerate(itens, 1):
            local = f"{nome}.json, item {n}"
            if not isinstance(item, dict):
                problemas.append(f"{local}: precisa ser um objeto")
                continue
            local = f"{nome}.json, '{item.get('id', n)}'"
            for campo in _OBRIGATORIOS_CATALOGO[nome]:
                if campo not in item or item[campo] in ("", None, []):
                    problemas.append(f"{local}: falta '{campo}'")
            ident = item.get("id")
            if not isinstance(ident, str) or not _SLUG.match(ident):
                problemas.append(f"{local}: id precisa ser kebab-case")
            elif ident in vistos:
                problemas.append(f"{local}: id repetido")
            vistos.add(ident)
            for campo, chaves in _SUBITENS_CATALOGO.items():
                for sub in item.get(campo, []):
                    if not isinstance(sub, dict) or any(not isinstance(sub.get(c), str) or not sub[c] for c in chaves):
                        problemas.append(f"{local}: cada item de '{campo}' precisa de {', '.join(chaves)}")
                    elif campo == "perguntas" and not isinstance(sub.get("bloqueia", False), bool):
                        problemas.append(f"{local}: 'bloqueia' precisa ser true ou false")
            for v in item.get("variaveis", []):
                if not isinstance(v, str) or not _VARIAVEL.match(v):
                    problemas.append(f"{local}: variável '{v}' precisa ser MAIÚSCULAS_COM_SUBLINHADO")
            for s in item.get("skills", []):
                if not isinstance(s, str) or not _SLUG.match(s):
                    problemas.append(f"{local}: skill '{s}' precisa ser kebab-case")
            if not _lista_de_textos(item.get("caminhos_sensiveis", [])):
                problemas.append(f"{local}: 'caminhos_sensiveis' precisa ser uma lista de textos")
            if nome == "stacks":
                problemas += _problemas_stack(local, item)
            if nome == "tipos-de-campo" and not isinstance(item.get("pessoal"), bool):
                problemas.append(f"{local}: 'pessoal' precisa ser true ou false")
    return problemas


def _problemas_stack(local, item):
    problemas = []
    camadas = item.get("camadas")
    if not _lista_de_textos(camadas) or not set(camadas) <= set(CAMADAS):
        problemas.append(f"{local}: 'camadas' precisa ser uma lista de {', '.join(CAMADAS)}")
    if any(not isinstance(e, str) or not e.startswith(".") for e in item.get("extensoes", [])):
        problemas.append(f"{local}: extensões começam com ponto (.ts)")
    comandos = item.get("comandos", {})
    if not isinstance(comandos, dict) or not set(comandos) <= {"formatar", "lint", "testar"}:
        problemas.append(f"{local}: 'comandos' aceita só formatar, lint e testar")
    else:
        for chave in ("formatar", "lint"):
            if comandos.get(chave) and "{arquivo}" not in comandos[chave]:
                problemas.append(f"{local}: o comando '{chave}' precisa de {{arquivo}}")
    for p in item.get("permissoes", []):
        if not isinstance(p, str) or not _PERMISSAO.match(p):
            problemas.append(f"{local}: permissão '{p}' fora do formato Ferramenta(padrão)")
    for padrao in item.get("comandos_permitidos", []):
        try:
            re.compile(padrao)
        except (re.error, TypeError):
            problemas.append(f"{local}: comando permitido '{padrao}' não é uma expressão regular válida")
    if not _lista_de_textos(item.get("pastas", [])):
        problemas.append(f"{local}: 'pastas' precisa ser uma lista de textos")
    return problemas


def opcoes():
    """Valores fixos das listas do formulário (os catálogos trazem o resto)."""
    tamanhos = config_freelancer().get("tamanhos")
    return {"camadas": list(CAMADAS), "prioridades": list(PRIORIDADES), "tipos_ator": list(TIPOS_ATOR),
            "cardinalidades": list(CARDINALIDADES),
            "tamanhos": tamanhos if isinstance(tamanhos, dict) and tamanhos else dict(TAMANHOS_PADRAO)}


# ---------------------------------------------------------------- normalização e estrutura

def _limpar(valor):
    if isinstance(valor, str):
        return valor.strip()
    if isinstance(valor, list):
        return [_limpar(v) for v in valor]
    if isinstance(valor, dict):
        return {k: _limpar(v) for k, v in valor.items()}
    return valor


def _completar(dados, base):
    for chave, padrao in base.items():
        if chave not in dados or (dados[chave] is None and padrao is not None):
            dados[chave] = copy.deepcopy(padrao)
        elif isinstance(padrao, dict) and isinstance(dados[chave], dict):
            _completar(dados[chave], padrao)


def normalizar(dados):
    """Completa as chaves que faltam, tira espaços das pontas e padroniza IDs, prioridades e tamanhos."""
    if not isinstance(dados, dict):
        return dados
    dados = _limpar(copy.deepcopy(dados))
    _completar(dados, vazio())
    for caminho, lista in LISTAS.items():
        for _n, item in _itens(dados, caminho):
            if lista.prefixo and "id" in item:
                if item["id"] in ("", None):
                    del item["id"]
                elif isinstance(item["id"], str):
                    item["id"] = item["id"].upper()
            for campo in lista.listas:
                if item.get(campo) is None and campo in item:
                    item[campo] = []
                elif _lista_de_textos(item.get(campo)) and campo != "dispositivos":
                    item[campo] = [v.upper() for v in item[campo] if v]
    for _n, f in _itens(dados, "funcionalidades"):
        if isinstance(f.get("prioridade"), str) and f["prioridade"]:
            f["prioridade"] = _PRIORIDADE.get(f["prioridade"].casefold().replace("’", "'"), f["prioridade"])
        if isinstance(f.get("tamanho"), str):
            f["tamanho"] = f["tamanho"].upper()
    return dados


def _checar_tipos(dados, base, prefixo, erros):
    for chave, padrao in base.items():
        caminho, valor = prefixo + chave, dados.get(chave)
        if isinstance(padrao, dict):
            if not isinstance(valor, dict):
                erros.append(f"'{caminho}' precisa ser um objeto")
            else:
                _checar_tipos(valor, padrao, caminho + ".", erros)
        elif isinstance(padrao, list) and not isinstance(valor, list):
            erros.append(f"'{caminho}' precisa ser uma lista")
        elif isinstance(padrao, str) and not isinstance(valor, str):
            erros.append(f"'{caminho}' precisa ser texto")


def estrutura(dados):
    """Erros que impedem gravar o formulário: tipos errados e IDs inválidos ou repetidos."""
    if not isinstance(dados, dict):
        return ["o formulário precisa ser um objeto JSON"]
    erros = []
    versao = dados.get("versao")
    if not isinstance(versao, int) or isinstance(versao, bool) or versao < 1:
        erros.append("'versao' precisa ser um número inteiro")
    elif versao > VERSAO_FORMULARIO:
        erros.append(f"formulário na versão {versao}; este Prumo lê até a versão {VERSAO_FORMULARIO} (atualize o Prumo)")
    _checar_tipos(dados, {k: v for k, v in vazio().items() if k != "versao"}, "", erros)
    if erros:
        return erros
    for caminho in LISTAS_TEXTO:
        if not _lista_de_textos(_no(dados, caminho)):
            erros.append(f"'{caminho}' precisa ser uma lista de textos")
    if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in dados["ultimo_id"].values()):
        erros.append("'ultimo_id' precisa ligar cada prefixo a um número inteiro")
    if any(not isinstance(v, str) for v in dados["tecnico"]["stack"].values()):
        erros.append("'tecnico.stack' precisa ligar cada camada a um texto (id do catálogo ou nome livre)")
    for caminho, lista in LISTAS.items():
        vistos = set()
        for n, item in enumerate(_no(dados, caminho), 1):
            if not isinstance(item, dict):
                erros.append(f"'{caminho}', item {n}: precisa ser um objeto")
                continue
            for campo in lista.listas:
                if campo in item and not _lista_de_textos(item[campo]):
                    erros.append(f"{_rotulo(lista, item, n)}: '{campo}' precisa ser uma lista de textos")
            if lista.prefixo and "id" in item:
                ident = item["id"]
                if not isinstance(ident, str) or not re.fullmatch(_padrao_id(lista.prefixo), ident):
                    modelo = _formatar_id(lista.prefixo, 1)
                    erros.append(f"{lista.rotulo} {n}: ID '{ident}' inválido (formato {modelo})")
                elif ident in vistos:
                    erros.append(f"{lista.rotulo} {ident}: ID repetido")
                vistos.add(ident)
            if caminho == "entidades":
                for sub in SUBLISTAS:
                    valor = item.get(sub, [])
                    if not isinstance(valor, list) or any(not isinstance(v, dict) for v in valor):
                        erros.append(f"{_rotulo(lista, item, n)}: '{sub}' precisa ser uma lista de objetos")
    return erros


# ---------------------------------------------------------------- IDs

def ids_dos_documentos(projeto):
    """IDs já usados nos documentos do projeto. Os exemplos dos modelos ('[PREENCHER...') não contam."""
    analise = rastreio.analisar_projeto(projeto)
    usados = {i for i, item in analise.itens.items() if not item.titulo.startswith(MARCADOR_LACUNA)}
    return usados | set(analise.indefinidos())


def atribuir_ids(dados, ocupados=(), anteriores=None):
    """Dá a cada item sem ID o próximo número depois do maior já usado (formulário, documentos e `ultimo_id`).

    `anteriores` é o `ultimo_id` do arquivo já gravado (caso quem envia o formulário não o tenha preservado).
    Itens sem o campo obrigatório (linha recém-criada e ainda vazia) ficam sem ID até serem preenchidos.
    Devolve os IDs criados.
    """
    novos, ultimo = [], dados["ultimo_id"]
    for caminho, lista in LISTAS.items():
        if not lista.prefixo:
            continue
        itens = _no(dados, caminho)
        usados = [_numero(i) for i in ocupados if i.startswith(lista.prefixo + "-")]
        usados += [_numero(i["id"]) for _n, i in _itens(dados, caminho) if i.get("id")]
        usados += [ultimo.get(lista.prefixo, 0), (anteriores or {}).get(lista.prefixo, 0)]
        proximo = max(usados) + 1
        for pos, item in enumerate(itens):
            if isinstance(item, dict) and not item.get("id") and _preenchido(item.get(lista.obrigatorio)):
                ident = _formatar_id(lista.prefixo, proximo)
                itens[pos] = {"id": ident, **item}
                novos.append(ident)
                proximo += 1
        if proximo > 1:
            ultimo[lista.prefixo] = proximo - 1
    return novos


# ---------------------------------------------------------------- validação

def validar(dados, catalogos=None, ids_documentos=(), documentos=None):
    """Lista de (gravidade, mensagem).

    Erro: estrutura, campo obrigatório vazio, referência solta, valor fora do catálogo, nome repetido.
    Aviso: campo desconhecido, referência a ID que só existe nos documentos, combinações estranhas.
    """
    dados = normalizar(dados)
    erros_estrutura = estrutura(dados)
    if erros_estrutura:
        return [("erro", m) for m in erros_estrutura]
    catalogos = catalogos or carregar_catalogos()
    tamanhos = opcoes()["tamanhos"]
    problemas = []

    def erro(msg):
        problemas.append(("erro", msg))

    def aviso(msg):
        problemas.append(("aviso", msg))

    _campos_desconhecidos(dados, vazio(), "", aviso)
    for caminho, lista in LISTAS.items():
        for n, item in _itens(dados, caminho):
            if not _preenchido(item.get(lista.obrigatorio)):
                erro(f"{_rotulo(lista, item, n)}: falta '{lista.obrigatorio}'")
            for campo in sorted(set(item) - lista.campos):
                aviso(f"{_rotulo(lista, item, n)}: campo desconhecido '{campo}'")

    atores = _nomes_unicos(dados, "atores", erro)
    entidades = _nomes_unicos(dados, "entidades", erro)
    termos = set()
    for _n, t in _itens(dados, "glossario"):
        if _chave(t.get("termo")) in termos:
            aviso(f"Termo '{t['termo']}' aparece duas vezes no glossário")
        termos.add(_chave(t.get("termo")))
    ids = {lista.prefixo: {i["id"] for _n, i in _itens(dados, c) if i.get("id")}
           for c, lista in LISTAS.items() if lista.prefixo}

    def ref_ator(local, nome):
        if _preenchido(nome) and _chave(nome) not in atores:
            erro(f"{local}: ator '{nome}' não está na lista de usuários (atores)")

    def ref_ids(local, valores, prefixo):
        for ident in valores or []:
            if ident in ids[prefixo]:
                continue
            if not re.fullmatch(_padrao_id(prefixo), ident):
                erro(f"{local}: '{ident}' não é um ID {prefixo}")
            elif ident in ids_documentos:
                aviso(f"{local}: {ident} existe só nos documentos; o gerador não vai citá-lo")
            else:
                erro(f"{local}: {ident} não existe")

    lista = LISTAS["atores"]
    for n, a in _itens(dados, "atores"):
        if a.get("tipo") and a["tipo"] not in TIPOS_ATOR:
            erro(f"{_rotulo(lista, a, n)}: tipo '{a['tipo']}' (use {' ou '.join(TIPOS_ATOR)})")
    lista = LISTAS["funcionalidades"]
    for n, f in _itens(dados, "funcionalidades"):
        local = _rotulo(lista, f, n)
        ref_ator(local, f.get("ator"))
        ref_ids(local, f.get("regras"), "RN")
        if f.get("prioridade") and f["prioridade"] not in PRIORIDADES:
            erro(f"{local}: prioridade '{f['prioridade']}' (use {', '.join(PRIORIDADES)})")
        if f.get("tamanho") and f["tamanho"] not in tamanhos:
            erro(f"{local}: tamanho '{f['tamanho']}' (use {', '.join(tamanhos)})")
    lista = LISTAS["casos_de_uso"]
    for n, uc in _itens(dados, "casos_de_uso"):
        local = _rotulo(lista, uc, n)
        ref_ator(local, uc.get("ator"))
        ref_ids(local, uc.get("requisitos"), "RF")
        ref_ids(local, uc.get("regras"), "RN")
        ref_ids(local, uc.get("telas"), "TL")
    lista = LISTAS["interface.telas"]
    for n, tl in _itens(dados, "interface.telas"):
        local = _rotulo(lista, tl, n)
        ref_ator(local, tl.get("ator"))
        ref_ids(local, tl.get("atende"), "RF")
        ref_ids(local, tl.get("vai_para"), "TL")
    if documentos is not None and dados["interface"]["telas"] and "docs/05-interface.md" not in documentos:
        aviso("Há telas no formulário, mas o projeto não tem docs/05-interface.md (prumo doc 05-interface)")
    for n, p in _itens(dados, "perguntas"):
        if not isinstance(p.get("bloqueia", False), bool):
            erro(f"{_rotulo(LISTAS['perguntas'], p, n)}: 'bloqueia' precisa ser true ou false")
    _validar_entidades(dados, catalogos, entidades, erro, aviso)
    _validar_tecnico(dados, catalogos, atores, erro, aviso)
    _validar_comercial(dados, erro, aviso)
    email = dados["contato"]["email"]
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        aviso(f"Contato: e-mail '{email}' parece inválido")
    return problemas


def _campos_desconhecidos(dados, base, prefixo, aviso):
    for chave in dados:
        if chave not in base:
            aviso(f"Campo desconhecido '{prefixo}{chave}' (o gerador vai ignorá-lo)")
        elif isinstance(base[chave], dict) and base[chave] and isinstance(dados[chave], dict):
            _campos_desconhecidos(dados[chave], base[chave], f"{prefixo}{chave}.", aviso)


def _nomes_unicos(dados, caminho, erro):
    lista, nomes = LISTAS[caminho], set()
    for _n, item in _itens(dados, caminho):
        chave = _chave(item.get("nome"))
        if chave and chave in nomes:
            erro(f"{lista.rotulo} '{item['nome']}' aparece duas vezes (as referências são pelo nome)")
        nomes.add(chave)
    nomes.discard("")
    return nomes


def _validar_entidades(dados, catalogos, entidades, erro, aviso):
    tipos = indice(catalogos, "tipos-de-campo")
    for n, ent in _itens(dados, "entidades"):
        local = _rotulo(LISTAS["entidades"], ent, n)
        for sub, lista in SUBLISTAS.items():
            for m, item in enumerate(ent.get(sub, []), 1):
                if not _preenchido(item.get(lista.obrigatorio)):
                    erro(f"{local}, {lista.rotulo.lower()} {m}: falta '{lista.obrigatorio}'")
                for campo in sorted(set(item) - lista.campos):
                    aviso(f"{local}, {lista.rotulo.lower()} {m}: campo desconhecido '{campo}'")
        vistos = set()
        for _m, campo in enumerate(ent.get("campos", []), 1):
            nome = _chave(campo.get("nome"))
            if nome and nome in vistos:
                erro(f"{local}: campo '{campo['nome']}' repetido")
            vistos.add(nome)
            if campo.get("tipo") and campo["tipo"] not in tipos:
                erro(f"{local}, campo '{campo.get('nome', '')}': tipo '{campo['tipo']}' não está no catálogo de tipos")
            for marca in ("obrigatorio", "unico", "pessoal"):
                if not isinstance(campo.get(marca, False), bool):
                    erro(f"{local}, campo '{campo.get('nome', '')}': '{marca}' precisa ser true ou false")
        for rel in ent.get("relacoes", []):
            com = rel.get("com")
            if _preenchido(com) and _chave(com) not in entidades:
                erro(f"{local}: relação com '{com}', que não está na lista de entidades")
            if rel.get("cardinalidade") and rel["cardinalidade"] not in CARDINALIDADES:
                erro(f"{local}: cardinalidade '{rel['cardinalidade']}' (use {', '.join(CARDINALIDADES)})")


def _validar_tecnico(dados, catalogos, atores, erro, aviso):
    tecnico = dados["tecnico"]
    stacks = indice(catalogos, "stacks")
    for camada, valor in tecnico["stack"].items():
        if camada not in CAMADAS:
            aviso(f"Técnico: camada desconhecida '{camada}' (use {', '.join(CAMADAS)})")
        elif valor in stacks and camada not in stacks[valor]["camadas"]:
            aviso(f"Técnico: '{valor}' não é da camada {camada} (é de {', '.join(stacks[valor]['camadas'])})")
    if tecnico["login"] and tecnico["login"] not in indice(catalogos, "logins"):
        erro(f"Técnico: login '{tecnico['login']}' não está no catálogo (templates/catalogos/logins.json)")
    for campo, catalogo in (("integracoes", "integracoes"), ("rnf", "rnf")):
        conhecidos = indice(catalogos, catalogo)
        for ident in tecnico[campo]:
            if ident not in conhecidos:
                erro(f"Técnico: '{ident}' não está no catálogo (templates/catalogos/{catalogo}.json)")
    for perfil in tecnico["perfis_acesso"]:
        if _chave(perfil) not in atores:
            aviso(f"Técnico: perfil de acesso '{perfil}' não corresponde a nenhum ator")


def _validar_comercial(dados, erro, aviso):
    comercial = dados["comercial"]
    for campo in ("validade_dias", "garantia_dias"):
        valor = comercial[campo]
        if valor not in (None, "") and (not isinstance(valor, int) or isinstance(valor, bool) or valor < 0):
            erro(f"Comercial: '{campo}' precisa ser um número inteiro de dias")
    percentuais = []
    for n, marco in _itens(dados, "comercial.marcos"):
        valor = marco.get("percentual")
        if valor in (None, ""):
            continue
        if not isinstance(valor, (int, float)) or isinstance(valor, bool) or not 0 <= valor <= 100:
            erro(f"{_rotulo(LISTAS['comercial.marcos'], marco, n)}: percentual precisa ser um número de 0 a 100")
        else:
            percentuais.append(valor)
    if percentuais and len(percentuais) == len(comercial["marcos"]) and abs(sum(percentuais) - 100) > 0.01:
        aviso(f"Comercial: os percentuais dos marcos somam {sum(percentuais):g}%, não 100%")


# ---------------------------------------------------------------- leitura, gravação e resumo

def carregar(projeto):
    """(formulário normalizado, existe?). Sem arquivo, devolve o formulário vazio."""
    dados = ler_json(projeto.raiz / ARQUIVO, None)
    if dados is None:
        return vazio(), False
    return normalizar(dados), True


def salvar(projeto, dados):
    """Normaliza, atribui IDs e grava especificacao.prumo.json.

    Só a estrutura impede a gravação (a interface grava a cada mudança, com o formulário ainda incompleto);
    referências soltas e valores fora do catálogo voltam em 'problemas'.
    """
    dados = normalizar(dados)
    erros = estrutura(dados)
    if erros:
        raise ErroPrumo("Formulário não gravado:\n  " + "\n  ".join(erros))
    ocupados = ids_dos_documentos(projeto)
    anterior = ler_json(projeto.raiz / ARQUIVO, None)
    anteriores = anterior.get("ultimo_id") if isinstance(anterior, dict) else None
    novos = atribuir_ids(dados, ocupados, anteriores if isinstance(anteriores, dict) else None)
    gravar_json(projeto.raiz / ARQUIVO, dados)
    problemas = validar(dados, ids_documentos=ocupados, documentos=projeto.config.get("documentos"))
    return {"arquivo": ARQUIVO, "ids_criados": novos, "problemas": problemas}


def preenchimento(dados, documentos=None):
    """Quantos campos de cada passo estão preenchidos (o passo Telas só existe com docs/05-interface.md)."""
    saida = []
    for ident, titulo, campos in PASSOS:
        if ident == "telas" and documentos is not None and "docs/05-interface.md" not in documentos:
            continue
        vazios = [c for c in campos if not _preenchido(_no(dados, c))]
        saida.append({"id": ident, "titulo": titulo, "preenchidos": len(campos) - len(vazios), "total": len(campos),
                      "vazios": vazios})
    return saida


def contagens(dados):
    return {caminho: len(_itens(dados, caminho)) for caminho in LISTAS}


def resumo(projeto):
    """Tudo o que a interface precisa para montar o formulário: dados, catálogos, opções, passos e problemas."""
    dados, existe = carregar(projeto)
    documentos = projeto.config.get("documentos")
    catalogos = carregar_catalogos()
    problemas = validar(dados, catalogos, ids_dos_documentos(projeto), documentos)
    valido = isinstance(dados, dict) and not estrutura(dados)
    return {"arquivo": ARQUIVO, "existe": existe, "formulario": dados,
            "passos": preenchimento(dados, documentos) if valido else [],
            "itens": contagens(dados) if valido else {},
            "problemas": problemas, "catalogos": catalogos, "opcoes": opcoes()}
