"""Confere o catálogo de traduções (prumo_cli/i18n/en.json) contra os textos do código e da interface.

    python tools/i18n.py            # lista os textos sem tradução (sai com 1 se houver)
    python tools/i18n.py --json     # o mesmo, como JSON {texto: ""} pronto para colar no catálogo

Textos considerados: constantes e trechos fixos de f-strings em prumo_cli/*.py e as strings e o HTML de
prumo_cli/gui/index.html que parecem frases em português, e a primeira linha da docstring dos hooks (aba do kit). Os prompts enviados ao Claude ficam de fora (o Claude lê
português; projetos em inglês recebem a regra de idioma no prompt). Trecho que não deve ser traduzido (nome próprio,
termo técnico) vai em "ignorar" no catálogo.
"""

import ast
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CATALOGO = RAIZ / "prumo_cli" / "i18n" / "en.json"
GUI = RAIZ / "prumo_cli" / "gui" / "index.html"
HOOKS = RAIZ / "templates" / "agentes" / "claude" / "hooks"
# módulos e nomes fora da interface: prompts do Claude, catálogos de detecção e o próprio i18n
IGNORAR_MODULOS = {"i18n.py", "__init__.py", "__main__.py"}
IGNORAR_NOMES = {"AVISO_NAO_INTERATIVO", "REGRAS_ESPECIFICACAO", "DICAS_VALIDACAO", "IDIOMA_EN", "montar_prompt",
                 "montar_prompt_etapas", "_aviso_final", "_corpo_skill", "RE_LOGIN", "RE_LIMITE",
                 "CELULAS_EN", "DICAS_EN", "ROTULOS_EN", "ROTULOS_DE_LINHA"}
PALAVRAS_PT = re.compile(r"\b(de|da|do|das|dos|para|com|sem|não|em|no|na|nos|nas|um|uma|que|ou|os|as|ao|à|é|já|por|se|e|desta|deste|esta|este|cada|mais|sobre|entre|pelo|pela|seu|sua|ainda|gera|lista|cria|mostra)\b", re.I)


def parece_texto(s):
    s = s.strip()
    if len(s) < 3 or not re.search(r"[A-Za-zÀ-ú]{2}", s):
        return False
    if re.fullmatch(r"[A-ZÀ-Ú][a-zà-ú]{2,}:?", s):
        return True  # rótulo de uma palavra ("Cliente", "Salvar")
    if s.startswith("[") and '", "' in s:
        return False  # literal de lista do JS
    if re.search(r"\\|\(\?|\$\{|=>|^[\w./*-]+$|^--|^[a-z_]+=|https?://", s):
        return False  # regex, código, caminhos, identificadores
    if re.search(r"[À-ú]", s) or PALAVRAS_PT.search(s):
        return True
    if len(re.findall(r"\b[a-zA-Z]{2,}\b", s)) >= 2 and not re.search(r"[(){}\[\]<>|$@#]|^\w+\s*:", s):
        return True  # frase sem acento nem palavra comum ("gera docs/rastreabilidade.md")
    return bool(re.match(r"[A-ZÀ-Ú][a-zà-ú]{2,}( [a-zà-ú]+)*:?$", s))  # rótulo curto ("Cliente", "Lacunas a preencher")


def _partes(texto):
    for linha in texto.split("\n"):
        linha = linha.strip()
        if parece_texto(linha):
            yield linha


def textos_python():
    achados = {}
    for arq in sorted((RAIZ / "prumo_cli").glob("*.py")):
        if arq.name in IGNORAR_MODULOS:
            continue
        arvore = ast.parse(arq.read_text(encoding="utf-8"))
        pular = set()
        for no in ast.walk(arvore):
            corpo = getattr(no, "body", None)
            if isinstance(corpo, list) and corpo and isinstance(corpo[0], ast.Expr) and isinstance(corpo[0].value, ast.Constant):
                pular.add(id(corpo[0].value))  # docstrings
            nome = getattr(no, "name", None) or (no.targets[0].id if isinstance(no, ast.Assign) and isinstance(no.targets[0], ast.Name) else None)
            if nome in IGNORAR_NOMES:
                pular |= {id(n) for n in ast.walk(no)}
            if isinstance(no, ast.Call) and getattr(no.func, "attr", getattr(no.func, "id", "")) in ("compile", "search", "match", "sub", "fullmatch", "findall", "finditer", "split"):
                pular |= {id(n) for n in ast.walk(no.args[0])} if no.args else set()  # padrões de regex
            if isinstance(no, ast.Subscript):
                pular |= {id(n) for n in ast.walk(no.slice)}  # chaves de dicionário (dados["campo"])
        for no in ast.walk(arvore):
            if isinstance(no, ast.JoinedStr):
                for v in no.values:
                    pular.add(id(v))
                    if isinstance(v, ast.Constant) and id(no) not in pular:
                        for p in _partes(v.value):
                            achados.setdefault(p, arq.name)
            elif isinstance(no, ast.Constant) and isinstance(no.value, str) and id(no) not in pular:
                for p in _partes(no.value):
                    achados.setdefault(p, arq.name)
    return achados


def textos_gui():
    t = GUI.read_text(encoding="utf-8")
    t = re.sub(r"<style>.*?</style>|<svg.*?</svg>|/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r"^\s*//.*$|(?<=[;,{)])\s*//[^\n\"'`]*$", "", t, flags=re.M)
    achados = {}
    html = re.sub(r"<script>.*?</script>", "", t, flags=re.S)
    script = "".join(re.findall(r"<script>(.*?)</script>", t, flags=re.S))
    for m in re.finditer(r">([^<>]+)<", html):
        for parte in _partes(m.group(1)):
            achados.setdefault(parte, "index.html")
    t = script
    for m in re.finditer(r">([^<>]+)<", script):  # texto dos trechos de HTML dentro dos templates do JS
        for parte in re.split(r"\$\{(?:[^{}]|\{[^{}]*\})*\}|\$\{.*|\n", m.group(1)):
            parte = parte.strip()
            if parece_texto(parte) and not re.search(r"[{};=`]|\(\)|\.\w+\(|\$\{|\|\||&&", re.sub(r"\{\w+\}", "", parte)):
                achados.setdefault(parte, "index.html")
    for m in re.finditer(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`', t):
        s = next(g for g in m.groups() if g is not None)
        for parte in re.split(r"\$\{(?:[^{}]|\{[^{}]*\})*\}|<[^>]*>|\n", s):
            parte = parte.strip()
            if parece_texto(parte) and not re.search(r"[{};=]|\(\)|\.\w+\(", re.sub(r"\{\w+\}", "", parte)):
                achados.setdefault(parte, "index.html")
    return achados


def textos_hooks():
    """Primeira linha da docstring de cada hook: a interface a mostra na aba do kit."""
    achados = {}
    for arq in sorted(HOOKS.glob("*.py")):
        doc = ast.get_docstring(ast.parse(arq.read_text(encoding="utf-8"))) or ""
        if doc:
            achados.setdefault(doc.splitlines()[0].strip(), arq.name)
    return achados


def catalogo():
    return json.loads(CATALOGO.read_text(encoding="utf-8"))


def cobre(texto, cat):
    """O trecho está no catálogo (traduzido ou ignorado) ou é coberto por uma chave maior que o contém."""
    textos, ignorar = cat.get("textos", {}), set(cat.get("ignorar", []))
    return texto in textos or texto in ignorar


def faltando():
    cat = catalogo()
    todos = {**textos_python(), **textos_gui(), **textos_hooks()}
    return {t: origem for t, origem in sorted(todos.items()) if not cobre(t, cat)}


def main(argv):
    falta = faltando()
    if "--json" in argv:
        print(json.dumps({t: "" for t in falta}, ensure_ascii=False, indent=2))
    else:
        for t, origem in falta.items():
            print(f"{origem}: {t}")
        print(f"{len(falta)} texto(s) sem tradução", file=sys.stderr)
    return 1 if falta else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
