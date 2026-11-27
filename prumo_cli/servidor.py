"""Servidor local mínimo da interface gráfica.

A interface (prumo_cli/gui/index.html) é HTML/CSS/JS puro; este servidor só entrega a página e
traduz chamadas da interface em comandos do Prumo (`prumo --json ...`), executados em subprocesso.
Escuta apenas em 127.0.0.1 e exige um token aleatório em toda chamada.
"""

import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import i18n
from .util import CONGELADO, RAIZ_KIT, VERSAO, config_freelancer, executavel_console, progresso

PAGINA = Path(__file__).resolve().parent / "gui" / "index.html"
PERMITIDOS = {"perfis", "projetos", "novo", "mapear", "ferramentas", "status", "validar", "rastreabilidade", "contexto", "aprovar",
              "desaprovar", "adr", "mudanca", "doc", "agentes", "orcamento", "horas", "seguranca", "diagramas",
              "figma", "versao", "config", "formulario", "gerar"}
LIMITE_CORPO = 2_000_000  # bytes aceitos no corpo de um POST
DESCARTE_MAXIMO = 16_000_000  # acima disso a conexão fecha sem ler o resto
EXT_LEITURA = {".md", ".json", ".txt", ".mmd", ".log", ".py"}


def comando_base():
    if CONGELADO:
        return [str(executavel_console())]
    return [sys.executable, str(RAIZ_KIT / "prumo.py")]


def _env():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _flags_sem_janela():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}


def _flags_tarefa():
    if os.name == "nt":
        return _flags_sem_janela()
    return {"start_new_session": True}  # grupo próprio: parar encerra também os filhos


class Tarefa:
    def __init__(self, args, cwd):
        self.linhas = []
        self.fim = False
        self.codigo = None
        self.inicio = time.time()
        self.proc = subprocess.Popen(comando_base() + args, cwd=cwd, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=_env(), **_flags_tarefa())
        threading.Thread(target=self._ler, daemon=True).start()

    def _ler(self):
        with self.proc:  # fecha o pipe e espera o processo
            for bruto in self.proc.stdout:
                self.linhas.append(bruto.decode("utf-8", "replace").rstrip("\r\n"))
        self.codigo = self.proc.returncode
        self.fim = True

    def parar(self):
        """Encerra o Prumo e o Claude Code que ele abriu (no Windows, terminate() deixaria o Claude órfão)."""
        from .claude import encerrar_arvore
        encerrar_arvore(self.proc)


class Estado:
    def __init__(self, projeto_inicial=None):
        self.token = secrets.token_urlsafe(18)
        self.tarefas = {}
        self.ultimo_ping = time.time()
        self.projeto_inicial = projeto_inicial


def criar_handler(estado):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"Prumo/{VERSAO}"

        def log_message(self, *a):  # silencioso
            pass

        def _responder(self, status, corpo, tipo="application/json; charset=utf-8"):
            dados = corpo if isinstance(corpo, bytes) else json.dumps(corpo, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(dados)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(dados)

        def _autorizado(self):
            return secrets.compare_digest(self.headers.get("X-Prumo-Token", ""), estado.token)

        def _ler_corpo(self):
            """Corpo bruto da requisição, ou None se passar de LIMITE_CORPO.

            Um corpo grande demais é lido e descartado (até DESCARTE_MAXIMO) para a resposta
            chegar ao cliente: no Windows, fechar o socket com dados pendentes envia RST."""
            try:
                tamanho = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                tamanho = 0
            if tamanho <= 0:  # negativo faria read(-1) esperar o fim da conexão
                return b""
            if tamanho <= LIMITE_CORPO:
                return self.rfile.read(tamanho)
            restante = min(tamanho, DESCARTE_MAXIMO)
            while restante > 0:
                bloco = self.rfile.read(min(65536, restante))
                if not bloco:
                    break
                restante -= len(bloco)
            self.close_connection = True
            return None

        @staticmethod
        def _json(bruto):
            try:
                return json.loads(bruto.decode("utf-8") or "{}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {}

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/":
                if not secrets.compare_digest((parse_qs(url.query).get("t") or [""])[0], estado.token):
                    return self._responder(HTTPStatus.FORBIDDEN, b"Acesso negado.", "text/plain; charset=utf-8")
                html = PAGINA.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Security-Policy",
                                 "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:")
                self.end_headers()
                return self.wfile.write(html)
            if url.path.startswith("/estatico/"):
                # <script src> não envia cabeçalhos: o token vem na URL, como na página
                if not secrets.compare_digest((parse_qs(url.query).get("t") or [""])[0], estado.token):
                    return self._responder(HTTPStatus.FORBIDDEN, {"erro": "token inválido"})
                return self._estatico(url.path[len("/estatico/"):])
            if not self._autorizado():
                return self._responder(HTTPStatus.FORBIDDEN, {"erro": "token inválido"})
            if url.path == "/api/ping":
                estado.ultimo_ping = time.time()
                idioma = i18n.idioma_interface()
                return self._responder(200, {"ok": True, "versao": VERSAO, "projeto_inicial": estado.projeto_inicial,
                                             "idioma": idioma,  # catálogo só no primeiro ping (?i18n=1)
                                             "textos": i18n.catalogo(idioma) if parse_qs(url.query).get("i18n") else {},
                                             "idioma_projetos": i18n.normalizar(config_freelancer().get("idioma_projetos"))})
            if url.path.startswith("/api/tarefas/"):
                tarefa = estado.tarefas.get(url.path.rsplit("/", 1)[-1])
                if not tarefa:
                    return self._responder(404, {"erro": "tarefa não encontrada"})
                desde = int((parse_qs(url.query).get("desde") or ["0"])[0])
                return self._responder(200, {"linhas": tarefa.linhas[desde:], "total": len(tarefa.linhas),
                                             "fim": tarefa.fim, "codigo": tarefa.codigo})
            return self._responder(404, {"erro": "não encontrado"})

        def _estatico(self, nome):
            # arquivos da própria interface (ex.: mermaid.min.js); exigem o token como a API
            arq = (PAGINA.parent / nome).resolve()
            if arq.parent != PAGINA.parent or arq.suffix not in (".js", ".css") or not arq.is_file():
                return self._responder(404, {"erro": "não encontrado"})
            tipo = "text/javascript; charset=utf-8" if arq.suffix == ".js" else "text/css; charset=utf-8"
            return self._responder(200, arq.read_bytes(), tipo)

        def do_POST(self):
            # Lê o corpo antes de recusar: no Windows, fechar o socket com dados não lidos
            # envia RST e o cliente recebe "conexão redefinida" em vez da resposta 403.
            bruto = self._ler_corpo()
            if not self._autorizado():
                return self._responder(HTTPStatus.FORBIDDEN, {"erro": "token inválido"})
            if bruto is None:
                return self._responder(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"erro": "requisição grande demais"})
            corpo = self._json(bruto)
            rota = urlparse(self.path).path
            try:
                if rota == "/api/executar":
                    return self._responder(200, executar(corpo))
                if rota == "/api/tarefas":
                    args = [str(a) for a in corpo.get("args") or []]
                    if not args or args[0] != "claude":
                        return self._responder(400, {"erro": "somente tarefas do Claude"})
                    pasta = corpo.get("projeto")
                    if pasta:
                        args = ["--projeto", pasta] + args
                    ident = secrets.token_hex(6)
                    estado.tarefas[ident] = Tarefa(args, pasta or str(Path.home()))
                    return self._responder(200, {"id": ident})
                if rota.startswith("/api/tarefas/") and rota.endswith("/parar"):
                    tarefa = estado.tarefas.get(rota.split("/")[3])
                    if tarefa and not tarefa.fim:
                        tarefa.parar()
                    return self._responder(200, {"ok": True})
                if rota == "/api/ler":
                    return self._responder(200, ler_arquivo(corpo))
                if rota == "/api/salvar":
                    return self._responder(200, salvar_arquivo(corpo))
                if rota == "/api/formulario":
                    return self._responder(200, salvar_formulario(corpo))
                if rota == "/api/abrir":
                    return self._responder(200, abrir(corpo))
                if rota == "/api/escolher-pasta":
                    r = subprocess.run(comando_base() + ["_escolher-pasta"], capture_output=True, env=_env(),
                                       timeout=600, **_flags_sem_janela())
                    try:
                        return self._responder(200, json.loads(r.stdout.decode("utf-8") or "{}"))
                    except json.JSONDecodeError:
                        return self._responder(200, {"pasta": ""})
            except Exception as e:  # erro inesperado vira mensagem para a interface
                return self._responder(500, {"erro": str(e)})
            return self._responder(404, {"erro": "rota desconhecida"})

    return Handler


def executar(corpo):
    args = [str(a) for a in corpo.get("args") or []]
    if not args or args[0] not in PERMITIDOS:
        return {"codigo": 2, "dados": {"erro": "comando não permitido pela interface"}}
    base = ["--json"] + (["--projeto", corpo["projeto"]] if corpo.get("projeto") else [])
    r = subprocess.run(comando_base() + base + args, capture_output=True, env=_env(), timeout=900,
                       cwd=corpo.get("projeto") or None, **_flags_sem_janela())
    texto = r.stdout.decode("utf-8", "replace")
    try:
        dados = json.loads(texto) if texto.strip() else None
    except json.JSONDecodeError:
        dados = None
    return {"codigo": r.returncode, "dados": dados, "saida": texto[-20000:] if dados is None else "",
            "stderr": r.stderr.decode("utf-8", "replace")[-4000:]}


def _dentro(projeto, arquivo):
    raiz = Path(projeto).resolve()
    alvo = (raiz / arquivo).resolve()
    try:
        alvo.relative_to(raiz)
    except ValueError:
        raise ValueError("arquivo fora da pasta do projeto") from None
    return alvo


def ler_arquivo(corpo):
    alvo = _dentro(corpo["projeto"], corpo["arquivo"])
    if alvo.suffix.lower() not in EXT_LEITURA or alvo.name.startswith(".env"):
        return {"erro": "tipo de arquivo não permitido"}
    return {"texto": alvo.read_text(encoding="utf-8", errors="replace")[:400_000], "versao": alvo.stat().st_mtime_ns}


def salvar_arquivo(corpo):
    """Grava um Markdown editado na interface: documentos em docs/, skills e subagentes em .claude/, CLAUDE.md e AGENTS.md.
    Nunca grava um documento aprovado pelo cliente nem sobrescreve uma alteração feita fora da interface."""
    raiz = Path(corpo["projeto"]).resolve()
    config = json.loads((raiz / "projeto.prumo.json").read_text(encoding="utf-8-sig"))
    alvo = _dentro(raiz, corpo["arquivo"])
    rel = alvo.relative_to(raiz).as_posix()
    editavel = rel.startswith(("docs/", ".claude/skills/", ".claude/agents/")) or rel in ("CLAUDE.md", "AGENTS.md")
    if alvo.suffix.lower() != ".md" or not editavel:
        return {"erro": "este arquivo não pode ser editado pela interface"}
    if rel in (config.get("aprovados") or {}):
        return {"erro": "documento aprovado pelo cliente: libere a edição antes de alterar"}
    if not alvo.is_file():
        return {"erro": "arquivo não encontrado"}
    if corpo.get("versao") is not None and alvo.stat().st_mtime_ns != int(corpo["versao"]):
        return {"erro": "o arquivo foi alterado fora da interface; recarregue antes de salvar", "conflito": True}
    texto = str(corpo.get("texto", ""))
    if len(texto) > 2_000_000:
        return {"erro": "arquivo grande demais"}
    with open(alvo, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto.replace("\r\n", "\n"))
    return {"ok": True, "versao": alvo.stat().st_mtime_ns}


def salvar_formulario(corpo):
    """Grava o formulário da interface: o CLI roda com a entrada padrão fechada, então o corpo vai para
    .prumo/formulario-recebido.json e `prumo formulario salvar` valida, atribui IDs e grava especificacao.prumo.json.
    Com "gerar", preenche em seguida os documentos (prumo gerar)."""
    raiz = Path(corpo["projeto"]).resolve()
    if not (raiz / "projeto.prumo.json").is_file():
        return {"codigo": 2, "dados": {"erro": "pasta sem projeto do Prumo"}}
    if not isinstance(corpo.get("formulario"), dict):
        return {"codigo": 2, "dados": {"erro": "formulário ausente"}}
    temp = raiz / ".prumo" / "formulario-recebido.json"
    temp.parent.mkdir(parents=True, exist_ok=True)
    temp.write_text(json.dumps(corpo["formulario"], ensure_ascii=False), encoding="utf-8")
    args = ["formulario", "salvar", str(temp)] + (["--gerar"] if corpo.get("gerar") else [])
    return executar({"args": args, "projeto": str(raiz)})


def _abrir_no_sistema(caminho):
    if os.name == "nt":
        os.startfile(str(caminho))  # noqa
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(caminho)])
    else:
        subprocess.Popen(["xdg-open", str(caminho)])


def abrir(corpo):
    projeto = Path(corpo["projeto"]).resolve()
    alvo = corpo.get("alvo", "pasta")
    if alvo == "pasta":
        _abrir_no_sistema(projeto)
    elif alvo == "arquivo":
        _abrir_no_sistema(_dentro(projeto, corpo["arquivo"]))
    elif alvo == "vscode":
        code = shutil.which("code")
        if not code:
            return {"erro": "VS Code (comando 'code') não encontrado no PATH"}
        subprocess.Popen([code, str(projeto)], **_flags_sem_janela())
    elif alvo == "claude":
        if os.name == "nt":
            terminal = shutil.which("wt")
            ps = shutil.which("pwsh") or "powershell"
            cmd = [ps, "-NoExit", "-Command", f"Set-Location -LiteralPath '{projeto}'; claude"]
            if terminal:
                subprocess.Popen([terminal, "-d", str(projeto)] + cmd)
            else:
                subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        elif sys.platform == "darwin":
            subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script "cd {projeto} && claude"'])
        else:
            term = shutil.which("x-terminal-emulator") or shutil.which("gnome-terminal")
            if not term:
                return {"erro": "nenhum terminal encontrado"}
            subprocess.Popen([term, "--", "sh", "-c", f'cd "{projeto}" && claude; exec sh'])
    return {"ok": True}


def _navegador_app():
    """Edge ou Chrome em modo aplicativo (janela própria, sem barra do navegador)."""
    candidatos = []
    if os.name == "nt":
        for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"), os.environ.get("LOCALAPPDATA")):
            if base:
                candidatos += [Path(base) / "Microsoft/Edge/Application/msedge.exe",
                               Path(base) / "Google/Chrome/Application/chrome.exe"]
    else:
        for nome in ("microsoft-edge", "google-chrome", "chromium", "chromium-browser"):
            if shutil.which(nome):
                candidatos.append(Path(shutil.which(nome)))
        candidatos.append(Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"))
        candidatos.append(Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"))
    return next((c for c in candidatos if c.exists()), None)


def iniciar(porta=0, abrir_janela=True, projeto_inicial=None):
    estado = Estado(str(Path(projeto_inicial).resolve()) if projeto_inicial else None)
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), criar_handler(estado))
    endereco = f"http://127.0.0.1:{servidor.server_address[1]}/?t={estado.token}"
    progresso(f"Prumo {VERSAO} — interface em {endereco}")
    if abrir_janela:
        navegador = _navegador_app()
        perfil = RAIZ_KIT / "config" / ".janela"
        if navegador:
            subprocess.Popen([str(navegador), f"--app={endereco}", f"--user-data-dir={perfil}",
                              "--window-size=1200,800", "--no-first-run", "--no-default-browser-check"])
        else:
            webbrowser.open(endereco)

        def vigiar():
            while True:
                time.sleep(10)
                ocupado = any(not t.fim for t in estado.tarefas.values())
                if not ocupado and time.time() - estado.ultimo_ping > 60:
                    servidor.shutdown()
                    return
        threading.Thread(target=vigiar, daemon=True).start()
    else:
        progresso("Ctrl+C para encerrar.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
    return 0
