"""Idiomas do Prumo: português do Brasil (padrão) e inglês.

Dois ajustes independentes:
- idioma da interface (CLI e GUI): variável PRUMO_IDIOMA, depois `idioma_interface` em config/freelancer.json
  ("auto" segue o sistema);
- idioma do projeto (documentos e kit do Claude): campo `idioma` de projeto.prumo.json, escolhido em
  `prumo novo --idioma en`. Os modelos em inglês ficam em templates/en/, com o mesmo caminho dos originais.

O código continua escrito em português. A tradução troca trechos conhecidos (catálogo i18n/en.json, chave = texto
em português) no texto que vai para a tela; o que não está no catálogo, como nomes e caminhos, passa intacto.
Trechos entre PROTEGER_INICIO e PROTEGER_FIM (conteúdo dos documentos) nunca são traduzidos.
"""

import json
import locale
import os
import re
from pathlib import Path

PADRAO = "pt-BR"
IDIOMAS = ("pt-BR", "en")
NOMES = {"pt-BR": "Português (Brasil)", "en": "English"}
PROTEGER_INICIO, PROTEGER_FIM = "", ""
PASTA = Path(__file__).resolve().parent / "i18n"
_CACHE = {}


def normalizar(idioma, padrao=PADRAO):
    """'pt', 'pt_BR', 'PT-br' -> 'pt-BR'; 'en', 'en_US' -> 'en'; outro ou vazio -> padrao."""
    t = str(idioma or "").strip().replace("_", "-").lower()
    if t.startswith("pt"):
        return "pt-BR"
    if t.startswith("en"):
        return "en"
    return padrao


def validar(idioma):
    from .util import ErroPrumo
    t = str(idioma or "").strip()
    if normalizar(t, None) is None:
        raise ErroPrumo(f"Idioma '{t}' não suportado. Use: {', '.join(IDIOMAS)}")
    return normalizar(t)


def idioma_sistema():
    """Idioma do sistema operacional: pt-BR se for português, en se for outro idioma, pt-BR se indefinido."""
    candidatos = [os.environ.get(v, "") for v in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE")]
    if os.name == "nt":
        try:
            import ctypes
            candidatos.insert(0, locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), ""))
        except Exception:
            pass
    try:
        candidatos.append(locale.getlocale()[0] or "")
    except Exception:
        pass
    for c in candidatos:
        c = c.split(":")[0].split(".")[0]
        if re.match(r"[A-Za-z]{2,3}([_-]|$)", c) and c.upper() not in ("C", "POSIX"):
            return normalizar(c, "en")
    return PADRAO


def idioma_interface():
    """Idioma da CLI e da interface gráfica."""
    env = os.environ.get("PRUMO_IDIOMA", "").strip()
    if env:
        return normalizar(env)
    try:
        from .util import RAIZ_KIT
        dados = json.loads((RAIZ_KIT / "config" / "freelancer.json").read_text(encoding="utf-8-sig"))
        escolhido = str(dados.get("idioma_interface") or "").strip()
    except Exception:
        escolhido = ""
    if escolhido and escolhido.lower() != "auto":
        return normalizar(escolhido)
    return idioma_sistema()


def catalogo(idioma):
    """{texto em português: tradução}. Vazio para pt-BR."""
    idioma = normalizar(idioma)
    if idioma == PADRAO:
        return {}
    if idioma not in _CACHE:
        try:
            dados = json.loads((PASTA / f"{idioma}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            dados = {}
        _CACHE[idioma] = {k: v for k, v in (dados.get("textos") or {}).items() if v}
    return _CACHE[idioma]


_REGEX = {}


def _regex(idioma):
    if idioma not in _REGEX:
        cat = catalogo(idioma)
        chaves = sorted(cat, key=len, reverse=True)
        partes = []
        for k in chaves:
            p = re.escape(k)
            if re.match(r"\w", k):
                p = r"(?<![\w])" + p  # não começa no meio de uma palavra
            if re.search(r"\w$", k):
                p += r"(?![\w])"
            partes.append(p)
        _REGEX[idioma] = re.compile("|".join(partes)) if partes else None
    return _REGEX[idioma]


def traduzir(texto, idioma=None):
    """Troca os trechos do catálogo; trechos protegidos passam intactos (e os marcadores saem)."""
    if texto is None or not isinstance(texto, str):
        return texto
    idioma = normalizar(idioma or idioma_interface())
    rx = _regex(idioma) if idioma != PADRAO else None
    if rx is None:
        return texto.replace(PROTEGER_INICIO, "").replace(PROTEGER_FIM, "")
    cat = catalogo(idioma)
    saida, pos = [], 0
    for m in re.finditer(re.escape(PROTEGER_INICIO) + "(.*?)(?:" + re.escape(PROTEGER_FIM) + "|$)", texto, re.S):
        saida.append(rx.sub(lambda x: cat[x.group(0)], texto[pos:m.start()]))
        saida.append(m.group(1))
        pos = m.end()
    saida.append(rx.sub(lambda x: cat[x.group(0)], texto[pos:]))
    return "".join(saida)


def proteger(texto):
    return f"{PROTEGER_INICIO}{texto}{PROTEGER_FIM}"


def t(texto):
    """Atalho para textos da interface."""
    return traduzir(texto)


def traduzir_parser(parser, idioma=None):
    """Traduz descrições e ajudas do argparse (inclusive dos subcomandos)."""
    import argparse
    idioma = normalizar(idioma or idioma_interface())
    if idioma == PADRAO:
        return parser
    vistos = set()

    def visitar(p):
        if id(p) in vistos:
            return
        vistos.add(id(p))
        p.description = traduzir(p.description, idioma)
        for acao in p._actions:
            if acao.help and acao.help is not argparse.SUPPRESS:
                acao.help = traduzir(acao.help, idioma)
            if isinstance(acao, argparse._SubParsersAction):
                for escolha in acao._choices_actions:
                    escolha.help = traduzir(escolha.help, idioma)
                for sub in acao.choices.values():
                    visitar(sub)

    visitar(parser)
    return parser
