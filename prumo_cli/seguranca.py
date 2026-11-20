"""Varredura estática leve de falhas comuns de segurança (complementa a revisão manual da skill)."""

import os
import re
from pathlib import Path

from .rastreio import IGNORAR_PASTAS

EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro", ".php", ".rb", ".go",
       ".java", ".kt", ".cs", ".dart", ".rs", ".swift", ".sql", ".yml", ".yaml", ".json", ".toml", ".ini",
       ".env.example", ".html", ".sh", ".ps1", ".tf"}
NOMES_EXTRAS = {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}
IGNORAR_ARQUIVOS = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "composer.lock", "projeto.prumo.json"}

# (id, gravidade, descrição, regex, extensões ou None)
REGRAS = [
    ("chave-privada", "Crítica", "Chave privada no código", r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", None),
    ("aws-chave", "Crítica", "Chave de acesso AWS", r"\bAKIA[0-9A-Z]{16}\b", None),
    ("token-conhecido", "Crítica", "Token de serviço (GitHub/Slack/Stripe/Google/OpenAI/Anthropic)",
     r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|xox[baprs]-[A-Za-z0-9-]{10,}|sk_live_[A-Za-z0-9]{20,}|"
     r"AIza[0-9A-Za-z_-]{35}|sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{32,})\b", None),
    ("segredo-literal", "Alta", "Senha, segredo ou token escrito diretamente no código",
     r"""(?i)\b(password|passwd|senha|secret|segredo|api[_-]?key|token|jwt[_-]?secret|client[_-]?secret)\b\s*[:=]\s*['"][^'"\s]{6,}['"]""",
     None),
    ("sql-concatenado", "Alta", "SQL montado com concatenação/interpolação (risco de injeção)",
     r"""(?i)(select|insert|update|delete)\b[^;\n]{0,80}\b(from|into|set|where)\b[^;\n]*(['"]\s*\+\s*\w|\$\{|%s['"]\s*%|f['"][^'"]*\{|\.format\()""",
     None),
    ("eval", "Alta", "Execução dinâmica de código (eval/exec/new Function)",
     r"\b(eval|exec)\s*\(|new\s+Function\s*\(", {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".php", ".rb"}),
    ("shell-injecao", "Alta", "Comando de shell com entrada possivelmente externa",
     r"(shell\s*=\s*True|os\.system\s*\(|child_process\.exec\s*\(|\bexecSync\s*\(|shell_exec\s*\(|\bsystem\s*\(\s*\$)", None),
    ("tls-desligado", "Alta", "Verificação de certificado TLS desativada",
     r"(verify\s*=\s*False|rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0|InsecureSkipVerify\s*:\s*true|CURLOPT_SSL_VERIFYPEER\s*,\s*false)",
     None),
    ("cors-aberto", "Média", "CORS liberado para qualquer origem",
     r"""(Access-Control-Allow-Origin['"]?\s*[:,]\s*['"]\*|origin\s*:\s*['"]\*['"]|allow_origins\s*=\s*\[\s*['"]\*['"]|cors\(\s*\)|CORS_ALLOW_ALL_ORIGINS\s*=\s*True)""",
     None),
    ("debug-ligado", "Média", "Modo debug ligado (não pode ir para produção)",
     r"(?i)(\bDEBUG\s*=\s*True\b|app\.run\([^)]*debug\s*=\s*True|APP_DEBUG\s*=\s*true)", None),
    ("html-sem-escape", "Média", "HTML inserido sem escape (risco de XSS)",
     r"(dangerouslySetInnerHTML|\.innerHTML\s*=|v-html\s*=|\{\{\{|\|\s*safe\b|mark_safe\s*\(|\{!!)", None),
    ("hash-fraco", "Média", "Algoritmo de hash fraco (MD5/SHA-1) — inadequado para senhas",
     r"(?i)\b(md5|sha1)\s*\(|createHash\(\s*['\"](md5|sha1)['\"]|hashlib\.(md5|sha1)\b", None),
    ("aleatorio-inseguro", "Baixa", "Gerador aleatório não criptográfico (não use para tokens)",
     r"(Math\.random\(\)|\brandom\.(random|randint|choice)\()", None),
    ("http-sem-tls", "Baixa", "URL http:// (sem TLS) fora de localhost",
     r"http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]|schemas\.|www\.w3\.org|json-schema\.org)[\w.-]+\.\w{2,}", None),
    ("jwt-sem-verificacao", "Alta", "JWT decodificado sem verificar assinatura",
     r"(jwt\.decode\([^)]*verify\s*=\s*False|options\s*=\s*\{[^}]*verify_signature['\"]?\s*:\s*False|algorithms\s*=\s*\[\s*['\"]none['\"])",
     None),
]
COMPILADAS = [(i, g, d, re.compile(r), e) for i, g, d, r, e in REGRAS]
ORDEM = {"Crítica": 0, "Alta": 1, "Média": 2, "Baixa": 3}
SEGREDOS = {"chave-privada", "aws-chave", "token-conhecido", "segredo-literal"}


def mascarar(texto):
    """Não repete o segredo no relatório: mantém só os 4 primeiros caracteres de cada valor."""
    texto = re.sub(r"""(['"])([^'"]{4})[^'"]*\1""", lambda m: f"{m.group(1)}{m.group(2)}…{m.group(1)}", texto)
    return re.sub(r"\b([A-Za-z0-9_-]{4})[A-Za-z0-9_-]{12,}\b", r"\1…", texto)


def _arquivos(raiz, pastas):
    vistos = set()
    alvos = [raiz / p for p in pastas if (raiz / p).is_dir()]
    for nome in os.listdir(raiz):  # arquivos de configuração na raiz
        p = raiz / nome
        if p.is_file():
            yield p
    for base in alvos:
        for dirpath, dirnames, nomes in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in IGNORAR_PASTAS]
            for nome in nomes:
                p = Path(dirpath) / nome
                if p not in vistos:
                    vistos.add(p)
                    yield p


def varrer(projeto, pastas=None, arquivos=None):
    raiz = projeto.raiz
    pastas = pastas or list(dict.fromkeys((projeto.config.get("pastas_codigo") or []) + [".github", "infra", "config"]))
    candidatos = [raiz / a for a in arquivos] if arquivos else _arquivos(raiz, pastas)
    achados = []
    for caminho in candidatos:
        nome = caminho.name
        if nome in IGNORAR_ARQUIVOS or nome == ".env" or (nome.startswith(".env.") and nome != ".env.example"):
            continue
        sufixo = ".env.example" if nome == ".env.example" else caminho.suffix.lower()
        if sufixo not in EXT and nome not in NOMES_EXTRAS:
            continue
        if nome.endswith((".min.js", ".map")):
            continue
        try:
            if not caminho.is_file() or caminho.stat().st_size > 800_000:
                continue
            linhas = caminho.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        rel = caminho.relative_to(raiz).as_posix()
        teste = bool(re.search(r"(^|/)(tests?|__tests__|spec)/|\.(test|spec)\.|_test\.|test_", rel))
        for n, linha in enumerate(linhas, 1):
            if "prumo:ignorar" in linha or len(linha) > 2000:
                continue
            for ident, grav, desc, rx, exts in COMPILADAS:
                if exts and sufixo not in exts:
                    continue
                if rx.search(linha):
                    if teste and grav in ("Baixa", "Média"):
                        continue
                    if ident == "segredo-literal" and re.search(r"(?i)(example|exemplo|changeme|placeholder|xxx|\*\*\*|<.+>|process\.env|os\.environ|getenv)", linha):
                        continue
                    trecho = linha.strip()[:160]
                    if ident in SEGREDOS:
                        trecho = mascarar(trecho)
                    achados.append({"regra": ident, "gravidade": grav, "descricao": desc, "arquivo": rel,
                                    "linha": n, "trecho": trecho})
    achados.sort(key=lambda a: (ORDEM[a["gravidade"]], a["arquivo"], a["linha"]))
    return achados
