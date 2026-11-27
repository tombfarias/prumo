"""Entrevista guiada: perguntas padronizadas, uma por vez, que completam o formulário (sem IA, sem tokens).

As perguntas ficam em templates/catalogos/entrevista.json. Cada resposta é aplicada ao formulário
(especificacao.prumo.json) e gravada em `entrevista.respostas`; pergunta já respondida, fora do perfil ou cujo campo
já está preenchido não é feita. Respostas sim/não e escolhas acrescentam requisitos, integrações e RNFs padrão.
"""

import copy
import json
import re

from . import formulario
from .util import ErroPrumo, ler_json

ARQUIVO = formulario.PASTA_CATALOGOS / "entrevista.json"
TIPOS = ("texto", "area", "lista", "numero", "sim-nao", "escolha", "multipla")
PULADA = "(pulada)"
_SIM = {"sim", "s", "yes", "y", "true", "1"}
_NAO = {"nao", "não", "n", "no", "false", "0"}


def carregar_perguntas(idioma=None):
    """Perguntas da entrevista, com os textos no idioma do projeto."""
    dados = ler_json(ARQUIVO, None)
    if not isinstance(dados, dict) or not isinstance(dados.get("itens"), list):
        raise ErroPrumo("Catálogo ausente ou inválido: templates/catalogos/entrevista.json")
    return formulario.no_idioma(dados["itens"], idioma)


# ---------------------------------------------------------------- condições e pendências

def _texto_de(valor):
    return "" if valor is None else str(valor)


def _condicao(cond, dados, perfil):
    if cond.startswith("perfil:"):
        return perfil in cond[len("perfil:"):].split("|")
    m = re.fullmatch(r"(campo:)?([\w.-]+)(!?=)(.*)", cond)
    if not m:
        return False
    if m.group(1):
        atual = formulario._no(dados, m.group(2))
        atual = "" if isinstance(atual, (list, dict)) and not atual else _texto_de(atual)
    else:
        atual = _texto_de(dados["entrevista"]["respostas"].get(m.group(2)))
    return (atual == m.group(4)) == (m.group(3) == "=")


def pendentes(dados, perfil="", perguntas=None):
    """Perguntas que ainda cabem, na ordem do catálogo."""
    respostas = dados["entrevista"]["respostas"]
    saida = []
    for q in perguntas or carregar_perguntas():
        if q["id"] in respostas or not all(_condicao(c, dados, perfil) for c in q.get("se", [])):
            continue
        if q.get("campo") and not q.get("acumula") and formulario._preenchido(formulario._no(dados, q["campo"])):
            continue
        saida.append(q)
    return saida


def _aplicaveis(dados, perfil, perguntas):
    """Total de perguntas que valem para este projeto (feitas + pendentes), para o indicador de progresso."""
    respostas = dados["entrevista"]["respostas"]
    return len([q for q in perguntas if q["id"] in respostas]) + len(pendentes(dados, perfil, perguntas))


# ---------------------------------------------------------------- aplicação

def _chave_item(lista, item):
    campo = formulario.LISTAS[lista].obrigatorio if lista in formulario.LISTAS else None
    return formulario._chave(item.get(campo)) if campo else None


def _acrescentar(dados, lista, item, feitos):
    alvo = formulario._no(dados, lista)
    chave = _chave_item(lista, item)
    if chave and any(isinstance(i, dict) and _chave_item(lista, i) == chave for i in alvo):
        return
    alvo.append(copy.deepcopy(item))
    feitos.append(f"{formulario.LISTAS[lista].rotulo}: {item[formulario.LISTAS[lista].obrigatorio]}")


def _marcar(dados, lista, valor, feitos):
    alvo = formulario._no(dados, lista)
    if valor not in alvo:
        alvo.append(valor)
        feitos.append(f"{lista}: {valor}")


def _definir(dados, caminho, valor, feitos):
    partes = caminho.split(".")
    alvo = formulario._no(dados, ".".join(partes[:-1])) if len(partes) > 1 else dados
    if alvo.get(partes[-1]) != valor:
        alvo[partes[-1]] = valor
        feitos.append(f"{caminho}: {valor}")


def _acoes(dados, acoes, feitos):
    for a in acoes or []:
        if "acrescentar" in a:
            _acrescentar(dados, a["acrescentar"], a["item"], feitos)
        elif "marcar" in a:
            _marcar(dados, a["marcar"], a["valor"], feitos)
        elif "definir" in a:
            _definir(dados, a["definir"], a["valor"], feitos)


def _linhas(valor):
    if isinstance(valor, list):
        return [str(v).strip() for v in valor if str(v).strip()]
    return [l.strip(" -•\t") for l in str(valor or "").splitlines() if l.strip(" -•\t")]


def interpretar(q, valor):
    """Resposta normalizada para o tipo da pergunta, ou ErroPrumo com o formato esperado."""
    tipo = q["tipo"]
    if tipo in ("texto", "area"):
        return str(valor or "").strip()
    if tipo == "lista":
        return _linhas(valor)
    if tipo == "numero":
        texto = str(valor or "").strip()
        if not texto:
            return None
        if not re.fullmatch(r"\d+", texto):
            raise ErroPrumo(f"'{q['id']}': responda com um número inteiro (ex.: 15).")
        return int(texto)
    if tipo == "sim-nao":
        texto = str(valor).strip().casefold() if not isinstance(valor, bool) else ("sim" if valor else "nao")
        if texto in _SIM:
            return "sim"
        if texto in _NAO:
            return "nao"
        raise ErroPrumo(f"'{q['id']}': responda sim ou não.")
    opcoes = [o["valor"] for o in q["opcoes"]]
    escolhidos = _linhas(valor) if tipo == "multipla" else [str(valor).strip()]
    saida = []
    for e in escolhidos:
        if e.isdigit() and 1 <= int(e) <= len(opcoes):
            e = opcoes[int(e) - 1]
        if e not in opcoes:
            raise ErroPrumo(f"'{q['id']}': escolha entre {', '.join(opcoes)} (ou o número da opção).")
        saida.append(e)
    return saida if tipo == "multipla" else saida[0]


def aplicar(dados, q, valor):
    """Aplica a resposta (já interpretada) ao formulário. Devolve a lista do que mudou."""
    feitos = []
    tipo, campo = q["tipo"], q.get("campo")
    if tipo in ("texto", "area", "numero") and campo and valor not in ("", None):
        _definir(dados, campo, valor, feitos)
    elif tipo == "lista" and valor:
        if campo in formulario.LISTAS_TEXTO:
            for v in valor:
                _marcar(dados, campo, v, feitos)
        elif campo:
            for v in valor:
                item = {k: (x.replace("{valor}", v) if isinstance(x, str) else x) for k, x in q["modelo"].items()}
                _acrescentar(dados, campo, item, feitos)
        _acoes(dados, q.get("acoes"), feitos)
    elif tipo == "sim-nao":
        _acoes(dados, q.get("se_sim" if valor == "sim" else "se_nao"), feitos)
    elif tipo in ("escolha", "multipla"):
        for v in valor if tipo == "multipla" else [valor]:
            if campo:
                (_marcar if tipo == "multipla" else _definir)(dados, campo, v, feitos)
            _acoes(dados, next(o for o in q["opcoes"] if o["valor"] == v).get("acoes"), feitos)
    dados["entrevista"]["respostas"][q["id"]] = valor
    return feitos


# ---------------------------------------------------------------- uso pelo projeto

def _perfil(projeto):
    return projeto.config.get("perfil", "")


def proxima(projeto, dados=None):
    """{'pergunta', 'feitas', 'total'}; 'pergunta' é None quando a entrevista acabou."""
    dados = dados or formulario.carregar(projeto)[0]
    perguntas = carregar_perguntas(projeto.idioma)
    pend = pendentes(dados, _perfil(projeto), perguntas)
    feitas = len(dados["entrevista"]["respostas"])
    return {"pergunta": pend[0] if pend else None, "feitas": feitas,
            "total": _aplicaveis(dados, _perfil(projeto), perguntas)}


def _pergunta(ident, idioma=None):
    q = next((q for q in carregar_perguntas(idioma) if q["id"] == ident), None)
    if not q:
        raise ErroPrumo(f"Pergunta '{ident}' não existe (veja templates/catalogos/entrevista.json).")
    return q


def responder(projeto, ident, valor):
    """Aplica a resposta, grava o formulário (IDs novos atribuídos) e devolve o que mudou e a próxima pergunta."""
    dados = formulario.carregar(projeto)[0]
    q = _pergunta(ident, projeto.idioma)
    feitos = aplicar(dados, q, interpretar(q, valor))
    r = formulario.salvar(projeto, dados)
    return {"aplicado": feitos, "ids_criados": r["ids_criados"], **proxima(projeto)}


def pular(projeto, ident):
    dados = formulario.carregar(projeto)[0]
    _pergunta(ident)
    dados["entrevista"]["respostas"][ident] = PULADA
    formulario.salvar(projeto, dados)
    return {"aplicado": [], "ids_criados": [], **proxima(projeto)}


def reiniciar(projeto):
    """Esquece as respostas (o que já foi para o formulário fica); perguntas com campo preenchido continuam puladas."""
    dados = formulario.carregar(projeto)[0]
    dados["entrevista"]["respostas"] = {}
    formulario.salvar(projeto, dados)
    return proxima(projeto)


def valor_de_texto(texto):
    """Resposta vinda da linha de comando: JSON se for uma lista, senão o próprio texto."""
    texto = (texto or "").strip()
    if texto.startswith("["):
        try:
            return json.loads(texto)
        except ValueError:
            pass
    return texto


# ---------------------------------------------------------------- conferência do catálogo (testes)

def _existe(dados, caminho):
    for parte in caminho.split("."):
        if not isinstance(dados, dict) or parte not in dados:
            return False
        dados = dados[parte]
    return True


def problemas_entrevista(perguntas=None, catalogos=None):
    perguntas = perguntas if perguntas is not None else carregar_perguntas()
    catalogos = catalogos or formulario.carregar_catalogos()
    vazio = formulario.vazio()
    valores = {"tecnico.integracoes": formulario.indice(catalogos, "integracoes"),
               "tecnico.rnf": formulario.indice(catalogos, "rnf"), "tecnico.login": formulario.indice(catalogos, "logins")}
    ids, problemas = set(), []

    def acoes(local, lista):
        for a in lista or []:
            if "acrescentar" in a:
                alvo = a["acrescentar"]
                if alvo not in formulario.LISTAS:
                    problemas.append(f"{local}: lista '{alvo}' não existe")
                elif set(a.get("item", {})) - formulario.LISTAS[alvo].campos or \
                        not a.get("item", {}).get(formulario.LISTAS[alvo].obrigatorio):
                    problemas.append(f"{local}: item de '{alvo}' com campo desconhecido ou sem o principal")
            elif "marcar" in a or "definir" in a:
                alvo = a.get("marcar") or a.get("definir")
                if not _existe(vazio, alvo):
                    problemas.append(f"{local}: campo '{alvo}' não existe")
                if alvo in valores and a.get("valor") not in valores[alvo]:
                    problemas.append(f"{local}: '{a.get('valor')}' não está no catálogo de {alvo}")
            else:
                problemas.append(f"{local}: ação desconhecida {a}")

    for n, q in enumerate(perguntas, 1):
        local = f"entrevista.json, '{q.get('id', n)}'"
        if not q.get("id") or q["id"] in ids:
            problemas.append(f"{local}: id ausente ou repetido")
        ids.add(q.get("id"))
        if q.get("tipo") not in TIPOS:
            problemas.append(f"{local}: tipo '{q.get('tipo')}' (use {', '.join(TIPOS)})")
        if not q.get("pergunta") or q.get("passo") not in {p[0] for p in formulario.PASSOS}:
            problemas.append(f"{local}: falta 'pergunta' ou 'passo' inválido")
        campo = q.get("campo")
        if campo and not _existe(vazio, campo):
            problemas.append(f"{local}: campo '{campo}' não existe no formulário")
        if q.get("tipo") == "lista" and campo in formulario.LISTAS and "{valor}" not in json.dumps(q.get("modelo", {})):
            problemas.append(f"{local}: lista de objetos precisa de 'modelo' com {{valor}}")
        if q.get("tipo") in ("escolha", "multipla"):
            if not q.get("opcoes"):
                problemas.append(f"{local}: falta 'opcoes'")
            for o in q.get("opcoes", []):
                acoes(f"{local}, opção '{o.get('valor')}'", o.get("acoes"))
                if campo in valores and o.get("valor") not in valores[campo]:
                    problemas.append(f"{local}: opção '{o.get('valor')}' não está no catálogo")
        for chave in ("se_sim", "se_nao", "acoes"):
            acoes(local, q.get(chave))
    for q in perguntas:
        for c in q.get("se", []):
            m = re.fullmatch(r"([\w-]+)!?=.*", c)
            if m and not c.startswith("campo:") and m.group(1) not in ids:
                problemas.append(f"entrevista.json, '{q['id']}': condição cita '{m.group(1)}', que não existe")
    return problemas
