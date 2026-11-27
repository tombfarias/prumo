"""Verifica a paleta da interface (prumo_cli/gui/index.html) nos temas claro e escuro.

- Contraste WCAG 2.x: texto ≥ 4,5:1; elementos que não são texto ≥ 3:1.
- Cores de estado distinguíveis sob daltonismo (simulação de Machado et al. 2009, severidade 1,0),
  medidas por ΔE2000 ≥ 15.

Uso: python tools/cores.py   (sai com código 1 se algo falhar). Também roda nos testes.
"""

import math
import re
import sys
from pathlib import Path

PAGINA = Path(__file__).resolve().parent.parent / "prumo_cli" / "gui" / "index.html"

# [frente, fundo, mínimo, onde aparece]
PARES = [
    ("texto", "bg", 4.5, "texto principal"), ("texto", "sup", 4.5, "texto em cartões"),
    ("suave", "bg", 4.5, "texto secundário"), ("suave", "sup", 4.5, "texto secundário em cartões"),
    ("suave", "sup2", 4.5, "rótulos da barra lateral"), ("fraco", "sup2", 3, "marcadores e ícones discretos"),
    ("pri-txt", "pri", 4.5, "botão principal"), ("pri", "sup", 4.5, "links e destaques"),
    ("pri-2", "pri-bg", 4.5, "chip ok"), ("ambar-txt", "ambar-bg", 4.5, "chip de lacunas"),
    ("verm", "verm-bg", 4.5, "chip de erro"), ("azul-txt", "azul-bg", 4.5, "chip aprovado / IDs"), ("ambar", "sup", 3, "ponto de lacunas (não texto)"),
    ("azul", "sup", 3, "ponto de aprovado (não texto)"),
    ("roxo", "roxo-bg", 4.5, "chip Figma / do projeto"), ("terra", "terra-bg", 4.5, "chip personalizado"),
    ("verm", "sup", 4.5, "botão de perigo"), ("console-txt", "console", 4.5, "saída do Claude"),
    ("pri", "sup3", 3, "anel de prontidão (não texto)"),
]
# cores de estado que aparecem só como cor (pontos da lista de documentos): completo, lacunas, aprovado, erro.
# Os chips trazem texto ("ausente", "personalizado"...), então não dependem só da cor.
ESTADOS = [("pri", "ambar"), ("pri", "verm"), ("pri", "azul"), ("ambar", "verm"), ("ambar", "azul"), ("azul", "verm")]
MIN_DE = 15

CVD = {
    "normal": None,
    "protanopia": [[.152286, 1.052583, -.204868], [.114503, .786281, .099216], [-.003882, -.048116, 1.051998]],
    "deuteranopia": [[.367322, .860646, -.227968], [.280085, .672501, .047413], [-.01182, .04294, .968881]],
    "tritanopia": [[1.255528, -.076749, -.178779], [-.078411, .930809, .147602], [.004733, .691367, .3039]],
}


def tokens(css):
    claro = re.search(r":root\{(.*?)\}", css, re.S).group(1)
    escuro = re.search(r':root\[data-theme="dark"\]\{(.*?)\}', css, re.S).group(1)
    ler = lambda bloco: {k: v.strip() for k, v in re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{3,6})", bloco)}
    t_claro = ler(claro)
    return {"claro": t_claro, "escuro": {**t_claro, **ler(escuro)}}


def _rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _lin(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def contraste(a, b):
    lum = lambda h: sum(p * _lin(c) for p, c in zip((.2126, .7152, .0722), _rgb(h)))
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + .05) / (y + .05)


def _lab(h, matriz=None):
    c = [_lin(v) for v in _rgb(h)]
    if matriz:
        c = [min(1, max(0, sum(m * v for m, v in zip(linha, c)))) for linha in matriz]
    xyz = [sum(m * v for m, v in zip(linha[:3], c)) / linha[3] for linha in
           ([.4124564, .3575761, .1804375, .95047], [.2126729, .7151522, .072175, 1], [.0193339, .119192, .9503041, 1.08883])]
    f = lambda t: math.cbrt(t) if t > .008856 else 7.787 * t + 16 / 116
    fx, fy, fz = map(f, xyz)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def de2000(p, q):
    (L1, a1, b1), (L2, a2, b2) = p, q
    r = math.pi / 180
    Cm = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    G = .5 * (1 - math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)))
    A1, A2 = a1 * (1 + G), a2 * (1 + G)
    c1, c2 = math.hypot(A1, b1), math.hypot(A2, b2)
    ang = lambda b, a: (math.atan2(b, a) / r) % 360
    h1, h2 = ang(b1, A1), ang(b2, A2)
    dL, dC = L2 - L1, c2 - c1
    dh = 0 if c1 * c2 == 0 else (h2 - h1 - 360 if h2 - h1 > 180 else h2 - h1 + 360 if h2 - h1 < -180 else h2 - h1)
    dH = 2 * math.sqrt(c1 * c2) * math.sin(dh * r / 2)
    Lm, cm = (L1 + L2) / 2, (c1 + c2) / 2
    hm = h1 + h2
    if c1 * c2 != 0:
        hm = ((hm + 360) / 2 if hm < 360 else (hm - 360) / 2) if abs(h1 - h2) > 180 else hm / 2
    T = 1 - .17 * math.cos((hm - 30) * r) + .24 * math.cos(2 * hm * r) + .32 * math.cos((3 * hm + 6) * r) - .2 * math.cos((4 * hm - 63) * r)
    SL = 1 + .015 * (Lm - 50) ** 2 / math.sqrt(20 + (Lm - 50) ** 2)
    SC, SH = 1 + .045 * cm, 1 + .015 * cm * T
    RT = -2 * math.sqrt(cm ** 7 / (cm ** 7 + 25 ** 7)) * math.sin(60 * math.exp(-(((hm - 275) / 25) ** 2)) * r)
    return math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH))


def verificar(css=None):
    """Retorna (linhas do relatório, número de falhas)."""
    temas = tokens(css if css is not None else PAGINA.read_text(encoding="utf-8"))
    linhas, falhas = [], 0
    for nome, t in temas.items():
        linhas.append(f"\n== Tema {nome} ==")
        for f, b, minimo, onde in PARES:
            q = contraste(t[f], t[b])
            ok = q >= minimo
            falhas += not ok
            linhas.append(f"{'✓' if ok else '✗'} {f} {t[f]} / {b} {t[b]}: {q:.2f} (mín. {minimo}) · {onde}")
        for visao, matriz in CVD.items():
            d = sorted((de2000(_lab(t[a], matriz), _lab(t[b], matriz)), a, b) for a, b in ESTADOS)
            ruins = [x for x in d if x[0] < MIN_DE]
            falhas += len(ruins)
            linhas.append(f"{'✗' if ruins else '✓'} {visao:<12} menor ΔE {d[0][0]:.1f} ({d[0][1]} × {d[0][2]})"
                          + (" · abaixo: " + ", ".join(f"{a}×{b} {v:.1f}" for v, a, b in ruins) if ruins else ""))
    return linhas, falhas


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rel, n = verificar()
    print("\n".join(rel))
    print(f"\n{n} falha(s)." if n else "\nTudo certo.")
    sys.exit(1 if n else 0)
