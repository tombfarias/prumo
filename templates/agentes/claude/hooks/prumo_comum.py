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
LACUNA = re.compile(r"\[(?:PREENCHER|FILL)\b")  # [FILL: ...] nos projetos em inglês


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


# ---------------------------------------------------------------- idioma das mensagens

# Projetos em inglês (projeto.prumo.json -> "idioma": "en"): as mensagens dos hooks saem em inglês.
# Chave = trecho em português, como aparece nas mensagens; o resto (caminhos, comandos) passa intacto.
EN = {
    "Os testes passaram do tempo limite. Informe o usuário.": "The tests timed out. Tell the user.",
    "Não foi possível rodar os testes": "Could not run the tests",
    ": o programa não está instalado ou não está no PATH. ": ": the program is not installed or not on PATH. ",
    "Não instale nada globalmente por conta própria: avise o usuário qual ferramenta falta.":
        "Do not install anything globally on your own: tell the user which tool is missing.",
    "Os testes falharam": "The tests failed",
    ". Corrija antes de encerrar ou explique ao usuário por que não foi possível:":
        ". Fix them before finishing or explain to the user why you could not:",
    " · cliente ": " · client ", " · perfil ": " · profile ",
    " aprovado(s), ": " approved, ", " completo(s), ": " complete, ", " com lacunas": " with gaps",
    "Somente leitura (aprovados): ": "Read-only (approved): ",
    "Regras: AGENTS.md. Use `prumo contexto <ID>` para carregar só a trilha necessária.":
        "Rules: AGENTS.md. Use `prumo contexto <ID>` to load only the trail you need.",
    "O conteúdo para ": "The content for ", " parece conter ": " seems to contain ",
    ". Segredos ficam só no .env (documente o nome da variável em .env.example) e a documentação usa dados fictícios, nunca dados reais de clientes. ":
        ". Secrets live only in .env (document the variable name in .env.example) and the documentation uses fictitious data, never real client data. ",
    "Se for um falso positivo, peça ao usuário para desligar a verificação (hooks.bloquear_dados_sensiveis: false).":
        "If this is a false positive, ask the user to turn the check off (hooks.bloquear_dados_sensiveis: false).",
    "Acesso bloqueado a ": "Access blocked to ",
    ": arquivos de segredos não podem ser lidos nem editados por agentes. ":
        ": secret files cannot be read or edited by agents. ",
    "Documente variáveis em .env.example e peça ao usuário para preencher o .env.":
        "Document variables in .env.example and ask the user to fill in .env.",
    " foi aprovado pelo cliente em ": " was approved by the client on ", " e é somente leitura.": " and is read-only.",
    "Para alterar: registre um pedido com ": "To change it: file a request with ",
    ", faça a análise de impacto e, depois da aprovação do cliente, o usuário roda ":
        ", do the impact analysis and, after the client approves, the user runs ",
    " é gerado automaticamente. Não edite: rode ": " is generated automatically. Do not edit it: run ",
    "A lista de documentos aprovados só pode ser alterada pelo usuário (prumo aprovar/desaprovar).":
        "Only the user can change the list of approved documents (prumo aprovar/desaprovar).",
    "Conteúdo inválido para projeto.prumo.json (JSON malformado).": "Invalid content for projeto.prumo.json (malformed JSON).",
    "Comando bloqueado: altera ": "Command blocked: it changes ",
    ", que é somente leitura (aprovado pelo cliente ou gerado pelo Prumo).":
        ", which is read-only (approved by the client or generated by Prumo).",
    "Comando bloqueado: ": "Command blocked: ", "Comando: ": "Command: ",
    "Mudança em documento aprovado passa por ": "A change to an approved document goes through ",
    "; arquivos gerados se refazem com o comando do Prumo.": "; generated files are rebuilt with the Prumo command.",
    "Se for realmente necessário, explique ao usuário e peça que ele rode o comando no terminal, ou que adicione uma exceção em projeto.prumo.json -> hooks.comandos_permitidos.":
        "If it is really needed, explain it to the user and ask them to run the command in the terminal, or to add an exception in projeto.prumo.json -> hooks.comandos_permitidos.",
    "remoção recursiva da raiz, da pasta pessoal ou do projeto inteiro": "recursive removal of the root, the home folder or the whole project",
    "remoção da pasta .git ou da documentação": "removal of the .git folder or the documentation",
    "remoção recursiva ampla no PowerShell": "broad recursive removal in PowerShell",
    "use --force-with-lease, se realmente necessário": "use --force-with-lease if really needed",
    "descarta trabalho não commitado": "discards uncommitted work",
    "apaga arquivos não versionados": "deletes untracked files",
    "descarta alterações locais": "discards local changes",
    "exclusão forçada de branch": "forced branch deletion",
    "DROP de banco, schema ou tabela": "DROP of a database, schema or table",
    "TRUNCATE de tabela": "TRUNCATE of a table",
    "reset de banco pelo Prisma": "database reset through Prisma",
    "limpeza total do banco": "full database wipe",
    "WP-CLI apagando o banco ou o conteúdo do site": "WP-CLI deleting the database or the site content",
    "sem --dry-run (rode antes com --dry-run e faça backup)": "without --dry-run (run it with --dry-run first and back up)",
    "formatação de disco": "disk formatting", "permissão 777": "777 permission",
    "execução de script baixado da internet sem revisão": "running a script downloaded from the internet without review",
    "publicação de pacote": "package publishing", "leitura de arquivo .env (segredos)": "reading an .env file (secrets)",
    "O lint encontrou problemas em ": "The linter found problems in ",
    "Mudança significativa nesta sessão: ": "Significant change in this session: ",
    " arquivo(s) de código, ~": " code file(s), ~", " linha(s)": " line(s)", "; áreas sensíveis: ": "; sensitive areas: ",
    "Arquivos: ": "Files: ",
    "Antes de encerrar, faça as duas verificações obrigatórias do projeto:": "Before finishing, do the project's two mandatory checks:",
    "1. Documentação: siga ": "1. Documentation: follow ",
    "Documentos provavelmente afetados: ": "Documents likely affected: ",
    "verifique a trilha da história": "check the story's trail",
    "Documentos aprovados não podem ser editados: registre um pedido de mudança.":
        "Approved documents cannot be edited: file a change request.",
    "2. Segurança: siga ": "2. Security: follow ",
    " sobre esses arquivos e registre os achados em ": " on these files and record the findings in ",
    "Depois, resuma ao usuário o que foi atualizado e os achados de segurança (ou que não houve achados).":
        "Then summarize to the user what was updated and the security findings (or that there were none).",
    "autenticação/autorização": "authentication/authorization", "banco de dados": "database", "rotas/API": "routes/API",
    "dependências": "dependencies", "infraestrutura": "infrastructure", "configuração": "configuration",
    "dados sensíveis": "sensitive data", "caminho sensível do projeto": "sensitive project path",
    "chave privada": "private key", "chave de acesso da AWS": "AWS access key", "token do GitHub": "GitHub token",
    "chave secreta de produção (Stripe)": "production secret key (Stripe)", "chave de API (OpenAI/Anthropic)": "API key (OpenAI/Anthropic)",
    "token do Slack": "Slack token", "chave de API do Google": "Google API key", "número de cartão": "card number",
}
_EN_RX = re.compile("|".join(re.escape(k) for k in sorted(EN, key=len, reverse=True)))


def idioma_projeto():
    return str(carregar_config(raiz_projeto()).get("idioma") or "pt-BR")


def traduzir(msg):
    """Mensagem no idioma do projeto (pt-BR, o padrão, sai como está)."""
    try:
        if not idioma_projeto().lower().startswith("en"):
            return msg
    except Exception:
        return msg
    return _EN_RX.sub(lambda m: EN[m.group(0)], msg)


def escrever_stderr(msg):
    msg = traduzir(msg)
    sys.stderr.buffer.write((msg.rstrip() + "\n").encode("utf-8"))
    sys.stderr.flush()


def escrever_stdout(msg):
    msg = traduzir(msg)
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
    return len(LACUNA.findall(sem_comentarios))


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
