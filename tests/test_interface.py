"""Testes da interface gráfica: comandos novos da CLI usados por ela, rotas do servidor e paleta de cores."""

import io
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))

from prumo_cli import cli, projeto as mp, servidor, util  # noqa: E402
import cores  # noqa: E402


def criar(pasta, perfil="minimo"):
    return mp.criar_projeto(Path(pasta) / "proj", perfil, nome="Projeto Teste", cliente="Cliente", git=False)


def rodar(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        codigo = cli.main(["--json", *args])
    return codigo, json.loads(buf.getvalue() or "null")


class KitIsolado(unittest.TestCase):
    """Redireciona config/ do Prumo para uma pasta temporária (não toca no freelancer.json real)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        kit = self.tmp / "kit"
        (kit / "config").mkdir(parents=True)
        for alvo in (mock.patch.object(cli, "RAIZ_KIT", kit), mock.patch.object(util, "RAIZ_KIT", kit)):
            alvo.start()
            self.addCleanup(alvo.stop)
        self.addCleanup(self._tmp.cleanup)


class TestConfigEProjetos(KitIsolado):
    def test_config_freelancer_e_projeto(self):
        p = criar(self.tmp)
        codigo, d = rodar("config", "--projeto", str(p.raiz), "--definir", "freelancer.valor_hora=150,5",
                          "--definir", "freelancer.nome=Ana", "--definir", "projeto.comandos.testar=npm test",
                          "--definir", "projeto.hooks.testes_ao_parar=sim", "--definir", 'projeto.pastas_codigo=["app","lib"]',
                          "--definir", "projeto.claude.max_turnos=")
        self.assertEqual(codigo, 0)
        self.assertEqual(d["freelancer"]["valor_hora"], 150.5)
        self.assertEqual(d["freelancer"]["nome"], "Ana")
        self.assertEqual(d["projeto"]["comandos.testar"], "npm test")
        self.assertIs(d["projeto"]["hooks.testes_ao_parar"], True)
        self.assertEqual(d["projeto"]["pastas_codigo"], ["app", "lib"])
        self.assertIsNone(d["projeto"]["claude.max_turnos"])
        salvo = json.loads((p.raiz / "projeto.prumo.json").read_text(encoding="utf-8"))
        self.assertEqual(salvo["comandos"]["testar"], "npm test")
        self.assertEqual(json.loads((self.tmp / "kit" / "config" / "freelancer.json").read_text(encoding="utf-8"))["nome"], "Ana")

    def test_config_recusa_chave_e_valor_invalidos(self):
        p = criar(self.tmp)
        for item in ("projeto.aprovados={}", "freelancer.senha=x", "projeto.hooks.limite_linhas=muitas", "outra.coisa=1"):
            codigo, d = rodar("config", "--projeto", str(p.raiz), "--definir", item)
            self.assertEqual(codigo, 2, item)
            self.assertIn("erro", d)

    def test_remover_recente(self):
        p = criar(self.tmp)
        rodar("status", "--projeto", str(p.raiz))
        _, lista = rodar("projetos")
        self.assertEqual([x["caminho"] for x in lista], [str(p.raiz)])
        _, lista = rodar("projetos", "--remover", str(p.raiz))
        self.assertEqual(lista, [])
        self.assertTrue((p.raiz / "projeto.prumo.json").exists())  # só sai da lista


class TestKit(unittest.TestCase):
    def test_listar_kit(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = criar(tmp)
            itens = p.listar_kit()
            tipos = {i["tipo"] for i in itens}
            self.assertTrue({"skill", "subagente", "hook", "instruções", "configuração"} <= tipos)
            self.assertTrue(all(i["estado"] == "igual ao kit" for i in itens), [i for i in itens if i["estado"] != "igual ao kit"])
            guarda = next(i for i in itens if i["nome"] == "guarda_arquivos")
            self.assertTrue(guarda["descricao"])
            self.assertTrue(any(e.startswith("PreToolUse") for e in guarda["eventos"]))
            skill = next(i for i in itens if i["tipo"] == "skill")
            alvo = p.raiz / skill["arquivo"]
            alvo.write_text(alvo.read_text(encoding="utf-8") + "\nAjuste do projeto.\n", encoding="utf-8")
            (p.raiz / ".claude" / "skills" / "minha-skill").mkdir()
            (p.raiz / ".claude" / "skills" / "minha-skill" / "SKILL.md").write_text("---\nname: minha-skill\ndescription: Própria.\n---\n", encoding="utf-8")
            (p.raiz / ".claude" / "agents" / "testador.md").unlink()
            estados = {i["nome"]: i["estado"] for i in p.listar_kit()}
            self.assertEqual(estados[skill["nome"]], "modificado")
            self.assertEqual(estados["minha-skill"], "próprio")
            self.assertEqual(estados["testador"], "ausente")
            p.instalar_kit_agentes(incluir_settings=False)
            self.assertEqual({i["nome"]: i["estado"] for i in p.listar_kit()}[skill["nome"]], "igual ao kit")


class TestServidorInterface(unittest.TestCase):
    def setUp(self):
        from http.server import ThreadingHTTPServer
        self._tmp = tempfile.TemporaryDirectory()
        self.p = criar(self._tmp.name)
        self.estado = servidor.Estado()
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), servidor.criar_handler(self.estado))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        self._tmp.cleanup()

    def post(self, rota, corpo):
        req = urllib.request.Request(self.base + rota, data=json.dumps(corpo).encode(), method="POST",
                                     headers={"X-Prumo-Token": self.estado.token, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())

    def test_salvar_documento(self):
        raiz, doc = str(self.p.raiz), "docs/01-visao.md"
        lido = self.post("/api/ler", {"projeto": raiz, "arquivo": doc})
        r = self.post("/api/salvar", {"projeto": raiz, "arquivo": doc, "texto": "# Visão\r\nPronto.\r\n", "versao": lido["versao"]})
        self.assertTrue(r.get("ok"), r)
        self.assertEqual((self.p.raiz / doc).read_bytes(), "# Visão\nPronto.\n".encode("utf-8"))  # CRLF vira LF
        # versão antiga: o arquivo mudou desde a leitura, não sobrescreve
        r = self.post("/api/salvar", {"projeto": raiz, "arquivo": doc, "texto": "x", "versao": lido["versao"] - 1})
        self.assertTrue(r.get("conflito"), r)
        # aprovado: recusa
        mp.aprovar(mp.Projeto(raiz), [doc], forcar=True)
        r = self.post("/api/salvar", {"projeto": raiz, "arquivo": doc, "texto": "x"})
        self.assertIn("aprovado", r.get("erro", ""))
        self.assertIn("Pronto.", (self.p.raiz / doc).read_text(encoding="utf-8"))

    def test_salvar_recusa_fora_da_area(self):
        raiz = str(self.p.raiz)
        for arq in ("projeto.prumo.json", ".claude/hooks/guarda_arquivos.py", ".claude/settings.json", "src/x.md"):
            (self.p.raiz / arq).parent.mkdir(parents=True, exist_ok=True)
            if not (self.p.raiz / arq).exists():
                (self.p.raiz / arq).write_text("x", encoding="utf-8")
            self.assertIn("erro", self.post("/api/salvar", {"projeto": raiz, "arquivo": arq, "texto": "y"}), arq)
        with self.assertRaises(urllib.error.HTTPError):
            self.post("/api/salvar", {"projeto": raiz, "arquivo": "../fora.md", "texto": "y"})
        skill = next(self.p.raiz.glob(".claude/skills/*/SKILL.md")).relative_to(self.p.raiz).as_posix()
        self.assertTrue(self.post("/api/salvar", {"projeto": raiz, "arquivo": skill, "texto": "ok"}).get("ok"))

    def test_estatico_exige_token(self):
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(self.base + "/estatico/mermaid.min.js", timeout=30)
        with urllib.request.urlopen(f"{self.base}/estatico/mermaid.min.js?t={self.estado.token}", timeout=30) as r:
            self.assertIn("javascript", r.headers["Content-Type"])
            self.assertGreater(len(r.read()), 100_000)
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(f"{self.base}/estatico/../servidor.py?t={self.estado.token}", timeout=30)

    def test_comandos_novos_permitidos(self):
        # pela API sem rodar o subprocesso: ele gravaria o projeto de teste nos recentes reais do Prumo
        self.assertTrue({"config", "agentes", "projetos"} <= servidor.PERMITIDOS)
        r = self.post("/api/executar", {"args": ["hook", "x"]})
        self.assertEqual(r["codigo"], 2)


class TestAgentesListarCli(KitIsolado):
    def test_listar_pela_cli(self):
        p = criar(self.tmp)
        codigo, itens = rodar("agentes", "listar", "--projeto", str(p.raiz))
        self.assertEqual(codigo, 0)
        self.assertTrue(any(i["tipo"] == "hook" and i["eventos"] for i in itens))


class TestPaleta(unittest.TestCase):
    def test_contraste_e_daltonismo(self):
        relatorio, falhas = cores.verificar()
        self.assertEqual(falhas, 0, "\n".join(relatorio))

    def test_verificador_detecta_falha(self):
        css = (cores.PAGINA.read_text(encoding="utf-8")).replace("--suave:#6f6a61", "--suave:#d0ccc4", 1)
        self.assertGreater(cores.verificar(css)[1], 0)


if __name__ == "__main__":
    unittest.main()
