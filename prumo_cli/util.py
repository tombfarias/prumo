"""Utilitários gerais: caminhos do kit, saída no console, modelos e JSON."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

VERSAO = "0.1.0"
URL_PRUMO = "https://github.com/tombfarias/prumo"
CONGELADO = bool(getattr(sys, "frozen", False))  # executável gerado pelo PyInstaller
if CONGELADO:
    RAIZ_KIT = Path(sys.executable).resolve().parent          # onde fica o prumo.exe (config gravável)
    RECURSOS = Path(getattr(sys, "_MEIPASS", RAIZ_KIT))      # templates e interface embutidos
else:
    RAIZ_KIT = Path(__file__).resolve().parent.parent
    RECURSOS = RAIZ_KIT
TEMPLATES = RECURSOS / "templates"
TEMPLATES_EN = TEMPLATES / "en"  # mesmos caminhos de templates/, em inglês
ARQUIVO_PROJETO = "projeto.prumo.json"
MARCADOR_LACUNA = "[PREENCHER"
LACUNA_EN = "[FILL"  # marcador dos modelos em inglês (templates/en)
LACUNA = re.compile(r"\[(?:PREENCHER|FILL)\b")


def tem_lacuna(texto):
    return bool(LACUNA.search(texto or ""))


def marcador_lacuna(idioma=None):
    """Marcador de lacuna do idioma do projeto: [PREENCHER ou [FILL."""
    return LACUNA_EN if str(idioma or "").lower().startswith("en") else MARCADOR_LACUNA


def modelo(rel, idioma=None):
    """Caminho de um modelo em templates/: a versão em inglês (templates/en/<rel>) se o projeto for em inglês e ela existir."""
    if str(idioma or "").lower().startswith("en") and (TEMPLATES_EN / rel).exists():
        return TEMPLATES_EN / rel
    return TEMPLATES / rel


class ErroPrumo(Exception):
    """Erro esperado, mostrado ao usuário sem traceback."""


def configurar_console():
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _t(msg):
    from .i18n import traduzir
    return traduzir(str(msg))


def info(msg=""):
    print(_t(msg))


def aviso(msg):
    print(_t(f"aviso: {msg}"), file=sys.stderr)


def progresso(msg):
    print(_t(msg), file=sys.stderr, flush=True)


def ler(caminho):
    return Path(caminho).read_text(encoding="utf-8-sig")


def gravar(caminho, texto):
    """Grava de forma atômica (arquivo temporário + troca): uma interrupção nunca deixa o arquivo pela metade."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temp = caminho.with_name(f".{caminho.name}.{os.getpid()}.tmp")
    try:
        with open(temp, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.replace(temp, caminho)
        except PermissionError:  # Windows: destino aberto em outro programa (antivírus, editor)
            with open(caminho, "w", encoding="utf-8", newline="\n") as f:
                f.write(texto)
    finally:
        if temp.exists():
            try:
                temp.unlink()
            except OSError:
                pass


def guardar_copia(raiz, rel, pasta):
    """Copia raiz/rel para raiz/.prumo/<pasta>/rel antes de sobrescrever; devolve o caminho relativo da cópia."""
    origem = Path(raiz) / rel
    destino = Path(raiz) / ".prumo" / pasta / rel
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)
    return destino.relative_to(raiz).as_posix()


def carimbo():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ler_json(caminho, padrao=None):
    try:
        return json.loads(ler(caminho))
    except FileNotFoundError:
        return padrao
    except json.JSONDecodeError as e:
        raise ErroPrumo(f"JSON inválido em {caminho}: {e}") from e


def gravar_json(caminho, dados):
    gravar(caminho, json.dumps(dados, ensure_ascii=False, indent=2) + "\n")


_CHAVE = re.compile(r"\{\{(\w+)\}\}")


def renderizar(texto, contexto):
    """Substitui {{chave}} pelos valores do contexto; chaves desconhecidas ficam como estão."""
    return _CHAVE.sub(lambda m: str(contexto[m.group(1)]) if m.group(1) in contexto else m.group(0), texto)


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "projeto"


def hoje_br():
    return date.today().strftime("%d/%m/%Y")


def agora_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def hash_conteudo(caminho):
    """SHA-256 do texto com quebras de linha normalizadas (imune a CRLF/LF do git no Windows)."""
    texto = Path(caminho).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(texto).hexdigest()


def hash_texto(texto):
    return hashlib.sha256(texto.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def sem_comentarios(texto):
    """Remove comentários HTML preservando a contagem de linhas."""
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), texto, flags=re.S)


def contar_lacunas(texto):
    return len(LACUNA.findall(sem_comentarios(texto)))


def comando_python():
    """Comando para chamar o Python nos hooks e nas instruções (python, python3 ou py)."""
    if os.name == "nt":
        return "python" if shutil.which("python") else ("py" if shutil.which("py") else "python")
    return "python3" if shutil.which("python3") else "python"


def python_disponivel():
    return any(shutil.which(c) for c in ("python", "python3", "py"))


def executavel_console():
    """No executável, o prumo.exe (console) ao lado; serve também quando quem roda é o prumo-app.exe (janela)."""
    vizinho = Path(sys.executable).resolve().with_name("prumo.exe")
    return vizinho if vizinho.exists() else Path(sys.executable).resolve()


def comando_prumo(python=None):
    """Como chamar o Prumo em instruções e hooks: o .exe, se for o executável, ou o Python com prumo.py."""
    if CONGELADO:
        return f'"{executavel_console().as_posix()}"'
    return f'{python or comando_python()} "{RAIZ_KIT.as_posix()}/prumo.py"'


def config_freelancer():
    padrao = ler_json(RECURSOS / "config" / "freelancer.exemplo.json", {}) or {}
    pessoal = ler_json(RAIZ_KIT / "config" / "freelancer.json", {}) or {}
    padrao.update({k: v for k, v in pessoal.items() if v not in (None, "")})
    return padrao


def git_usuario():
    try:
        r = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return ""


def formatar_moeda(valor, moeda="BRL"):
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}" if moeda == "BRL" else f"{moeda} {texto}"


def formatar_horas(horas):
    texto = f"{horas:.1f}".replace(".", ",")
    return texto[:-2] + "h" if texto.endswith(",0") else texto + "h"


def tabela_markdown(cabecalho, linhas):
    saida = ["| " + " | ".join(cabecalho) + " |", "|" + "|".join("---" for _ in cabecalho) + "|"]
    for linha in linhas:
        saida.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in linha) + " |")
    return "\n".join(saida)


def tabela_console(cabecalho, linhas):
    cabecalho = [_t(h) for h in cabecalho]
    linhas = [[str(c) for c in l] for l in linhas]
    larguras = [max(len(str(h)), *(len(l[i]) for l in linhas)) if linhas else len(str(h)) for i, h in enumerate(cabecalho)]
    fmt = "  ".join("{:<%d}" % w for w in larguras)
    saida = [fmt.format(*cabecalho), fmt.format(*("-" * w for w in larguras))]
    saida += [fmt.format(*l) for l in linhas]
    return "\n".join(saida)
