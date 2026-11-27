#!/usr/bin/env python3
"""Guarda de privacidade do repositório público do Prumo.

Impede que dados pessoais do autor, da máquina dele ou segredos em geral cheguem ao GitHub:
- termos descobertos na hora, na máquina de quem roda (nada pessoal fica gravado neste arquivo): nome de
  usuário do sistema, pasta pessoal (também no formato curto 8.3), nome do computador, pasta local do
  repositório, e-mails e nome do git, dados de config/freelancer.json, pastas, projetos e clientes de
  config/projetos.json e os termos de ~/.prumo/privado.txt;
- regras genéricas: e-mails reais, pastas de usuário (C:\\Users\\<nome>, /home/<nome>, WSL), tokens e chaves,
  URL com senha, Authorization: Basic, CPF/CNPJ válidos e arquivos que nunca devem ser versionados.

Os hooks do git varrem o conteúdo completo de cada arquivo novo ou alterado: UTF-8, UTF-16, CP1252, texto
escapado (\\u, %XX, &#..;) e, em binários, o texto legível e o de dentro de ZIP (docx/xlsx), PDF e PNG. Se o git
falhar, o guarda bloqueia em vez de liberar.

Modos (python .githooks/privacidade.py <modo>):
  instalar              instala os hooks do git deste clone (em .git/hooks; bloqueiam se o guarda sumir)
  pre-commit            arquivos preparados e identidade do commit (hook do git)
  commit-msg <arquivo>  mensagem do commit (hook do git)
  pre-push [remoto]     commits, tags e objetos que vão subir; lê a entrada padrão do git (hook do git)
  claude                hook PreToolUse do Claude Code (Bash/PowerShell)
  tudo [--historico]    arquivos versionados e novos; com --historico, também todos os commits e tags
  texto                 texto da entrada padrão

Saída: 0 = nada encontrado; 1 = achados ou erro (no modo claude, 2 = bloqueia a ação).
Falso positivo de uma regra genérica de conteúdo: acrescente "privacidade:ignorar" na linha. Termos pessoais,
arquivos proibidos e identidade não têm exceção. Variáveis: PRUMO_PRIVADO (outro arquivo de termos) e
PRUMO_PRIVACIDADE_AMBIENTE=0 (não usa os termos da máquina; para testes). No GitHub Actions os termos da máquina
ficam desligados. Só biblioteca padrão, sem rede.
"""

import base64
import getpass
import glob
import html
import io
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import unicodedata
import urllib.parse
import zipfile
import zlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HOOKS = ("pre-commit", "commit-msg", "pre-push")
MARCADOR = "prumo-privacidade"
IGNORAR = "privacidade:ignorar"
JANELA = 20000
SOBREPOSICAO = 512
MAX_RELATO = 40
MAX_DESCOMPACTADO = 50_000_000

NOMES_GENERICOS = {
    "public", "default", "default user", "all", "all users", "shared", "guest", "root", "admin", "administrator",
    "administrador", "runner", "runneradmin", "ubuntu", "vagrant", "docker", "codespace", "codespaces", "vscode",
    "node", "app", "appuser", "pi", "jovyan", "me", "www", "www-data", "git", "user", "username", "usuario", "voce",
    "you", "nome", "name", "seu-usuario", "seu_usuario", "seuusuario", "seunome", "example", "exemplo", "fulano",
    "localhost", "prumo", "contato", "comercial", "financeiro", "suporte", "vendas", "atendimento", "notebook",
    "desktop", "laptop", "pc", "dev", "home", "casa", "trabalho", "work", "projetos", "projects", "codigo", "code",
    "src", "repos", "github", "cliente", "projeto", "teste", "test", "demo",
}
CAMINHOS_EXEMPLO = {"c:/prumo", "/c/prumo", "/mnt/c/prumo", "c:/projetos", "d:/projetos", "~/prumo"}
DOMINIOS_EXEMPLO = {
    "domain.com", "email.com", "empresa.com", "empresa.com.br", "suaempresa.com", "suaempresa.com.br",
    "seudominio.com", "seudominio.com.br", "dominio.com", "dominio.com.br", "seusite.com", "seusite.com.br",
}
EXTENSOES_ARQUIVO = {
    "png", "jpg", "jpeg", "webp", "svg", "gif", "avif", "ico", "bmp", "pdf", "js", "mjs", "css", "json", "md",
    "txt", "woff", "woff2", "ttf", "otf", "mp4", "webm",
}

# ------------------------------------------------------------------ regras genéricas

RX_EMAIL = re.compile(r"(?<![\w.%+-])([A-Za-z0-9][A-Za-z0-9._%+-]*)@((?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})(?![\w-])")
_NOME_PASTA = r"([^\\/\s'\"`<>|*?:;,()\[\]{}]+)"
RX_PASTA_USUARIO = re.compile(
    r"(?:(?<![\w])[A-Za-z]:|(?<![\w.~$/])/(?:mnt/)?[A-Za-z](?=[\\/](?i:users)[\\/]))[\\/]+"
    r"(?i:users|documents and settings)[\\/]+" + _NOME_PASTA +
    r"|(?<![\w.~$/-])/(?:home|Users)/" + _NOME_PASTA +
    r"|(?i:\\\\wsl(?:\.localhost|\$)\\[^\\\s]+\\home\\)" + _NOME_PASTA)
SEGREDOS = [
    ("chave privada", re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----")),
    ("chave de acesso da AWS", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("token do GitHub", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})")),
    ("chave de API (Anthropic/OpenAI)", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{32,}")),
    ("token do Figma", re.compile(r"\bfigd_[A-Za-z0-9_-]{20,}")),
    ("token do Slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("chave do Google", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("chave do Stripe", re.compile(r"\b[rs]k_live_[A-Za-z0-9]{20,}")),
    ("token do npm/PyPI", re.compile(r"\b(?:npm_[A-Za-z0-9]{36}|pypi-[A-Za-z0-9_-]{50,})")),
    ("JWT", re.compile(r"(?<![\w-])eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]
PREFIXOS_SEGREDO = re.compile(r"^(?:sk-(?:ant-|proj-)?|gh[pousr]_|github_pat_|figd_|xox[abprs]-|AIza|[rs]k_live_|"
                              r"npm_|pypi-|AKIA|ASIA)")
ASSINATURAS_EXEMPLO = {"SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"}  # JWT de exemplo do jwt.io
RX_URL_SENHA = re.compile(r"(?<![\w+.-])[a-z][a-z0-9+.-]*://([^/\s:@'\"`]+):([^/\s@'\"`]+)@[\w.-]+", re.I)
RX_BASIC = re.compile(r"(?i)\bAuthorization:\s*Basic\s+([A-Za-z0-9+/=]{8,})")
RX_SENHA_EXEMPLO = re.compile(
    r"(?i)^(?:senha|password|pass|passwd|pwd|secret|segredo|changeme|troque\w*|guest|x{3,}|\*+|\.{3}|…|"
    r"\$\{?\w+\}?|%\w+%|<[^>]*>|\{\{[^}]*\}\}|\[[^\]]*\]|user|usuario|postgres|root|admin)$")
RX_CPF = re.compile(r"(?<![\d./-])(\d{3})\.(\d{3})\.(\d{3})-(\d{2})(?![\d./-])")
RX_CNPJ = re.compile(r"(?<![\d./-])(\d{2})\.(\d{3})\.(\d{3})/(\d{4})-(\d{2})(?![\d./-])")
DOCUMENTOS_EXEMPLO = {"12345678909", "11144477735", "11222333000181"}  # CPF/CNPJ de exemplo conhecidos

CAMINHOS_PROIBIDOS = [
    ("arquivo .env com valores reais",
     re.compile(r"(?:^|/)\.env(?:\.(?!(?:example|exemplo|sample|modelo|template|dist)$)[^/]+)?$", re.I)),
    ("configuração pessoal do Prumo", re.compile(r"^config/(?:freelancer|projetos)\.json$|^config/\.janela/", re.I)),
    ("estado local do Prumo", re.compile(r"(?:^|/)\.prumo/")),
    ("configuração local do Claude", re.compile(r"(?:^|/)(?:CLAUDE\.local\.md|\.claude/settings\.local\.json)$", re.I)),
    ("chave ou certificado",
     re.compile(r"\.(?:pem|key|p12|pfx|jks|keystore|ppk|kdbx)$|(?:^|/)id_(?:rsa|dsa|ecdsa|ed25519)(?:\.pub)?$", re.I)),
    ("executável (os .exe saem só pelo CI, nas Releases)", re.compile(r"\.(?:exe|dll|msi)$", re.I)),
    ("histórico ou credencial local",
     re.compile(r"(?:^|/)(?:\.(?:bash_history|zsh_history|python_history|psql_history|netrc|git-credentials|npmrc|pypirc)"
                r"|ConsoleHost_history\.txt)$", re.I)),
    ("log local", re.compile(r"\.log$", re.I)),
]


# ------------------------------------------------------------------ utilitários

class ErroGit(Exception):
    """O git falhou: o guarda não consegue conferir e por isso bloqueia."""


def dobrar(texto):
    """Remove acentos (Tomé -> Tome) para achar também a grafia sem acento."""
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _git(args, entrada=None, cwd=None):
    env = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1"}  # ver os objetos que de fato sobem, não os substitutos
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=str(cwd or RAIZ), input=entrada,
                           capture_output=True, timeout=600, env=env)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, b"", str(e).encode()
    return r.returncode, r.stdout, r.stderr


def git(*args, entrada=None):
    """Versão tolerante: devolve "" se o git falhar (só para consultas cuja ausência é normal)."""
    codigo, saida, _ = _git(args, entrada)
    return saida.decode("utf-8", "replace") if codigo == 0 else ""


def git_ok(*args, entrada=None, bruto=False):
    """Versão estrita: se o git falhar, levanta ErroGit (o guarda bloqueia)."""
    codigo, saida, erro = _git(args, entrada)
    if codigo != 0:
        msg = erro.decode("utf-8", "replace").strip()[:400] or f"código {codigo}"
        raise ErroGit(f"git {' '.join(args[:2])}: {msg}")
    return saida if bruto else saida.decode("utf-8", "replace")


def ler_texto(caminho):
    try:
        return Path(caminho).read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return ""


def ler_json(caminho):
    texto = ler_texto(caminho)
    try:
        return json.loads(texto) if texto.strip() else None
    except ValueError:
        return None


def linhas(texto):
    """Divide só em \\n (splitlines também quebraria em \\f, \\v, U+2028... e esconderia o resto da linha)."""
    return [l[:-1] if l.endswith("\r") else l for l in texto.split("\n")]


def _inflar(bloco, orcamento):
    try:
        saida = zlib.decompressobj().decompress(bloco, max(orcamento[0], 0))
    except zlib.error:
        return b""
    orcamento[0] -= len(saida)
    return saida


def _literal_pdf(bruto):
    saida, i = bytearray(), 0
    while i < len(bruto):
        c = bruto[i]
        if c == 0x5C and i + 1 < len(bruto):  # barra invertida
            m = re.match(rb"[0-7]{1,3}", bruto[i + 1:i + 4])
            if m:
                saida.append(int(m.group(0), 8) & 0xFF)
                i += 1 + len(m.group(0))
                continue
            saida.append(bruto[i + 1])
            i += 2
            continue
        saida.append(c)
        i += 1
    return bytes(saida)


def textos_compactados(dados, profundidade, orcamento):
    """Texto de dentro de formatos compactados: ZIP (docx/xlsx/odt), PDF (FlateDecode e strings UTF-16) e PNG."""
    saida = []
    if profundidade > 3 or orcamento[0] <= 0:
        return saida
    if dados.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(dados)) as z:
                for info in z.infolist()[:5000]:
                    saida.append(info.filename)
                    if info.file_size > orcamento[0]:
                        continue
                    conteudo = z.read(info)
                    orcamento[0] -= len(conteudo)
                    saida.append(decodificar(conteudo, profundidade + 1, orcamento)[0])
        except (zipfile.BadZipFile, OSError, RuntimeError, NotImplementedError, ValueError, EOFError):
            pass
    if dados.startswith(b"%PDF"):
        for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", dados, re.S):
            inflado = _inflar(m.group(1), orcamento)
            if inflado:
                saida.append(decodificar(inflado, profundidade + 1, orcamento)[0])
        for m in re.finditer(rb"<\s*(FE\s*FF(?:\s*[0-9A-Fa-f]{2})+)\s*>", dados):
            try:
                saida.append(bytes.fromhex(re.sub(rb"\s", b"", m.group(1)).decode()).decode("utf-16-be", "replace"))
            except ValueError:
                pass
        for m in re.finditer(rb"\((\xfe\xff(?:[^\\)]|\\.)*)\)", dados, re.S):
            saida.append(_literal_pdf(m.group(1)).decode("utf-16", "replace"))
    if dados.startswith(b"\x89PNG\r\n\x1a\n"):
        pos = 8
        while pos + 8 <= len(dados):
            tamanho = int.from_bytes(dados[pos:pos + 4], "big")
            tipo, corpo = dados[pos + 4:pos + 8], dados[pos + 8:pos + 8 + tamanho]
            pos += 12 + tamanho
            if tipo == b"zTXt":
                chave, _, resto = corpo.partition(b"\0")
                saida += [chave.decode("latin-1"), _inflar(resto[1:], orcamento).decode("latin-1", "replace")]
            elif tipo == b"iTXt":
                chave, _, resto = corpo.partition(b"\0")
                comprimido, resto = resto[:1] == b"\x01", resto[2:]
                _, _, resto = resto.partition(b"\0")  # idioma
                _, _, texto = resto.partition(b"\0")  # palavra-chave traduzida
                texto = _inflar(texto, orcamento) if comprimido else texto
                saida += [chave.decode("latin-1"), texto.decode("utf-8", "replace")]
    return saida


def decodificar(dados, profundidade=0, orcamento=None):
    """Texto de um arquivo: UTF-8, UTF-16/32 (com ou sem BOM), CP1252 ou, em binários, o texto legível e o de
    dentro de ZIP/PDF/PNG. Devolve (texto, binario)."""
    orcamento = orcamento if orcamento is not None else [MAX_DESCOMPACTADO]
    for bom, codificacao in ((b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe\x00\x00", "utf-32-le"),
                             (b"\x00\x00\xfe\xff", "utf-32-be"), (b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be")):
        if dados.startswith(bom):
            return dados[len(bom):].decode(codificacao, "replace"), False
    assinatura = dados.startswith((b"PK\x03\x04", b"%PDF", b"\x89PNG\r\n\x1a\n"))
    amostra = dados[:8000]
    if b"\0" in amostra and not assinatura:
        metade = max(len(amostra) // 2, 1)
        pares, impares = amostra[0::2].count(0), amostra[1::2].count(0)
        if impares > metade * 0.3 and pares < metade * 0.05:
            return dados.decode("utf-16-le", "replace"), False
        if pares > metade * 0.3 and impares < metade * 0.05:
            return dados.decode("utf-16-be", "replace"), False
    if b"\0" in amostra or assinatura:
        partes = [p.decode("utf-8", "replace") for p in re.findall(rb"(?:[\x20-\x7e\t]|[\xc2-\xf4][\x80-\xbf]{1,3}){4,}",
                                                                     dados)]
        partes += [p.decode("utf-16-le", "replace") for p in re.findall(rb"(?:[\x20-\x7e]\x00){4,}", dados)]
        partes += textos_compactados(dados, profundidade, orcamento)
        return "\n".join(partes), True
    try:
        return dados.decode("utf-8"), False
    except UnicodeDecodeError:
        return dados.decode("cp1252", "replace"), False


def usar_ambiente():
    if os.environ.get("GITHUB_ACTIONS", "").strip().lower() == "true":
        return False
    return os.environ.get("PRUMO_PRIVACIDADE_AMBIENTE", "1").strip() != "0"


def dono_do_repositorio():
    url = git("remote", "get-url", "origin").strip()
    m = re.search(r"[:/]([^/\s:]+)/([^/\s:]+?)(?:\.git)?/?$", url)
    return (m.group(1), m.group(2)) if m else ("", "")


def usuario_noreply(email):
    m = re.match(r"^(?:\d+\+)?([^@+]+)@users\.noreply\.github\.com$", (email or "").strip(), re.I)
    return m.group(1) if m else ""


def email_livre(local, dominio):
    local, dominio = local.lower(), dominio.lower().rstrip(".")
    if dominio == "users.noreply.github.com" or dominio.endswith(".users.noreply.github.com"):
        return True
    if local in {"noreply", "no-reply", "nao-responda", "naoresponda", "donotreply", "do-not-reply"}:
        return True
    if f"{local}@{dominio}" in {"git@github.com", "git@gitlab.com", "git@bitbucket.org", "git@ssh.dev.azure.com"}:
        return True
    partes = dominio.split(".")
    if dominio in DOMINIOS_EXEMPLO or partes[-1] in EXTENSOES_ARQUIVO or re.match(r"^\d+(?:\.\d+)?x$", partes[0]):
        return True  # domínio de exemplo ou nome de arquivo (logo@2x.png)
    return partes[-1] in {"example", "test", "invalid", "localhost", "local"} or \
        any(p in {"example", "exemplo"} for p in partes[:-1])


def nome_generico(nome):
    n = dobrar(nome).casefold().strip()
    return not n or n[0] in "<$%{[*.~" or n in NOMES_GENERICOS


def segredo_de_exemplo(valor):
    corpo = PREFIXOS_SEGREDO.sub("", valor).replace("-", "").replace("_", "")
    return bool(re.fullmatch(r"(.)\1*", corpo)) or bool(re.search(r"(?i)example|exemplo|xxxx|placeholder", valor)) or \
        any(a in valor for a in ASSINATURAS_EXEMPLO)


def cpf_valido(d):
    if len(set(d)) == 1:
        return False
    n = [int(c) for c in d]
    for tam in (9, 10):
        s = sum(n[i] * (tam + 1 - i) for i in range(tam))
        if (s * 10 % 11) % 10 != n[tam]:
            return False
    return True


def cnpj_valido(d):
    if len(set(d)) == 1:
        return False
    n = [int(c) for c in d]
    pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    for tam, p in ((12, pesos), (13, [6] + pesos)):
        r = sum(n[i] * p[i] for i in range(tam)) % 11
        if (0 if r < 2 else 11 - r) != n[tam]:
            return False
    return True


def caminho_de_exemplo(caminho):
    n = str(caminho).strip().replace("\\", "/").rstrip("/").lower()
    return n in CAMINHOS_EXEMPLO


def nome_curto(caminho):
    """Forma curta 8.3 do Windows (C:\\Users\\<NOME>~1), comum em %TEMP%."""
    if os.name != "nt":
        return ""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        return buf.value if ctypes.windll.kernel32.GetShortPathNameW(str(caminho), buf, 1024) else ""
    except Exception:
        return ""


def variantes_caminho(caminho):
    s = str(caminho).strip().rstrip("\\/")
    if len(s) < 4 or caminho_de_exemplo(s):
        return set()
    v = {s, s.replace("\\", "/"), s.replace("/", "\\"), s.replace("\\", "\\\\")}
    m = re.match(r"^([A-Za-z]):[\\/]+(.*)$", s)
    if m:
        resto = m.group(2).replace("\\", "/")
        v |= {f"/{m.group(1).lower()}/{resto}", f"/mnt/{m.group(1).lower()}/{resto}"}
    return v


# ------------------------------------------------------------------ termos privados

def termos_privados():
    """Lista (rótulo, termo) com o que é pessoal nesta máquina. Nada disso fica gravado no repositório."""
    dono, repo = dono_do_repositorio()
    livres = {x.casefold() for x in (dono, repo) if x}
    emails = set()
    if usar_ambiente():
        emails = set(git("config", "--get-all", "user.email").split())
        emails |= {os.environ.get(k) or "" for k in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL", "EMAIL")}
        livres |= {usuario_noreply(e).casefold() for e in emails if usuario_noreply(e)}
    termos = []

    def add(rotulo, valor, minimo=3, filtrar=True):
        valor = (valor or "").strip()
        if len(valor) < minimo or valor.casefold() in livres or (filtrar and nome_generico(valor)):
            return
        termos.append((rotulo, valor))

    if usar_ambiente():
        try:
            usuario = getpass.getuser()
        except Exception:
            usuario = ""
        for n in {usuario, os.environ.get("USERNAME"), os.environ.get("USER"), os.environ.get("LOGNAME")}:
            add("nome de usuário do sistema", n)
        for pasta in {str(Path.home()), nome_curto(Path.home())}:
            for v in variantes_caminho(pasta):
                add("pasta pessoal", v, 6)
        curto = nome_curto(Path.home())
        if "~" in Path(curto).name:
            add("nome curto da pasta pessoal", Path(curto).name, 4)
        for h in {platform.node(), os.environ.get("COMPUTERNAME"), os.environ.get("HOSTNAME")}:
            add("nome do computador", h)
        for pasta in {str(RAIZ), nome_curto(RAIZ)}:
            for v in variantes_caminho(pasta):
                add("pasta local do repositório", v, 6)
        if not caminho_de_exemplo(RAIZ) and re.search(r"[A-Z0-9]", RAIZ.name[1:]):
            add("nome da pasta local do repositório", RAIZ.name, 6)  # só nomes próprios (MeuSistema2), não palavras
        for e in filter(None, emails):
            local, _, dominio = e.partition("@")
            if dominio and not email_livre(local, dominio):
                add("e-mail pessoal", e)
                if re.search(r"[\d._-]", local):
                    add("e-mail pessoal (parte antes do @)", local, 6)
        for nome in git("config", "--get-all", "user.name").splitlines():
            add("nome configurado no git", nome)

    freelancer = ler_json(RAIZ / "config" / "freelancer.json")
    if isinstance(freelancer, dict):
        for chave, valor in freelancer.items():
            if isinstance(valor, str) and chave != "moeda":
                add(f"dado pessoal de config/freelancer.json ({chave})", valor, 4)
    projetos = ler_json(RAIZ / "config" / "projetos.json")
    for p in projetos if isinstance(projetos, list) else []:
        if not isinstance(p, dict):
            continue
        caminho = str(p.get("caminho") or "")
        if not caminho or re.search(r"(?i)[\\/](?:temp|tmp)[\\/]", caminho):
            continue  # projetos de teste
        for v in variantes_caminho(caminho):
            add("pasta de projeto de cliente", v, 6)
        add("nome de projeto de cliente", str(p.get("nome") or ""), 4)
        add("nome de cliente", str(p.get("cliente") or ""), 4)

    arquivo = Path(os.environ.get("PRUMO_PRIVADO") or (Path.home() / ".prumo" / "privado.txt"))
    for linha in linhas(ler_texto(arquivo)):
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            add("termo de ~/.prumo/privado.txt", linha, 2, filtrar=False)
    return termos


def compilar(termos):
    """Cada termo vira uma regex sem diferenciar maiúsculas, com e sem acento; entre as palavras aceita espaço,
    quebra de linha, _, -, . ou nada (Ana Doces, Ana-Doces, ana_doces, AnaDoces)."""
    vistos, saida = set(), []
    for rotulo, termo in termos:
        for var in (unicodedata.normalize("NFC", termo), dobrar(termo)):
            chave = var.casefold()
            if chave in vistos:
                continue
            vistos.add(chave)
            rx = r"[\s_.\-]*".join(re.escape(p) for p in var.split())
            if re.match(r"\w", var):
                rx = r"(?<!\w)" + rx
            if re.search(r"\w$", var):
                rx += r"(?!\w)"
            saida.append((rotulo, re.compile(rx, re.I), len(var.split()) > 1))
    return saida


def variantes_escapadas(texto):
    """Versões do texto com escapes desfeitos: \\uXXXX/\\xXX (JSON), %XX (URL), &...; (HTML) e barras duplicadas."""
    vs = []
    if "\\u" in texto or "\\x" in texto:
        vs.append(re.sub(r"\\u([0-9a-fA-F]{4})|\\x([0-9a-fA-F]{2})",
                         lambda m: chr(int(m.group(1) or m.group(2), 16)), texto))
    if "%" in texto:
        vs.append(urllib.parse.unquote(texto))
    if "&" in texto:
        vs.append(html.unescape(texto))
    if "\\\\" in texto:
        vs.append(texto.replace("\\\\", "\\"))
    return [unicodedata.normalize("NFC", v) for v in dict.fromkeys(vs) if v != texto]


# ------------------------------------------------------------------ varredura

class Varredor:
    """Acumula achados: (onde, linha, regra, amostra, tipo); tipo = termo, generica, arquivo ou identidade."""

    def __init__(self, termos=None):
        self.termos = compilar(termos_privados() if termos is None else termos)
        self.achados = []
        self.problemas = []
        self._vistos = set()

    def _add(self, onde, linha, regra, amostra, tipo, mascarar=True):
        chave = (onde, linha, regra)
        if chave in self._vistos:
            return
        self._vistos.add(chave)
        amostra = amostra.strip()
        if mascarar and len(amostra) > 6:
            amostra = amostra[:4] + "…"
        self.achados.append((onde, linha, regra, amostra, tipo))

    def linha(self, onde, n, texto):
        texto = unicodedata.normalize("NFC", texto)
        for versao in [texto] + variantes_escapadas(texto):
            for rotulo, rx, _ in self.termos:  # literais: lineares, valem para a linha inteira
                m = rx.search(versao)
                if m:
                    self._add(onde, n, rotulo, m.group(0), "termo")
            if IGNORAR in texto:
                continue
            for ini in range(0, max(len(versao), 1), JANELA):  # regras genéricas em janelas (linhas enormes)
                self._genericas(onde, n, versao[max(0, ini - SOBREPOSICAO):ini + JANELA])

    def _genericas(self, onde, n, texto):
        for m in RX_EMAIL.finditer(texto):
            if not email_livre(m.group(1), m.group(2)):
                self._add(onde, n, "e-mail real (use voce@exemplo.com ou o noreply do GitHub)", m.group(0), "generica")
        for m in RX_PASTA_USUARIO.finditer(texto):
            if not nome_generico(m.group(1) or m.group(2) or m.group(3)):
                self._add(onde, n, "pasta de um usuário da máquina (use um caminho genérico)", m.group(0), "generica")
        for rotulo, rx in SEGREDOS:
            for m in rx.finditer(texto):
                if not segredo_de_exemplo(m.group(0)):
                    self._add(onde, n, rotulo, m.group(0), "generica")
                    break
        for m in RX_URL_SENHA.finditer(texto):
            usuario, senha = m.group(1), m.group(2)
            if not (RX_SENHA_EXEMPLO.match(senha) or senha == usuario):
                self._add(onde, n, "URL com usuário e senha", m.group(0), "generica")
        for m in RX_BASIC.finditer(texto):
            try:
                credencial = base64.b64decode(m.group(1) + "==", validate=False).decode("utf-8", "replace")
            except ValueError:
                continue
            usuario, dois_pontos, senha = credencial.partition(":")
            if dois_pontos and not (RX_SENHA_EXEMPLO.match(senha) or senha == usuario):
                self._add(onde, n, "credencial em Authorization: Basic", m.group(0), "generica")
        for m in RX_CPF.finditer(texto):
            d = "".join(m.groups())
            if d not in DOCUMENTOS_EXEMPLO and cpf_valido(d):
                self._add(onde, n, "CPF válido", m.group(0), "generica")
        for m in RX_CNPJ.finditer(texto):
            d = "".join(m.groups())
            if d not in DOCUMENTOS_EXEMPLO and cnpj_valido(d):
                self._add(onde, n, "CNPJ válido", m.group(0), "generica")

    def texto(self, onde, conteudo, inicio=1):
        conteudo = unicodedata.normalize("NFC", conteudo)
        for i, linha in enumerate(linhas(conteudo), inicio):
            self.linha(onde, i, linha)
        if "\n" in conteudo:  # termos de várias palavras quebrados entre linhas (parágrafos de Markdown)
            for rotulo, rx, varias in self.termos:
                if varias:
                    for m in rx.finditer(conteudo):
                        self._add(onde, conteudo.count("\n", 0, m.start()) + inicio, rotulo, m.group(0), "termo")

    def caminho(self, caminho, prefixo=""):
        rel = caminho.strip().replace("\\", "/")
        if not rel:
            return
        for rotulo, rx in CAMINHOS_PROIBIDOS:
            if rx.search(rel):
                self._add(prefixo + rel, 0, rotulo, rel, "arquivo", mascarar=False)
        self.linha(f"{prefixo}nome de arquivo", 0, rel)

    def identidade(self, onde, nome, email):
        local, _, dominio = (email or "").partition("@")
        if email and not (dominio and email_livre(local, dominio)):
            self._add(onde, 0, "e-mail do commit não é o noreply do GitHub", email, "identidade")
        if nome:
            antes = len(self.achados)
            self.linha(onde, 0, nome)
            self.achados[antes:] = [(o, l, r, a, "identidade") for o, l, r, a, _ in self.achados[antes:]]


def nomes_z(saida):
    return [n.strip("\n") for n in saida.split("\0") if n.strip("\n")]


def varrer_objetos(v, rotulos):
    """Varre o conteúdo de vários objetos do git ({especificação: rótulo}, ex. ':a.md' ou '<sha>:a.md') com dois
    processos só. Blobs repetidos são lidos uma vez."""
    if not rotulos:
        return
    specs = list(rotulos)
    checagem = git_ok("cat-file", "--batch-check=%(objectname) %(objecttype)",
                      entrada=("\n".join(specs) + "\n").encode()).split("\n")
    blobs = {}
    for spec, linha in zip(specs, checagem):
        partes = linha.split()
        if len(partes) == 2 and partes[1] == "blob":
            blobs.setdefault(partes[0], rotulos[spec])
    if not blobs:
        return
    lote = git_ok("cat-file", "--batch", entrada=("\n".join(blobs) + "\n").encode(), bruto=True)
    pos = 0
    while pos < len(lote):
        fim = lote.index(b"\n", pos)
        cab = lote[pos:fim].split()
        if len(cab) < 3:
            raise ErroGit("resposta inesperada do git cat-file --batch")
        tamanho = int(cab[2])
        dados = lote[fim + 1:fim + 1 + tamanho]
        pos = fim + 1 + tamanho + 1
        texto, binario = decodificar(dados)
        rotulo = blobs.get(cab[0].decode(), cab[0].decode())
        v.texto(rotulo + (" (binário, texto legível)" if binario else ""), texto)


def varrer_commits(v, shas):
    """Autor, committer, mensagem, nomes e conteúdo dos arquivos alterados de cada commit (merges contra todos os pais)."""
    if not shas:
        return
    entrada = ("\n".join(shas) + "\n").encode()
    meta = git_ok("log", "--no-walk=unsorted", "--stdin", "--format=%H%x00%an%x00%ae%x00%cn%x00%ce%x00%B%x1e",
                  entrada=entrada)
    for bloco in meta.split("\x1e"):
        partes = bloco.lstrip("\n").split("\0", 5)
        if len(partes) < 6:
            continue
        sha, an, ae, cn, ce, corpo = partes
        v.identidade(f"commit {sha[:8]} (autor)", an, ae)
        v.identidade(f"commit {sha[:8]} (committer)", cn, ce)
        v.texto(f"commit {sha[:8]} (mensagem)", corpo)
    conjunto, atual, rotulos = set(shas), None, {}
    saida = git_ok("diff-tree", "--stdin", "-r", "-z", "--name-only", "--no-renames", "--diff-filter=d", "--root",
                   "-m", entrada=entrada)
    for item in nomes_z(saida):
        if item in conjunto:
            atual = item
        elif atual:
            v.caminho(item, f"commit {atual[:8]}: ")
            rotulos[f"{atual}:{item}"] = f"commit {atual[:8]}: {item}"
    varrer_objetos(v, rotulos)


# ------------------------------------------------------------------ instalação dos hooks do git

STUB = """#!/bin/sh
# {marcador}: instalado por "python .githooks/privacidade.py instalar"; não edite (rode o instalador de novo).
raiz=$(git rev-parse --show-toplevel 2>/dev/null) || exit 1
script="$raiz/.githooks/privacidade.py"
if [ ! -f "$script" ]; then
  echo "privacidade: este checkout não tem .githooks/privacidade.py; por segurança o {hook} bloqueou." >&2
  echo "Volte para um branch que tenha o guarda (ou traga-o com um merge) antes de commitar ou publicar." >&2
  exit 1
fi
py='{python}'
if [ ! -f "$py" ]; then
  py=
  for c in python3 python py; do
    if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" </dev/null >/dev/null 2>&1; then py="$c"; break; fi
  done
  [ -n "$py" ] || {{ echo "privacidade: Python 3.9+ não encontrado; bloqueado." >&2; exit 1; }}
fi
exec "$py" "$script" {hook} "$@"
"""


def pasta_de_hooks():
    pasta = git_ok("rev-parse", "--git-path", "hooks").strip()
    return Path(pasta) if Path(pasta).is_absolute() else RAIZ / pasta


def hooks_ativos():
    try:
        pasta = pasta_de_hooks()
    except ErroGit:
        return False
    return all(MARCADOR in ler_texto(pasta / h) for h in HOOKS)


def modo_instalar():
    """Grava os hooks no diretório de hooks do repositório (compartilhado pelos worktrees). Eles chamam o
    .githooks/privacidade.py do checkout atual e bloqueiam se ele não existir: trocar para um branch sem o guarda
    não desliga nada em silêncio."""
    if git("config", "--get", "core.hooksPath").strip():
        git_ok("config", "--unset-all", "core.hooksPath")
        print("core.hooksPath removido (os hooks agora ficam no diretório de hooks do repositório).")
    comum = Path(git_ok("rev-parse", "--git-common-dir").strip())
    pasta = (comum if comum.is_absolute() else RAIZ / comum) / "hooks"
    pasta.mkdir(parents=True, exist_ok=True)
    python = Path(sys.executable).as_posix().replace("'", "")
    for hook in HOOKS:
        arquivo = pasta / hook
        if arquivo.exists() and MARCADOR not in ler_texto(arquivo):
            arquivo.replace(arquivo.with_name(hook + ".antes-do-prumo"))
            print(f"{hook}: o hook que existia foi guardado como {hook}.antes-do-prumo.")
        arquivo.write_bytes(STUB.format(marcador=MARCADOR, hook=hook, python=python).encode("utf-8"))
        arquivo.chmod(0o755)
    print(f"Hooks de privacidade instalados: {', '.join(HOOKS)}.")
    return 0


# ------------------------------------------------------------------ modos do git

def modo_pre_commit(v):
    for papel, rotulo in (("AUTHOR", "autor"), ("COMMITTER", "committer")):
        m = re.match(r"^(.*?) <([^>]*)>", git_ok("var", f"GIT_{papel}_IDENT").strip())
        if m:
            v.identidade(f"identidade do commit ({rotulo})", m.group(1), m.group(2))
    nomes = nomes_z(git_ok("diff", "--cached", "--name-only", "-z", "--no-renames", "--diff-filter=d"))
    for nome in nomes:
        v.caminho(nome)
    varrer_objetos(v, {f":{n}": n for n in nomes})
    return "o commit"


def modo_commit_msg(v, arquivo):
    texto = ler_texto(arquivo)
    corte = texto.find("# ------------------------ >8 ------------------------")
    if corte >= 0:
        texto = texto[:corte]
    # varre também as linhas com '#': com `git commit -m`, elas ficam na mensagem
    v.texto("mensagem do commit", texto)
    return "a mensagem do commit"


def modo_pre_push(v, entrada, remoto=""):
    """`remoto` é o nome que o git passa ao hook. Só os commits que esse remoto já tem ficam de fora: o que está
    em outro remoto (um backup privado, por exemplo) é conferido antes de ir para este."""
    nomeado = remoto in git("remote").split()
    for linha in linhas(entrada):
        partes = linha.split()
        if len(partes) < 4 or set(partes[1]) == {"0"}:
            continue
        ref, sha, sha_remoto = partes[0], partes[1], partes[3]
        if git_ok("cat-file", "-t", sha).strip() == "tag":
            conteudo = git_ok("cat-file", "-p", sha)
            m = re.search(r"^tagger (.*?) <([^>]*)>", conteudo, re.M)
            if m:
                v.identidade(f"tag {ref}", m.group(1), m.group(2))
            v.texto(f"tag {ref} (mensagem)", conteudo.split("\n\n", 1)[-1])
        alvo = git_ok("rev-parse", f"{sha}^{{}}").strip()
        tipo = git_ok("cat-file", "-t", alvo).strip()
        if tipo == "blob":
            varrer_objetos(v, {alvo: f"{ref} (blob)"})
            continue
        if tipo == "tree":
            arquivos = nomes_z(git_ok("ls-tree", "-r", "-z", "--name-only", alvo))
            for a in arquivos:
                v.caminho(a, f"{ref}: ")
            varrer_objetos(v, {f"{alvo}:{a}": f"{ref}: {a}" for a in arquivos})
            continue
        if set(sha_remoto) != {"0"} and _git(["cat-file", "-e", f"{sha_remoto}^{{commit}}"])[0] == 0:
            revs = git_ok("rev-list", alvo, f"^{sha_remoto}")
        elif nomeado:
            revs = git_ok("rev-list", alvo, "--not", f"--remotes={remoto}")
        else:
            revs = git_ok("rev-list", alvo)
        varrer_commits(v, revs.split())
    return "o push"


def modo_tudo(v, historico=False):
    # versionados e novos ainda não ignorados (candidatos ao próximo commit)
    arquivos = nomes_z(git_ok("ls-files", "-z", "--cached", "--others", "--exclude-standard"))
    if not arquivos:
        raise ErroGit("nenhum arquivo listado pelo git")
    for nome in arquivos:
        v.caminho(nome)
        try:
            dados = (RAIZ / nome).read_bytes()
        except OSError:
            continue
        texto, binario = decodificar(dados)
        v.texto(nome + (" (binário, texto legível)" if binario else ""), texto)
    if historico:
        varrer_commits(v, git_ok("rev-list", "--all").split())
        for linha in git_ok("for-each-ref", "refs/tags", "--format=%(objecttype) %(objectname) %(refname)").split("\n"):
            partes = linha.split(" ", 2)
            if len(partes) == 3 and partes[0] == "tag":
                conteudo = git_ok("cat-file", "-p", partes[1])
                m = re.search(r"^tagger (.*?) <([^>]*)>", conteudo, re.M)
                if m:
                    v.identidade(partes[2], m.group(1), m.group(2))
                v.texto(f"{partes[2]} (mensagem)", conteudo.split("\n\n", 1)[-1])
    return "o repositório" + (" (com o histórico)" if historico else ""), len(arquivos)


# ------------------------------------------------------------------ hook do Claude Code

RX_GIT = re.compile(
    r"(?<![\w./\\-])git(?:\.exe)?(?![\w.-])((?:\s+(?:-[cC]|--(?:git-dir|work-tree|namespace|super-prefix|config-env|"
    r"exec-path))(?:=|\s+)(?:\"[^\"]*\"|'[^']*'|\S+)|\s+--?[\w-]+(?:=\S+)?)*)(?:\s+([\w-]+))?")
RX_GH = re.compile(r"(?<![\w./\\-])gh(?:\.exe)?\s+(pr|issue|release|gist|repo|api)\b(?:\s+(\w[\w-]*))?")
RX_GH_BRUTO = re.compile(r"(?i)\bgh(?:\.exe)?['\"]?\s+(?:pr|issue|release|gist|repo|api)\b")
RX_SEPARADOR = re.compile(r"&&|\|\||[;|\n]")
RX_CD = re.compile(r"(?:^|&&|\|\||[;|\n(])\s*(?:cd|Set-Location|sl|pushd|Push-Location|chdir)\s+"
                   r"(?:-LiteralPath\s+|-Path\s+)?(\"[^\"]*\"|'[^']*'|[^\s;&|)]+)", re.I)
RX_INCERTO = re.compile(r"\(|\bpopd\b|\bPop-Location\b|\bcd\s+-(?=\s|$|;|&)|\bcd\s*(?=$|[;&|\n])|OLDPWD", re.I)
RX_NO_VERIFY = re.compile(r"(?<![\w-])--no-ve(?:r(?:i(?:fy?)?)?)?(?![\w-])")
RX_PUBLICA_GIT = re.compile(r"\b(?:commit|push|merge|rebase|cherry-pick|am|revert|pull)\b")
RX_CONFIG_PERIGOSA = re.compile(r"(?i)(?:(?<![\w-])-c\s*|--config-env[=\s]+)[\"']?(?:core\.hookspath|alias\.)")
RX_ENV_PERIGOSA = re.compile(
    r"(?i)(?:\$env:|(?<![\w$]))(?:GIT_CONFIG_(?:COUNT|PARAMETERS|KEY_\d+|VALUE_\d+)|PRUMO_PRIVACIDADE_AMBIENTE|"
    r"PRUMO_PRIVADO|GITHUB_ACTIONS)\s*=")
RX_PASTA_HOOKS = re.compile(r"(?i)\.git[\\/]+(?:[^\s\"']*[\\/]+)?hooks\b|--git-path\s+hooks")
RX_ANINHADO = re.compile(
    r"(?i)\b(bash|sh|zsh|dash|pwsh|powershell|cmd)(?:\.exe)?\s+(?:-\w+\s+)*?(?:-c|-Command|/c|/k)\s+"
    r"(\"(?:[^\"\\`]|\\.|`.)*\"|'(?:[^']|'')*')")
RX_HEREDOC = re.compile(r"(?<!<)<<-?[ \t]*(['\"]?)([A-Za-z_][\w-]*)\1[^\n]*\n(.*?)(?:\n[ \t]*\2[ \t]*(?=\n|$|\))|$)",
                        re.S)
RX_HERESTRING = re.compile(r"@(['\"])[ \t]*\r?\n(.*?)\r?\n\1@", re.S)
RX_ASPAS = {"Bash": re.compile(r"\"(?:[^\"\\]|\\.)*\"|'[^']*'", re.S),
            "PowerShell": re.compile(r"\"(?:[^\"`]|`.)*\"|'(?:[^']|'')*'", re.S)}
RX_ASPAS_SIMPLES = {"Bash": re.compile(r"'[^']*'"), "PowerShell": re.compile(r"'(?:[^']|'')*'")}
RX_SUBSTITUICAO = re.compile(r"\$\(\s*(?:cat|Get-Content|gc|type)\b([^)<]*)\)|\$\(\s*<\s*([^)]*)\)", re.I)
RX_SUBST_HEREDOC = re.compile(r"\$\(\s*cat\s+<<", re.I)
RX_VARIAVEL = {"Bash": re.compile(r"\$[\w({]|`"), "PowerShell": re.compile(r"\$[\w({]")}
RX_API_ESCRITA = re.compile(r"(?:^|/)repos/([^/\s]+)/([^/\s]+)/(?:contents|import|git/(?:blobs|trees|commits|refs|tags))")
FLAGS_ARQUIVO_GH = {"--body-file", "-F", "--notes-file", "--input", "--template"}
FLAGS_BOOLEANAS_GH = {"--draft", "-d", "--prerelease", "-p", "--latest", "--generate-notes", "--verify-tag",
                      "--fail-on-no-commits", "--clobber", "--public", "--web", "-w", "--fill", "--fill-first",
                      "--fill-verbose", "--no-maintainer-edit", "--dry-run"}


def juntar_continuacoes(cmd, ferramenta):
    return re.sub(r"`\r?\n" if ferramenta == "PowerShell" else r"\\\r?\n", " ", cmd)


def mascarar_dados(cmd, ferramenta="Bash"):
    """O comando com o mesmo tamanho, mas com heredocs e textos entre aspas tapados: são dados, não comandos.
    Assim `git`/`gh` citados num texto não contam como execução, e separadores dentro de aspas não cortam o comando."""
    s = list(cmd)

    def tapar(ini, fim):
        for i in range(ini, fim):
            s[i] = "_"

    for m in RX_HEREDOC.finditer(cmd):
        tapar(m.start(3), m.end(3))
    for m in RX_HERESTRING.finditer(cmd):
        tapar(m.start(2), m.end(2))
    parcial = "".join(s)
    for m in RX_ASPAS.get(ferramenta, RX_ASPAS["Bash"]).finditer(parcial):
        tapar(m.start() + 1, m.end() - 1)
    return "".join(s)


def _caminho_local(texto, base):
    texto = texto.strip().strip("\"'")
    m = re.match(r"^/(?:mnt/)?([a-zA-Z])(/.*)?$", texto)
    if m and os.name == "nt":
        texto = f"{m.group(1)}:{m.group(2) or '/'}"
    texto = os.path.expandvars(os.path.expanduser(texto))
    p = Path(texto)
    return p if p.is_absolute() else Path(base) / p


def _dentro_do_repositorio(pasta):
    try:
        Path(pasta).resolve().relative_to(RAIZ.resolve())
        return True
    except (ValueError, OSError):
        return False


def _no_repositorio(cmd, mascara, inicio, globais, cwd):
    """O comando que começa em `inicio` age neste repositório? Na dúvida (subshell, popd, cd -, pasta que não existe
    ou variável), responde que sim."""
    antes = mascara[:inicio]
    if RX_INCERTO.search(antes):
        return True
    pasta = Path(cwd)
    for m in RX_CD.finditer(antes):
        pasta = _caminho_local(cmd[m.start(1):m.end(1)], pasta)
        if "$" in str(pasta) or "%" in str(pasta) or not pasta.is_dir():
            return True
    for m in re.finditer(r"-C\s+(\"[^\"]*\"|'[^']*'|\S+)", globais or ""):
        pasta = _caminho_local(m.group(1), pasta)
        if "$" in str(pasta) or "%" in str(pasta) or not pasta.is_dir():
            return True
    return _dentro_do_repositorio(pasta)


def _segmento(cmd, mascara, inicio):
    """Trecho do comando até o próximo separador (&&, ;, | ...) fora de aspas e heredocs: (início, fim)."""
    m = RX_SEPARADOR.search(mascara, inicio)
    return inicio, (m.start() if m else len(cmd))


def _tokens(texto):
    try:
        return shlex.split(texto, posix=True)
    except ValueError:
        return texto.split()


def _pula_hooks_commit(trecho):
    """`git commit -n` (ou -an, -nm...) pula os hooks."""
    pular = False
    for t in _tokens(trecho)[1:]:
        if pular:
            pular = False
            continue
        if t == "--":
            break
        if re.match(r"^-[A-Za-z]+$", t):
            for i, c in enumerate(t[1:]):
                if c == "n":
                    return True
                if c in "mFcCtS":
                    pular = i == len(t) - 2
                    break
    return False


def _mexe_em_hooks(segmento):
    """`git config ...` que muda, remove, renomeia ou edita core.hooksPath (o instalador cuida disso)."""
    baixo = [t.lower() for t in _tokens(segmento)]
    if {"-e", "--edit", "edit"} & set(baixo[2:]):
        return True
    if "core" in baixo and {"--rename-section", "--remove-section", "rename-section", "remove-section"} & set(baixo):
        return True
    for i, t in enumerate(baixo):
        if t == "core.hookspath":
            antes = set(baixo[:i])
            if antes & {"--get", "--get-all", "--get-regexp", "get", "--show-origin", "--show-scope"}:
                return False
            return i + 1 < len(baixo) or bool(antes & {"--unset", "--unset-all", "unset"})
    return False


def checar_git(cmd, mascara, cwd, problemas):
    invocacoes = [m for m in RX_GIT.finditer(mascara)]
    alvos = [_no_repositorio(cmd, mascara, m.start(), cmd[m.start(1):m.end(1)], cwd) for m in invocacoes]
    visivel = bool(invocacoes)
    aplica = any(alvos) if visivel else \
        bool(re.search(r"(?i)\bgit(?:\.exe)?\b", cmd)) and _dentro_do_repositorio(cwd)  # git escondido ("git", caminho)
    if not aplica:
        return
    publica = RX_PUBLICA_GIT.search(cmd)
    if publica and RX_NO_VERIFY.search(cmd):
        problemas.append("não pule os hooks de privacidade (--no-verify); corrija o que eles apontarem. "
                         "Se só estiver citando a opção num texto, grave o texto com a ferramenta de arquivos.")
    if RX_CONFIG_PERIGOSA.search(cmd):
        problemas.append("não troque core.hooksPath nem crie alias do git pela linha de comando (-c/--config-env).")
    if publica and RX_ENV_PERIGOSA.search(cmd):
        problemas.append("não mexa nas variáveis que desligam o guarda (GIT_CONFIG_*, PRUMO_PRIVACIDADE_AMBIENTE, "
                         "PRUMO_PRIVADO, GITHUB_ACTIONS) num comando que commita ou publica.")
    if RX_PASTA_HOOKS.search(cmd) and not re.search(r"privacidade\.py['\"]?\s+instalar", cmd):
        problemas.append("não mexa nos hooks instalados em .git/hooks; para reinstalar: "
                         "python .githooks/privacidade.py instalar")
    if publica and not visivel and not hooks_ativos():
        problemas.append("os hooks de privacidade não estão instalados neste clone. Rode antes: "
                         "python .githooks/privacidade.py instalar")
    for m, dentro in zip(invocacoes, alvos):
        if not dentro:
            continue
        sub = (m.group(2) or "").lower()
        _, fim = _segmento(cmd, mascara, m.start())
        if sub == "config" and _mexe_em_hooks(cmd[m.start():fim]):
            problemas.append("não mude core.hooksPath: os hooks de privacidade ficam no diretório de hooks do "
                             "repositório (python .githooks/privacidade.py instalar).")
        if sub == "commit" and _pula_hooks_commit(cmd[m.start(2):fim]):
            problemas.append("não pule os hooks de privacidade (git commit -n); corrija o que eles apontarem.")
        if sub in ("commit", "push", "merge", "rebase", "cherry-pick", "am", "revert", "pull") and not hooks_ativos():
            problemas.append("os hooks de privacidade não estão instalados neste clone. Rode antes: "
                             "python .githooks/privacidade.py instalar")


def _mesmo_repositorio(valor):
    dono, nome = dono_do_repositorio()
    if not dono:
        return True
    partes = re.sub(r"\.git$", "", valor.strip("\"'").rstrip("/")).split("/")  # dono/repo ou host/dono/repo
    return "/".join(partes[-2:]).lower() == f"{dono}/{nome}".lower()


def _sem_dados_conferiveis(segmento, ferramenta):
    """O segmento sem o que já é conferido (aspas simples, heredocs, $(cat arquivo), $(cat <<EOF)): se sobrar
    variável ou substituição de comando, o texto final não dá para conferir."""
    texto = RX_HEREDOC.sub(lambda m: m.group(0)[:m.start(3) - m.start()], segmento)
    texto = RX_ASPAS_SIMPLES.get(ferramenta, RX_ASPAS_SIMPLES["Bash"]).sub("''", texto)
    texto = RX_SUBST_HEREDOC.sub("", RX_SUBSTITUICAO.sub("", texto))
    return RX_VARIAVEL.get(ferramenta, RX_VARIAVEL["Bash"]).search(texto) is not None


def checar_gh(cmd, mascara, cwd, problemas, ferramenta="Bash"):
    """Varre só o que o gh vai publicar: argumentos do próprio comando, heredocs dele e arquivos citados."""
    textos, arquivos, nomes = [], [], []
    for m in RX_GH.finditer(mascara):
        grupo, acao = m.group(1), (m.group(2) or "")
        publica = grupo == "api" or (grupo in {"gist", "repo"} and acao in {"create", "edit"}) or \
            (grupo == "release" and acao in {"create", "edit", "upload"}) or \
            acao in {"create", "edit", "comment", "review", "close", "reopen", "merge"}
        if not publica:
            continue
        ini, fim = _segmento(cmd, mascara, m.start())
        segmento = cmd[ini:fim]
        tokens = _tokens(segmento)
        repo = next((tokens[i + 1] for i, t in enumerate(tokens[:-1]) if t in ("--repo", "-R")), None) or \
            next((t.split("=", 1)[1] for t in tokens if t.startswith("--repo=")), None)
        if grupo == "api":
            escrita = next((e for e in (RX_API_ESCRITA.search(t) for t in tokens[2:] if not t.startswith("-")) if e),
                           None)
            if escrita:
                repo = f"{escrita.group(1)}/{escrita.group(2)}"
                metodo = next((tokens[i + 1] for i, t in enumerate(tokens[:-1]) if t in ("-X", "--method")), "")
                campos = any(t in ("-f", "-F", "--field", "--raw-field", "--input") or
                             t.startswith(("--field=", "--raw-field=", "--input=")) for t in tokens)
                if _mesmo_repositorio(repo) and (campos or metodo.upper() not in ("", "GET")):
                    problemas.append("gravar no repositório pela API do GitHub pula os hooks do git; "
                                     "use git commit e git push.")
        if repo and not _mesmo_repositorio(repo):
            continue
        if not repo and not _no_repositorio(cmd, mascara, m.start(), "", cwd):
            continue
        base = Path(cwd)
        for c in RX_CD.finditer(mascara[:m.start()]):
            base = _caminho_local(cmd[c.start(1):c.end(1)], base)
        heredocs = [h.group(3) for h in RX_HEREDOC.finditer(cmd) if ini <= h.start() < fim] + \
                   [h.group(2) for h in RX_HERESTRING.finditer(cmd) if ini <= h.start() < fim]
        textos += heredocs
        if _sem_dados_conferiveis(segmento, ferramenta):
            problemas.append("o texto vem de variável ou de comando ($...) e não dá para conferir; grave-o num arquivo "
                             "e passe o arquivo (--body-file, --notes-file, -F campo=@arquivo).")
        for s in RX_SUBSTITUICAO.finditer(segmento):
            for t in _tokens(s.group(1) or s.group(2) or ""):
                if not t.startswith("-"):
                    arquivos.append(_caminho_local(t, base))
        stdin = "o texto vem da entrada padrão e não dá para conferir; grave-o num arquivo e passe o arquivo."
        publicos, posicionais, i = [], 0, 0
        while i < len(tokens):
            t = tokens[i]
            prox = tokens[i + 1] if i + 1 < len(tokens) else ""
            nome_flag, igual, valor = t.partition("=")
            if t.startswith("-") and len(t) > 1:
                if grupo == "api" and nome_flag in ("-F", "-f", "--field", "--raw-field"):
                    if not igual:
                        valor, i = prox, i + 1
                    conteudo = valor.partition("=")[2]
                    if conteudo == "@-":
                        if not heredocs:
                            problemas.append(stdin)
                    elif conteudo.startswith("@"):
                        arquivos.append(_caminho_local(conteudo[1:], base))
                    publicos.append(valor)
                elif nome_flag in FLAGS_ARQUIVO_GH:
                    if not igual:
                        valor, i = prox, i + 1
                    if valor == "-":
                        if not heredocs:
                            problemas.append(stdin)
                    elif valor:
                        arquivos.append(_caminho_local(valor, base))
                elif igual or nome_flag in FLAGS_BOOLEANAS_GH or not prox or prox.startswith("-"):
                    publicos.append(t)
                else:  # opção com valor separado: --title "x", --body 'y'
                    publicos += [t, prox]
                    i += 1
            else:
                posicionais += 1
                # gh release create|upload <tag> <arquivos...> / gh gist create <arquivos...>
                if (grupo == "release" and acao in {"create", "upload"} and posicionais > 4) or \
                        (grupo == "gist" and acao == "create" and posicionais > 3):
                    padrao = t.split("#", 1)[0]
                    achados = sorted(glob.glob(str(_caminho_local(padrao, base)))) if glob.has_magic(padrao) else \
                        [str(_caminho_local(padrao, base))]
                    if not achados:
                        problemas.append(f"anexo {padrao} não encontrado; não dá para conferir.")
                    for a in achados:
                        nomes.append(Path(a).name if glob.has_magic(padrao) else padrao)
                        arquivos.append(Path(a))
                else:
                    publicos.append(t)
            i += 1
        textos.append(" ".join(publicos))
    if not textos and not arquivos:
        return []
    v = Varredor()
    for texto in textos:
        v.texto("texto a publicar no GitHub", texto)
    for nome in nomes:
        v.caminho(nome, "anexo: ")
    for caminho in arquivos:
        try:
            dados = Path(caminho).read_bytes()
        except OSError:
            problemas.append(f"não consegui ler {Path(caminho).name} para conferir; por segurança, bloqueado.")
            continue
        texto, _ = decodificar(dados)
        v.texto(f"arquivo {Path(caminho).name}", texto)
    return v.achados


def analisar_comando(cmd, ferramenta, cwd, problemas, achados, profundidade=0):
    cmd = juntar_continuacoes(cmd, ferramenta)
    mascara = mascarar_dados(cmd, ferramenta)
    checar_git(cmd, mascara, cwd, problemas)
    achados += checar_gh(cmd, mascara, cwd, problemas, ferramenta)
    if profundidade < 2:  # bash -c "...", powershell -Command "...", cmd /c "..."
        for m in RX_ANINHADO.finditer(cmd):
            interno = m.group(2)[1:-1]
            if m.group(2).startswith('"'):
                interno = re.sub(r'\\(["\\$`])|`(["`$])', lambda x: x.group(1) or x.group(2), interno)
            else:
                interno = interno.replace("''", "'")
            if re.search(r"(?i)\b(?:git|gh)(?:\.exe)?\b", interno):
                sub = "PowerShell" if m.group(1).lower() in ("pwsh", "powershell") else "Bash"
                analisar_comando(interno, sub, cwd, problemas, achados, profundidade + 1)
    if RX_GH_BRUTO.search(cmd) and not RX_GH.search(mascara) and not RX_ANINHADO.search(cmd) and \
            _dentro_do_repositorio(cwd):
        problemas.append("gh escondido entre aspas ou por um caminho não dá para conferir; chame o gh diretamente.")


def modo_claude(bruto):
    try:
        dados = json.loads(bruto.decode("utf-8", "replace") or "{}")
    except ValueError:
        return 0
    ferramenta = dados.get("tool_name")
    if ferramenta not in ("Bash", "PowerShell"):
        return 0
    cmd = str((dados.get("tool_input") or {}).get("command") or "")
    if not re.search(r"(?i)\b(?:git|gh)(?:\.exe)?\b|\.git[\\/]", cmd):
        return 0
    problemas, achados = [], []
    analisar_comando(cmd, ferramenta, dados.get("cwd") or os.getcwd(), problemas, achados)
    if not problemas and not achados:
        return 0
    for p in dict.fromkeys(problemas):
        print(f"Privacidade (repositório público): {p}", file=sys.stderr)
    relatar(achados, "o texto que vai para o GitHub")
    return 2


# ------------------------------------------------------------------ saída

def relatar(achados, contexto):
    if not achados:
        return
    err = sys.stderr
    print(f"Privacidade: {contexto} contém dados que não podem ir para o GitHub (o repositório é público).", file=err)
    for onde, linha, regra, amostra, _ in achados[:MAX_RELATO]:
        local = f"{onde}:{linha}" if linha else onde
        print(f"  {local}  {regra}: {amostra}", file=err)
    if len(achados) > MAX_RELATO:
        print(f"  … e mais {len(achados) - MAX_RELATO} achado(s).", file=err)
    tipos = {a[4] for a in achados}
    if tipos & {"termo", "generica"}:
        print("Troque esses dados por exemplos genéricos (C:\\Prumo, voce@exemplo.com, Loja da Ana) e tente de novo.",
              file=err)
    if "arquivo" in tipos:
        print("Arquivos proibidos: tire-os do commit (git rm --cached <arquivo>) e acrescente-os ao .gitignore.", file=err)
    if "identidade" in tipos:
        print("Identidade: use o login do GitHub e o e-mail noreply neste clone:\n"
              "  git config user.name \"<login>\"\n"
              "  git config user.email \"<id>+<login>@users.noreply.github.com\"\n"
              "e refaça o commit (git commit --amend --reset-author --no-edit).", file=err)
    if "generica" in tipos:
        print('Falso positivo de regra genérica: acrescente "privacidade:ignorar" na linha.', file=err)


def main(argv):
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    modo = argv[1] if len(argv) > 1 else "tudo"
    if modo == "claude":
        try:
            return modo_claude(sys.stdin.buffer.read())
        except Exception as e:  # o hook nunca derruba a sessão; os hooks do git continuam valendo
            print(f"privacidade: erro no hook do Claude ({e}); os hooks do git seguem ativos.", file=sys.stderr)
            return 0
    if sys.version_info < (3, 9):
        print("privacidade: é preciso Python 3.9 ou superior.", file=sys.stderr)
        return 1
    if modo in HOOKS and os.environ.get("PRUMO_PRIVACIDADE_AMBIENTE", "").strip() == "0" and \
            os.environ.get("GITHUB_ACTIONS", "").strip().lower() != "true":
        print("privacidade: aviso — termos desta máquina desligados (PRUMO_PRIVACIDADE_AMBIENTE=0).", file=sys.stderr)
    total = None
    try:
        if modo == "instalar":
            return modo_instalar()
        v = Varredor()
        if modo == "pre-commit":
            contexto = modo_pre_commit(v)
        elif modo == "commit-msg" and len(argv) > 2:
            contexto = modo_commit_msg(v, argv[2])
        elif modo == "pre-push":
            contexto = modo_pre_push(v, sys.stdin.buffer.read().decode("utf-8", "replace"),
                                     argv[2] if len(argv) > 2 else "")
        elif modo == "tudo":
            contexto, total = modo_tudo(v, "--historico" in argv)
        elif modo == "texto":
            v.texto("entrada", decodificar(sys.stdin.buffer.read())[0])
            contexto = "o texto"
        else:
            print(__doc__, file=sys.stderr)
            return 1
    except ErroGit as e:
        print(f"Privacidade: não consegui conferir ({e}). Por segurança, bloqueado.", file=sys.stderr)
        return 1
    if v.achados:
        relatar(v.achados, contexto)
        return 1
    if total is not None:
        print(f"Privacidade: {contexto} está limpo ({total} arquivos versionados ou novos).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
