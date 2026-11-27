"""Avisos de estilo para os documentos gerados: enchimento, termos vagos, frases e parágrafos longos, repetição.

As regras seguem docs/guia-de-escrita.md. São avisos (sugestões), nunca erros.
"""

import re

MAX_PALAVRAS_FRASE = 40
MAX_PALAVRAS_PARAGRAFO = 70
MIN_CARACTERES_REPETIDA = 40
MIN_PALAVRAS_REPETIDA = 8  # linhas de metadados curtas ("**Épico:** EP-01 · ...") se repetem por natureza

# expressão -> sugestão
ENCHIMENTO = [
    (r"\b(é|e) importante (ressaltar|destacar|notar|mencionar|salientar|lembrar)( que)?", "corte; diga o fato"),
    (r"\bvale (a pena )?(ressaltar|destacar|mencionar|lembrar|notar)( que)?", "corte; diga o fato"),
    (r"\bcabe (ressaltar|destacar|mencionar|lembrar)( que)?", "corte; diga o fato"),
    (r"\bcomo (já )?(foi )?(mencionado|dito|citado|descrito) (anteriormente|acima)", "cite o ID ou a seção"),
    (r"\b(a fim de|com o (intuito|objetivo|propósito) de|com a finalidade de|de forma a|de modo a)\b", "use \"para\""),
    (r"\bno que (diz respeito|se refere|tange) (a|à|ao|aos|às)\b", "use \"sobre\" ou \"em\""),
    (r"\b(basicamente|essencialmente|simplesmente)\b", "corte"),
    (r"\b(nesse|neste|desse|deste) (sentido|contexto)\b", "corte"),
    (r"\bpor fim, mas não menos importante\b", "corte"),
]
# Termos que não dá para verificar; o briefing guarda as palavras do cliente e fica de fora.
VAGOS = [
    (r"\b(intuitiv[oa]s?|amigáve(l|is)|user[- ]friendly|modern[oa]s?|robust[oa]s?|eficientes?|ágil|ágeis)\b",
     "termo vago: troque por um critério verificável ou registre uma pergunta P-xx"),
    (r"\bde (forma|maneira) (rápida|fácil|simples|eficiente|adequada|intuitiva)\b",
     "termo vago: diga quanto (tempo, cliques, passos)"),
]
_ENCHIMENTO = [(re.compile(p, re.I), s) for p, s in ENCHIMENTO]
_VAGOS = [(re.compile(p, re.I), s) for p, s in VAGOS]
_FIM_DE_FRASE = re.compile(r"(?<=[.!?;])\s+(?=[A-ZÀ-Ú0-9\"*(\[])")
_ESTRUTURA = re.compile(r"^\s*(#|\||[-*+] |\d+[.)] |>|!\[|<|---)")


def _limpar(texto):
    """Troca frontmatter, comentários HTML e blocos de código por linhas vazias (preserva a numeração).

    O frontmatter das skills fica de fora: a descrição é uma linha longa de propósito (palavras de acionamento).
    """
    texto = re.sub(r"\A---\n.*?\n---\n", lambda m: "\n" * m.group(0).count("\n"), texto, flags=re.S)
    texto = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), texto, flags=re.S)
    return re.sub(r"^(```|~~~).*?^\1[^\n]*$", lambda m: "\n" * m.group(0).count("\n"), texto, flags=re.S | re.M)


def _palavras(trecho):
    trecho = re.sub(r"`[^`]*`|\[PREENCHER[^\]]*\]|\{\{\w+\}\}|https?://\S+", " x ", trecho)
    return len(re.findall(r"[\wÀ-ú]+", trecho))


def checar(texto, vagos=True):
    """Retorna [(linha, mensagem)] ordenada pela linha."""
    linhas = _limpar(texto).splitlines()
    avisos = []
    padroes = _ENCHIMENTO + (_VAGOS if vagos else [])
    vistas = {}
    paragrafo, inicio = [], 0

    def fechar_paragrafo():
        if paragrafo and _palavras(" ".join(paragrafo)) > MAX_PALAVRAS_PARAGRAFO:
            avisos.append((inicio, f"parágrafo com mais de {MAX_PALAVRAS_PARAGRAFO} palavras: divida ou use lista/tabela"))

    for n, linha in enumerate(linhas, 1):
        bruta = linha.strip()
        if not bruta:
            fechar_paragrafo()
            paragrafo = []
            continue
        sem_codigo = re.sub(r"`[^`]*`", "", bruta)
        sem_citacoes = re.sub(r"\"[^\"]*\"|“[^”]*”", "", sem_codigo)  # termos citados como exemplo
        for rx, sugestao in padroes:
            m = rx.search(sem_citacoes)
            if m:
                avisos.append((n, f"\"{m.group(0)}\": {sugestao}"))
        celulas = [c for c in sem_codigo.strip("|").split("|")] if bruta.startswith("|") else [sem_codigo]
        for celula in celulas:
            for frase in _FIM_DE_FRASE.split(celula):
                if _palavras(frase) > MAX_PALAVRAS_FRASE:
                    avisos.append((n, f"frase com mais de {MAX_PALAVRAS_FRASE} palavras: divida"))
                    break
        chave = re.sub(r"\s+", " ", bruta.lower())
        if (len(chave) >= MIN_CARACTERES_REPETIDA and _palavras(chave) >= MIN_PALAVRAS_REPETIDA and " · " not in chave
                and "preencher" not in chave and not chave.startswith(("|-", "#"))):
            if chave in vistas:
                avisos.append((n, f"linha repetida (igual à linha {vistas[chave]}): cite em vez de repetir"))
            else:
                vistas[chave] = n
        if _ESTRUTURA.match(linha):
            fechar_paragrafo()
            paragrafo = []
        else:
            if not paragrafo:
                inicio = n
            paragrafo.append(bruta)
    fechar_paragrafo()
    return sorted(avisos)
