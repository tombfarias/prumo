"""Funções compartilhadas pelos hooks do Prumo para o Claude Code.

Os hooks recebem um JSON pela entrada padrão e respondem por código de saída:
0 = segue normalmente; 2 = bloqueia a ação e a mensagem em stderr volta para o Claude.
Só usam a biblioteca padrão do Python (3.9+).
"""

import json
import os
import re
import sys
from pathlib import Path

MARCADOR_LACUNA = "[PREENCHER"


def ler_entrada():
    try:
        bruto = sys.stdin.buffer.read().decode("utf-8", "replace")
        return json.loads(bruto) if bruto.strip() else {}
    except Exception:
        return {}


def raiz_projeto():
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    # .claude/hooks/<arquivo>.py -> raiz do projeto
    return Path(__file__).resolve().parents[2]


def carregar_config(raiz):
    try:
        return json.loads((raiz / "projeto.prumo.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def relativo(raiz, caminho):
    """Caminho relativo à raiz, com barras '/', ou None se estiver fora do projeto."""
    if not caminho:
        return None
    try:
        p = Path(caminho)
        if not p.is_absolute():
            p = raiz / p
        return p.resolve().relative_to(raiz.resolve()).as_posix()
    except Exception:
        return None


def escrever_stderr(msg):
    sys.stderr.buffer.write((msg.rstrip() + "\n").encode("utf-8"))
    sys.stderr.flush()


def escrever_stdout(msg):
    sys.stdout.buffer.write((msg.rstrip() + "\n").encode("utf-8"))
    sys.stdout.flush()


def bloquear(msg):
    escrever_stderr("[Prumo] " + msg)
    sys.exit(2)


def documentos(raiz):
    pasta = raiz / "docs"
    if not pasta.is_dir():
        return []
    return sorted(p for p in pasta.rglob("*.md") if "diagramas" not in p.parts)


def contar_lacunas(texto):
    sem_comentarios = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    return sem_comentarios.count(MARCADOR_LACUNA)


# ---------------------------------------------------------------- mudanças significativas

ARQUIVO_ALTERACOES = "alteracoes.json"

SENSIVEIS = [
    (r"auth|login|logout|sess(ao|ion)|senha|password|token|jwt|oauth|permiss|rbac|acl|role", "autenticação/autorização"),
    (r"migrat|schema\.prisma|(^|/)models?/|entit|\.sql$", "banco de dados"),
    (r"(^|/)(routes?|controllers?|api|middlewares?|handlers?)/|webhook", "rotas/API"),
    (r"(^|/)(package\.json|requirements[^/]*\.txt|pyproject\.toml|composer\.json|Gemfile|go\.mod|Cargo\.toml|pubspec\.yaml)$",
     "dependências"),
    (r"Dockerfile|docker-compose|\.github/workflows|\.tf$|nginx|vercel\.json|netlify\.toml|fly\.toml", "infraestrutura"),
    (r"(^|/)\.env\.example$|(^|/)config/|settings\.py$", "configuração"),
    (r"upload|pagamento|payment|checkout|cript|crypto", "dados sensíveis"),
]

DOCS_POR_AREA = [
    (r"migrat|schema|(^|/)models?/|entit|\.sql$", ["docs/06-banco-de-dados.md", "docs/04-uml/classes.md", "docs/04-uml/objetos.md"]),
    (r"(^|/)(routes?|controllers?|api|handlers?|pages?|app|screens?|telas?|components?|componentes)/",
     ["docs/03-casos-de-uso.md", "docs/04-uml/sequencia.md", "docs/05-interface.md"]),
    (r"(^|/)(package\.json|requirements[^/]*\.txt|pyproject\.toml|composer\.json|Gemfile|go\.mod|Cargo\.toml|pubspec\.yaml)$",
     ["docs/07-arquitetura.md", "docs/04-uml/componentes.md", "docs/04-uml/pacotes.md"]),
    (r"Dockerfile|docker-compose|\.github/workflows|\.tf$|nginx|vercel\.json|netlify\.toml|fly\.toml",
     ["docs/04-uml/implantacao.md", "docs/07-arquitetura.md", "docs/11-entrega.md"]),
    (r"(^|/)\.env\.example$|(^|/)config/", ["docs/07-arquitetura.md", "docs/11-entrega.md", "README.md"]),
    (r"(^|/)tests?/|\.test\.|\.spec\.|_test\.|test_", ["docs/09-plano-de-testes.md"]),
    (r"auth|login|senha|password|token|permiss|rbac|role", ["docs/12-seguranca.md", "docs/07-arquitetura.md"]),
]


def eh_documentacao(rel):
    return rel.startswith("docs/") or rel.lower().endswith((".md", ".mdx", ".txt"))


def ler_alteracoes(raiz):
    try:
        return json.loads((raiz / ".prumo" / ARQUIVO_ALTERACOES).read_text(encoding="utf-8"))
    except Exception:
        return {"desde": None, "arquivos": {}}


def gravar_alteracoes(raiz, dados):
    pasta = raiz / ".prumo"
    pasta.mkdir(exist_ok=True)
    (pasta / ARQUIVO_ALTERACOES).write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


def areas_sensiveis(arquivos, extras=()):
    regras = list(SENSIVEIS) + [(p, "caminho sensível do projeto") for p in extras]
    achadas = []
    for padrao, nome in regras:
        if any(re.search(padrao, a, re.I) for a in arquivos) and nome not in achadas:
            achadas.append(nome)
    return achadas


def documentos_sugeridos(raiz, arquivos):
    sugeridos = []
    for padrao, docs in DOCS_POR_AREA:
        if any(re.search(padrao, a, re.I) for a in arquivos):
            sugeridos += [d for d in docs if d not in sugeridos]
    sugeridos.append("docs/08-backlog.md")
    return [d for d in sugeridos if (raiz / d).exists()]
