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
        dados = json.loads((raiz / "projeto.prumo.json").read_text(encoding="utf-8-sig"))  # aceita BOM (PowerShell 5.1)
        return dados if isinstance(dados, dict) else {}
    except Exception:
        return {}


def chave(rel):
    """Forma de comparar caminhos: no Windows maiúsculas/minúsculas e barras não importam."""
    rel = (rel or "").replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    return rel.lower() if os.name == "nt" else rel


def aprovados_do(config):
    aprovados = config.get("aprovados") if isinstance(config, dict) else None
    return aprovados if isinstance(aprovados, dict) else {}


def ler_texto(caminho):
    """Lê texto tolerando BOM e arquivos que não são UTF-8 (ex.: salvos em ANSI no Windows)."""
    return Path(caminho).read_bytes().decode("utf-8-sig", "replace")


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


def ferramenta_ausente(resultado):
    """O comando falhou porque o programa não está instalado (sh: 127; cmd do Windows: 9009)?"""
    if resultado.returncode in (127, 9009):
        return True
    saida = (resultado.stdout + resultado.stderr).decode("utf-8", "replace").lower()
    return resultado.returncode != 0 and ("command not found" in saida or "não é reconhecido" in saida
                                          or "is not recognized as an internal" in saida)


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


# ---------------------------------------------------------------- dados sensíveis

SEGREDOS = [
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "chave privada"),
    (r"\bAKIA[0-9A-Z]{16}\b", "chave de acesso da AWS"),
    (r"\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}", "token do GitHub"),
    (r"\b[sr]k_live_[A-Za-z0-9]{16,}", "chave secreta de produção (Stripe)"),
    (r"\bsk-(ant-|proj-)?[A-Za-z0-9_-]{32,}", "chave de API (OpenAI/Anthropic)"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "token do Slack"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "chave de API do Google"),
]


def _cpf_valido(digitos):
    if len(set(digitos)) == 1:
        return False
    for n in (9, 10):
        soma = sum(int(d) * (n + 1 - i) for i, d in enumerate(digitos[:n]))
        if (soma * 10 % 11) % 10 != int(digitos[n]):
            return False
    return True


def _luhn(digitos):
    total = 0
    for i, d in enumerate(reversed(digitos)):
        v = int(d) * (2 if i % 2 else 1)
        total += v - 9 if v > 9 else v
    return total % 10 == 0


# Valores de exemplo/teste conhecidos (não são de ninguém).
EXEMPLOS_PESSOAIS = {"12345678909", "11144477735", "52998224725", "4111111111111111", "4242424242424242",
                     "5555555555554444", "4000056655665556", "5105105105105100", "4012888888881881"}


def segredos(texto):
    return [nome for padrao, nome in SEGREDOS if re.search(padrao, texto)]


def dados_pessoais(texto):
    """Dados pessoais reais (CPF válido, cartão válido; valores de teste conhecidos são aceitos)."""
    achados = []
    for m in re.finditer(r"(?<![\d.-])\d{3}\.\d{3}\.\d{3}-\d{2}(?![\d.-])", texto):
        digitos = re.sub(r"\D", "", m.group(0))
        if digitos not in EXEMPLOS_PESSOAIS and _cpf_valido(digitos):
            achados.append("CPF")
            break
    for m in re.finditer(r"(?<![\d-])(?:\d{4}[ -]){3}\d{4}(?![\d-])|(?<!\d)\d{16}(?!\d)", texto):
        digitos = re.sub(r"\D", "", m.group(0))
        if digitos not in EXEMPLOS_PESSOAIS and digitos[0] in "3456" and _luhn(digitos):
            achados.append("número de cartão")
            break
    return achados
