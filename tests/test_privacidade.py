"""Testes do guarda de privacidade (.githooks/privacidade.py).

Os dados sensíveis daqui são fictícios e montados em tempo de execução, para que este arquivo não dispare o próprio
guarda nem os alertas de segredo do GitHub.
"""

import base64
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
import urllib.parse
import zipfile
import zlib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / ".githooks" / "privacidade.py"
ARROBA = "@"
EMAIL_REAL = "maria.ficticia" + ARROBA + "gmail.com"
NOREPLY = "123+maria" + ARROBA + "users.noreply.github.com"
TOKEN = "ghp" + "_" + "a1B2" * 9
TERMO = "Zéfiro Quintanilha"
USUARIO_FALSO = "UsuarioFicticioXyz"
ZEROS = "0" * 40


def cpf(base):
    """CPF válido (formatado) a partir de 9 dígitos."""
    n = [int(c) for c in base]
    for tam in (9, 10):
        n.append(sum(n[i] * (tam + 1 - i) for i in range(tam)) * 10 % 11 % 10)
    d = "".join(map(str, n))
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def carregar_modulo():
    spec = importlib.util.spec_from_file_location("privacidade", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def png_com_itxt(texto):
    """PNG mínimo com um chunk iTXt compactado (metadados XMP de editores de imagem)."""
    corpo = b"XML:com.adobe.xmp\0\x01\x00\0\0" + zlib.compress(texto.encode())
    chunk = len(corpo).to_bytes(4, "big") + b"iTXt" + corpo + zlib.crc32(b"iTXt" + corpo).to_bytes(4, "big")
    return b"\x89PNG\r\n\x1a\n" + chunk


class RepoTeste:
    """Repositório git temporário com uma cópia do guarda, configuração do git isolada e termos fictícios."""

    def __init__(self, tmp, ambiente=False):
        self.tmp = Path(tmp)
        self.raiz = self.tmp / "repo"
        (self.raiz / ".githooks").mkdir(parents=True)
        shutil.copy(SCRIPT, self.raiz / ".githooks" / "privacidade.py")
        self.privado = self.tmp / "privado.txt"
        self.privado.write_text("# termos de teste\n" + TERMO + "\n", encoding="utf-8")
        global_vazio = self.tmp / "gitconfig-global"
        global_vazio.write_text("", encoding="utf-8")
        self.env = {**os.environ, "PRUMO_PRIVADO": str(self.privado), "GIT_CONFIG_GLOBAL": str(global_vazio),
                    "GIT_CONFIG_NOSYSTEM": "1"}
        for k in ("GIT_AUTHOR_EMAIL", "GIT_COMMITTER_EMAIL", "GIT_AUTHOR_NAME", "GIT_COMMITTER_NAME", "EMAIL",
                  "GITHUB_ACTIONS", "CI", "GIT_DIR", "GIT_WORK_TREE"):
            self.env.pop(k, None)
        if ambiente:
            self.env.update({"PRUMO_PRIVACIDADE_AMBIENTE": "1", "USERNAME": USUARIO_FALSO, "USER": USUARIO_FALSO,
                             "LOGNAME": USUARIO_FALSO})
        else:
            self.env["PRUMO_PRIVACIDADE_AMBIENTE"] = "0"
        self.git("init", "-q")
        self.git("config", "user.name", "dono-teste")
        self.git("config", "user.email", NOREPLY)
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", "nenhum-hook")  # sem hooks até `instalar`
        self.git("remote", "add", "origin", "https://github.com/dono-teste/repo-teste.git")

    def git(self, *args, env=None):
        r = subprocess.run(["git", *args], cwd=self.raiz, capture_output=True, env=env or self.env)
        return r.stdout.decode("utf-8", "replace").strip()

    def git_rc(self, *args):
        r = subprocess.run(["git", *args], cwd=self.raiz, capture_output=True, env=self.env)
        return r.returncode, r.stderr.decode("utf-8", "replace")

    def escrever(self, nome, conteudo):
        p = self.raiz / nome
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(conteudo, bytes):
            p.write_bytes(conteudo)
        else:
            p.write_text(conteudo, encoding="utf-8")
        return p

    def commit(self, nome, conteudo, env=None):
        self.escrever(nome, conteudo)
        self.git("add", nome)
        self.git("commit", "-q", "-m", f"add {nome}", env=env)
        return self.git("rev-parse", "HEAD")

    def guarda(self, *args, entrada=b"", env=None):
        r = subprocess.run([sys.executable, str(self.raiz / ".githooks" / "privacidade.py"), *args], cwd=self.raiz,
                           input=entrada, capture_output=True, env=env or self.env)
        return r.returncode, r.stderr.decode("utf-8", "replace") + r.stdout.decode("utf-8", "replace")

    def preparado_bloqueia(self, nome, conteudo):
        self.escrever(nome, conteudo)
        self.git("add", nome)
        codigo, erro = self.guarda("pre-commit")
        self.git("reset", "-q")
        return codigo == 1, erro

    def claude(self, comando, cwd=None, ferramenta="Bash"):
        dados = {"tool_name": ferramenta, "tool_input": {"command": comando}, "cwd": str(cwd or self.raiz)}
        return self.guarda("claude", entrada=json.dumps(dados).encode("utf-8"))


class TestRegras(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = carregar_modulo()

    def achados(self, texto):
        v = self.mod.Varredor(termos=[("termo de teste", TERMO)])
        v.texto("x", texto)
        return v.achados

    def test_detecta(self):
        basic = base64.b64encode(("maria:" + "S3nhaForte").encode()).decode()
        casos = [
            EMAIL_REAL,
            "C:" + "\\Users\\" + "Mariazinha" + "\\docs\\a.md",
            "C:" + "/Users/" + "Mariazinha/docs",
            "/c/" + "Users/" + "Mariazinha/docs",
            "/home/" + "mariazinha/projetos",
            "\\\\wsl.localhost\\Ubuntu\\home\\" + "mariazinha\\x",
            "C:" + "\\Users\\" + "MARIAZ~1\\AppData",
            "token = " + TOKEN,
            "sk-" + "ant-" + "a1B2c3D4" * 5,
            "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
            "AKIA" + "QWERTYUIOPASDFGH",
            "documento: " + cpf("529982247"),
            "postgres://app:" + "S3nhaForte" + ARROBA + "db.interno:5432/app",
            "Authorization: Basic " + basic,
            TERMO,
            "zefiro quintanilha",  # sem acento e em minúsculas
            "Zéfiro-Quintanilha", "zéfiro_quintanilha", "ZéfiroQuintanilha", "Zéfiro  Quintanilha",
            "Zéfiro\nQuintanilha",  # quebrado entre linhas (parágrafo de Markdown)
            unicodedata.normalize("NFD", TERMO),  # acentos decompostos
            json.dumps({"autor": TERMO}),  # \u00e9
            urllib.parse.quote(TERMO),  # %C3%A9
            "Z&eacute;firo Quintanilha",  # entidade HTML
            "texto\x0c" + TOKEN,  # separador que str.splitlines trataria como quebra de linha
            "x" * 25000 + " " + TOKEN,  # linha enorme (.min.js)
        ]
        for caso in casos:
            with self.subTest(caso=caso[:30]):
                self.assertTrue(self.achados(caso), caso[:60])

    def test_nao_detecta(self):
        casos = [
            NOREPLY,
            "voce" + ARROBA + "exemplo.com",
            "contato" + ARROBA + "example.org",
            "user" + ARROBA + "domain.com",
            "Co-Authored-By: Claude <noreply" + ARROBA + "anthropic.com>",
            "git clone git" + ARROBA + "github.com:dono/repo.git",
            'srcset="logo' + ARROBA + '2x.png 2x"',
            "C:" + "\\Users\\" + "Public\\Desktop",
            "C:" + "\\Users\\" + "All Users\\Microsoft",
            "C:" + "\\Users\\" + "<nome>\\AppData",
            "/home/" + "runner/work",
            "WORKDIR /home/" + "app",
            "GET /users/me retorna o usuário logado",
            "Rota padrão: /Home/Index",
            "https://api.github.com/users/alguem",
            "C:\\Prumo\\prumo.exe",
            "123.456.789-09",
            "000.000.000-00",
            "11.222.333/0001-81",
            "postgres://user:senha" + ARROBA + "localhost/app",
            "postgres://app:app" + ARROBA + "db/app",
            "amqp://guest:guest" + ARROBA + "localhost:5672",
            "DATABASE_URL=postgres://app:${SENHA}" + ARROBA + "db/app",
            "Authorization: Basic " + base64.b64encode(b"user:password").decode(),
            "sk-" + "ant-" + "x" * 40,
            "AKIA" + "IOSFODNN7" + "EXAMPLE",
            "actions/checkout" + ARROBA + "v4",
            "Zéfiro é um vento; Quintanilha é outra palavra",
            "Custa 50% menos & entrega em 3 dias",
        ]
        for caso in casos:
            with self.subTest(caso=caso[:30]):
                self.assertEqual(self.achados(caso), [], caso)

    def test_ignorar_vale_so_para_regras_genericas(self):
        self.assertEqual(self.achados(EMAIL_REAL + "  # privacidade:ignorar"), [])
        self.assertTrue(self.achados(TERMO + "  # privacidade:ignorar"))

    def test_caminhos_proibidos(self):
        v = self.mod.Varredor(termos=[])
        for nome in (".env", "app/.env.local", "config/freelancer.json", "config/projetos.json", ".prumo/estado.json",
                     "CLAUDE.local.md", ".claude/settings.local.json", "chave.pem", "id_ed25519", "prumo.exe",
                     "erro.log"):
            v.caminho(nome)
        self.assertEqual(len({a[0] for a in v.achados}), 11, v.achados)
        v = self.mod.Varredor(termos=[])
        for nome in (".env.example", "templates/x/.env.exemplo", "config/freelancer.exemplo.json", "docs/chaves.md",
                     "assets/logo" + ARROBA + "2x.png"):
            v.caminho(nome)
        self.assertEqual(v.achados, [])

    def test_decodificar(self):
        texto = "autor: " + TERMO
        docx = io.BytesIO()
        with zipfile.ZipFile(docx, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("docProps/core.xml", "<dc:creator>" + TERMO + "</dc:creator>")
        pdf_flate = b"%PDF-1.7\n1 0 obj\n<< /Filter /FlateDecode >>\nstream\n" + zlib.compress(texto.encode()) + \
            b"\nendstream\nendobj\n"
        pdf_hex = b"%PDF-1.7\n<< /Author <" + ("\ufeff" + TERMO).encode("utf-16-be").hex().upper().encode() + b"> >>\n"
        for dados in (texto.encode("utf-16"), texto.encode("utf-16-le"), texto.encode("utf-16-be"),
                      texto.encode("cp1252"), b"\x89PNG\r\n\x1a\n\x00\x00" + texto.encode() + b"\x00\xff\x00",
                      docx.getvalue(), pdf_flate, pdf_hex, png_com_itxt(texto)):
            with self.subTest(dados=dados[:12]):
                self.assertTrue(self.achados(self.mod.decodificar(dados)[0]))

    def test_mascara_dados_do_comando(self):
        cmd = "cat <<'EOF' > a.md\ngit commit --no-verify\nEOF\ngit status && echo \"git push -f\""
        mascara = self.mod.mascarar_dados(cmd)
        self.assertEqual(len(mascara), len(cmd))
        self.assertNotIn("--no-verify", mascara)
        self.assertNotIn("push", mascara)
        self.assertIn("git status", mascara)


class TestHooksDoGit(unittest.TestCase):
    def test_pre_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = RepoTeste(tmp)
            r.escrever("docs/ok.md", "Conteúdo neutro\n")
            r.git("add", "docs/ok.md")
            self.assertEqual(r.guarda("pre-commit")[0], 0)
            r.git("reset", "-q")

            bloqueou, erro = r.preparado_bloqueia("docs/ruim.md", "linha 1\nautor: " + TERMO + "\n")
            self.assertTrue(bloqueou)
            self.assertIn("docs/ruim.md:2", erro)
            casos = {
                "utf16.txt": ("token: " + TOKEN).encode("utf-16"),  # o `>` do PowerShell 5.1
                "cp1252.txt": ("autor: " + TERMO).encode("cp1252"),
                "imagem.png": png_com_itxt("<dc:creator>" + TERMO + "</dc:creator>"),
                "config/freelancer.json": "{}\n",
            }
            for nome, conteudo in casos.items():
                with self.subTest(nome=nome):
                    self.assertTrue(r.preparado_bloqueia(nome, conteudo)[0])
            r.escrever(".gitattributes", "*.dat -diff\n")  # -diff não esconde o conteúdo
            self.assertTrue(r.preparado_bloqueia("dados.dat", "token: " + TOKEN + "\n")[0])
            self.assertFalse(r.preparado_bloqueia(".env.example", "SENHA=troque-aqui\n")[0])

            r.escrever("docs/ok.md", "Conteúdo neutro\n")
            r.git("add", "docs/ok.md")
            r.git("config", "user.email", EMAIL_REAL)
            codigo, erro = r.guarda("pre-commit")
            self.assertEqual(codigo, 1)
            self.assertIn("noreply", erro)

    def test_commit_msg(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = RepoTeste(tmp)
            msg = r.escrever("MSG", "feat: algo\n")
            self.assertEqual(r.guarda("commit-msg", str(msg))[0], 0)
            for texto in ("feat: algo para " + TERMO + "\n",
                          "#42 corrige bug relatado por " + TERMO + "\n"):  # com -m, linhas com # ficam na mensagem
                msg.write_text(texto, encoding="utf-8")
                self.assertEqual(r.guarda("commit-msg", str(msg))[0], 1, texto)
            msg.write_text("feat: x\n# ------------------------ >8 ------------------------\n+ " + TERMO + "\n",
                           encoding="utf-8")
            self.assertEqual(r.guarda("commit-msg", str(msg))[0], 0)

    def test_pre_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = RepoTeste(tmp)
            limpo = r.commit("a.md", "ok\n")
            entrada = f"refs/heads/main {limpo} refs/heads/main {ZEROS}\n".encode()
            self.assertEqual(r.guarda("pre-push", "origin", entrada=entrada)[0], 0)

            sujo = r.commit("b.md", "linha\ntoken: " + TOKEN + "\n")
            entrada = f"refs/heads/main {sujo} refs/heads/main {limpo}\n".encode()
            codigo, erro = r.guarda("pre-push", "origin", entrada=entrada)
            self.assertEqual(codigo, 1)
            self.assertIn("b.md:2", erro)
            self.assertIn("token do GitHub", erro)

            r.git("reset", "-q", "--hard", limpo)
            autor = r.commit("c.md", "ok\n", env={**r.env, "GIT_AUTHOR_EMAIL": EMAIL_REAL})
            codigo, erro = r.guarda("pre-push", "origin",
                                    entrada=f"refs/heads/main {autor} refs/heads/main {limpo}\n".encode())
            self.assertEqual(codigo, 1)
            self.assertIn("noreply", erro)
            # remoto que não existe localmente: varre tudo o que este remoto não tem
            entrada = f"refs/heads/main {autor} refs/heads/main {'f' * 40}\n".encode()
            self.assertEqual(r.guarda("pre-push", "origin", entrada=entrada)[0], 1)
            # apagar um branch remoto não envia nada
            entrada = f"(delete) {ZEROS} refs/heads/velho {limpo}\n".encode()
            self.assertEqual(r.guarda("pre-push", "origin", entrada=entrada)[0], 0)

            r.git("reset", "-q", "--hard", limpo)
            r.git("tag", "-a", "v1", "-m", "versão de " + TERMO)
            tag = r.git("rev-parse", "v1")
            entrada = f"refs/tags/v1 {tag} refs/tags/v1 {ZEROS}\n".encode()
            self.assertEqual(r.guarda("pre-push", "origin", entrada=entrada)[0], 1)
            blob = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=r.raiz, input=TOKEN.encode(),
                                  capture_output=True, env=r.env).stdout.decode().strip()
            entrada = f"refs/tags/dados {blob} refs/tags/dados {ZEROS}\n".encode()
            self.assertEqual(r.guarda("pre-push", "origin", entrada=entrada)[0], 1)

    def test_pre_push_confere_o_que_so_outro_remoto_tem(self):
        """Commit que já está num remoto privado (backup) ainda é conferido antes de ir para o público."""
        with tempfile.TemporaryDirectory() as tmp:
            r = RepoTeste(tmp)
            backup = Path(tmp) / "backup.git"
            subprocess.run(["git", "init", "-q", "--bare", str(backup)], capture_output=True, env=r.env)
            r.git("remote", "add", "backup", str(backup))
            sujo = r.commit("notas.md", "autor: " + TERMO + "\n")
            r.git("push", "-q", "backup", "HEAD:refs/heads/main")
            entrada = f"refs/heads/main {sujo} refs/heads/main {ZEROS}\n".encode()
            self.assertEqual(r.guarda("pre-push", "origin", entrada=entrada)[0], 1)
            self.assertEqual(r.guarda("pre-push", "backup", entrada=entrada)[0], 0)

    def test_historico(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = RepoTeste(tmp)
            r.commit("a.md", "autor: " + TERMO + "\n")
            r.commit("a.md", "autor: Ana Doces\n")
            self.assertEqual(r.guarda("tudo")[0], 0)
            codigo, erro = r.guarda("tudo", "--historico")
            self.assertEqual(codigo, 1)
            self.assertIn("a.md:1", erro)

    def test_falha_fechada(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp) / "sem-git"
            (pasta / ".githooks").mkdir(parents=True)
            shutil.copy(SCRIPT, pasta / ".githooks" / "privacidade.py")
            (pasta / "segredo.txt").write_text("token: " + TOKEN + "\n", encoding="utf-8")
            env = {**os.environ, "PRUMO_PRIVACIDADE_AMBIENTE": "0", "GIT_CEILING_DIRECTORIES": str(Path(tmp))}
            r = subprocess.run([sys.executable, str(pasta / ".githooks" / "privacidade.py"), "tudo"], cwd=pasta,
                               capture_output=True, env=env)
            self.assertEqual(r.returncode, 1)
            self.assertIn("não consegui conferir", r.stderr.decode("utf-8", "replace"))
            r2 = RepoTeste(Path(tmp) / "r2")
            codigo, _ = r2.guarda("pre-commit", env={**r2.env, "GIT_DIR": str(Path(tmp) / "nao-existe")})
            self.assertEqual(codigo, 1)

    def test_termos_da_maquina_e_projetos(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = RepoTeste(tmp, ambiente=True)
            self.assertTrue(r.preparado_bloqueia("nota.md", "autor: " + USUARIO_FALSO + "\n")[0])
            self.assertFalse(r.preparado_bloqueia("ok.md", "neutro\n")[0])
            # CI=1 não desliga nada; só o GitHub Actions desliga os termos da máquina
            r.escrever("nota.md", "autor: " + USUARIO_FALSO + "\n")
            r.git("add", "nota.md")
            self.assertEqual(r.guarda("pre-commit", env={**r.env, "CI": "1"})[0], 1)
            self.assertEqual(r.guarda("pre-commit", env={**r.env, "GITHUB_ACTIONS": "true"})[0], 0)
            r.git("reset", "-q")
            # user.name: só o login do GitHub (dono do origin ou o do e-mail noreply) passa
            r.escrever("ok.md", "neutro\n")
            r.git("add", "ok.md")
            r.git("config", "user.name", "Pessoa Teste")
            codigo, erro = r.guarda("pre-commit")
            self.assertEqual(codigo, 1)
            self.assertIn("git config user.name", erro)
            for nome in ("dono-teste", "maria"):
                r.git("config", "user.name", nome)
                self.assertEqual(r.guarda("pre-commit")[0], 0, nome)
            r.git("reset", "-q")
            # nomes de projeto e de cliente da lista de projetos recentes (fora de pastas temporárias)
            r.escrever("config/projetos.json", json.dumps([
                {"caminho": "D:/Clientes/padaria", "nome": "Padaria Estrela Guia", "cliente": "Joaquina Ferraz"},
                {"caminho": str(Path(tmp) / "Temp" / "x"), "nome": "Projeto Teste", "cliente": "Cliente"}]))
            self.assertTrue(r.preparado_bloqueia("docs/a.md", "Proposta para Joaquina Ferraz\n")[0])
            self.assertFalse(r.preparado_bloqueia("docs/b.md", "Projeto Teste do Cliente\n")[0])

    def test_instalar(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = RepoTeste(tmp)
            proprio = r.raiz / ".git" / "hooks" / "pre-commit"
            proprio.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            codigo, saida = r.guarda("instalar")
            self.assertEqual(codigo, 0, saida)
            self.assertEqual(r.git("config", "--get", "core.hooksPath"), "")
            for nome in ("pre-commit", "commit-msg", "pre-push"):
                stub = (r.raiz / ".git" / "hooks" / nome).read_text(encoding="utf-8")
                self.assertIn("prumo-privacidade", stub)
                self.assertIn(f'"$script" {nome}', stub)
                if os.name != "nt":
                    self.assertTrue(os.access(r.raiz / ".git" / "hooks" / nome, os.X_OK))
            self.assertTrue((r.raiz / ".git" / "hooks" / "pre-commit.antes-do-prumo").exists())
            self.assertEqual(r.guarda("instalar")[0], 0)  # idempotente

    def test_ponta_a_ponta_com_os_hooks(self):
        """git commit e git push de verdade, passando pelos hooks instalados."""
        with tempfile.TemporaryDirectory() as tmp:
            r = RepoTeste(tmp)
            remoto = Path(tmp) / "remoto.git"
            subprocess.run(["git", "init", "-q", "--bare", str(remoto)], capture_output=True, env=r.env)
            r.git("remote", "set-url", "origin", str(remoto))
            self.assertEqual(r.guarda("instalar")[0], 0)
            r.escrever("a.md", "ok\n")
            r.git("add", "a.md")
            self.assertEqual(r.git_rc("commit", "-q", "-m", "ok")[0], 0)
            r.escrever("b.md", "token: " + TOKEN + "\n")
            r.git("add", "b.md")
            codigo, erro = r.git_rc("commit", "-q", "-m", "token")
            self.assertNotEqual(codigo, 0)
            self.assertIn("token do GitHub", erro)
            r.git("-c", "core.hooksPath=nenhum-hook", "commit", "-q", "-m", "token")  # simula commit sem hooks
            codigo, erro = r.git_rc("push", "-q", "origin", "HEAD:refs/heads/main")
            self.assertNotEqual(codigo, 0)
            self.assertIn("token do GitHub", erro)
            # checkout sem o guarda (.githooks ausente): os hooks bloqueiam em vez de liberar em silêncio
            shutil.move(str(r.raiz / ".githooks"), str(Path(tmp) / "guardado"))
            r.escrever("c.md", "ok\n")
            r.git("add", "c.md")
            codigo, erro = r.git_rc("commit", "-q", "-m", "sem guarda")
            self.assertNotEqual(codigo, 0)
            self.assertIn(".githooks/privacidade.py", erro)


class TestHookDoClaude(unittest.TestCase):
    def test_git(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outro:
            r = RepoTeste(tmp)
            self.assertEqual(r.claude("git status")[0], 0)
            self.assertEqual(r.claude("ls", ferramenta="Read")[0], 0)
            codigo, erro = r.claude("git commit -am 'x'")
            self.assertEqual(codigo, 2)
            self.assertIn("privacidade.py instalar", erro)

            self.assertEqual(r.guarda("instalar")[0], 0)
            for cmd in ("git status", "git commit -am 'x'", "git push -u origin main",
                        "git config --get core.hooksPath", "python .githooks/privacidade.py instalar",
                        f'git -C "{outro}" commit --no-verify -m x', f'cd "{outro}" && git commit --no-verify -m x'):
                with self.subTest(cmd=cmd):
                    codigo, erro = r.claude(cmd)
                    self.assertEqual(codigo, 0, erro)
            bloqueia = [
                "git commit --no-verify -m x", "git commit -nm x", "git add . && git commit -n -m x",
                "git push --no-verify", 'git push "--no-verify" origin main', "git push --no-verif origin main",
                'git commit -m "feat: x\n\ncorpo" --no-verify',
                "git -c core.hooksPath=/dev/null commit -m x", "git -c alias.p=push p origin main",
                "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=x git push origin main",
                "PRUMO_PRIVACIDADE_AMBIENTE=0 git commit -m x",
                "git config core.hooksPath .githooks", "git config --unset core.hooksPath",
                "git config unset core.hooksPath", "git config core.hooksPath ''",
                "git config --rename-section core nucleo", "rm .git/hooks/pre-commit",
                f"(cd '{outro}' && ls); git push --no-verify origin main",
                "bash -c \"git commit --no-verify -m x\"",
                # conservador: citar --no-verify num comando que também fala em commit bloqueia
                "cat <<'EOF' > nota.md\nnunca use git commit --no-verify\nEOF",
            ]
            for cmd in bloqueia:
                with self.subTest(cmd=cmd):
                    self.assertEqual(r.claude(cmd)[0], 2)
            ps = f'Set-Location "{r.raiz}\\"; git commit --no-verify -m "x"'
            self.assertEqual(r.claude(ps, ferramenta="PowerShell")[0], 2)

    def test_script_ausente_nao_trava_a_sessao(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
            comando = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
            self.assertIn("! -f", comando)
            sh = shutil.which("sh") or shutil.which("bash")
            if not sh:
                self.skipTest("sh não encontrado")
            r = subprocess.run([sh, "-c", comando], input=b'{"tool_name":"Bash","tool_input":{"command":"ls"}}',
                               capture_output=True, env={**os.environ, "CLAUDE_PROJECT_DIR": tmp})
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_gh(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = RepoTeste(tmp)
            neutro = r.escrever("neutro.md", "Corpo neutro\n")
            corpo = r.escrever("corpo.md", "Contato: " + EMAIL_REAL + "\n")
            r.escrever("dist/prumo.exe", b"MZ\x00\x00")
            liberados = [
                "gh pr list",
                "gh pr create --title t --body 'Corrige o servidor'",
                f'cd "{r.raiz}" && gh pr create --title t --body ok',  # o cd não é publicado
                f'gh pr create --title t --body-file "{neutro}"',  # o caminho do arquivo também não
                "gh pr create --title t --body \"$(cat <<'EOF'\nCusta $10\nEOF\n)\"",
                "gh pr create --title t --body 'Custa $10'",
                "gh pr create -R outro/repo --body '" + TERMO + "'",
            ]
            for cmd in liberados:
                with self.subTest(cmd=cmd):
                    codigo, erro = r.claude(cmd)
                    self.assertEqual(codigo, 0, erro)
            bloqueados = [
                "gh pr create --title t --body 'Feito por " + TERMO + "'",
                "gh pr create --title '" + TERMO + "' --body ok",
                f"gh pr create --title t --body-file {corpo.name}",
                "gh issue create --title t --body \"$(cat <<'EOF'\nPasso a passo\n" + TOKEN + "\nEOF\n)\"",
                f'gh pr create --title t --body "$(cat {corpo.name})"',
                f'gh pr create --title t --body "$(cat {neutro.name} {corpo.name})"',
                'gh pr create --title t --body "$CORPO"',
                f"cat {corpo.name} | gh pr create --title t --body-file -",
                "gh api repos/dono-teste/repo-teste/issues -F title=x -F 'body=Feito por " + TERMO + "'",
                f"gh api repos/dono-teste/repo-teste/issues -F title=x -F body=@{corpo.name}",
                "gh api -X PUT repos/dono-teste/repo-teste/contents/a.md -f message=x -f content=b2s=",
                "gh pr create -R github.com/dono-teste/repo-teste --title t --body '" + TERMO + "'",
                "gh release create v1 --notes ok prumo.exe",
                "gh release create v1 --notes ok 'dist/*'",
                f"gh release upload v1 {corpo.name}",
                "bash -c \"gh pr create --title t --body '" + TERMO + "'\"",
            ]
            for cmd in bloqueados:
                with self.subTest(cmd=cmd):
                    self.assertEqual(r.claude(cmd)[0], 2)


class TestRepositorioPublico(unittest.TestCase):
    def test_repositorio_sem_dados_pessoais(self):
        """O próprio Prumo não pode conter dados pessoais de quem roda os testes (nem segredos)."""
        r = subprocess.run([sys.executable, str(SCRIPT), "tudo"], cwd=RAIZ, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))


if __name__ == "__main__":
    unittest.main()
