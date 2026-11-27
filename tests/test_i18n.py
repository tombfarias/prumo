"""Testes do suporte a inglês: catálogo, modelos em inglês, projetos em inglês, estilo, CLI e hooks."""

import json
import re
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tools"))
sys.path.insert(0, str(RAIZ / "tests"))
os.environ["PRUMO_IDIOMA"] = "pt-BR"

import i18n as ferramenta_i18n  # noqa: E402  (tools/i18n.py)
from prumo_cli import estilo, i18n, projeto as mp, validacao  # noqa: E402
from prumo_cli.util import ler, tem_lacuna  # noqa: E402

TEMPLATES = RAIZ / "templates"


def criar_en(pasta, perfil):
    return mp.criar_projeto(Path(pasta) / "proj", perfil, nome="Test Project", cliente="Client", git=False, idioma="en")


class TestCatalogo(unittest.TestCase):
    def test_todo_texto_tem_traducao(self):
        self.assertEqual(ferramenta_i18n.faltando(), {}, "rode: python tools/i18n.py --json")

    def test_traducoes_preenchidas(self):
        textos = i18n.catalogo("en")
        vazios = [k for k, v in textos.items() if not v.strip()]
        self.assertEqual(vazios, [])

    def test_traduzir_e_proteger(self):
        frase = "mostra a versão"
        self.assertEqual(i18n.traduzir(frase, "pt-BR"), frase)
        self.assertNotIn("versão", i18n.traduzir(frase, "en"))
        self.assertEqual(i18n.traduzir(i18n.proteger(frase), "en"), frase)

    def test_idioma(self):
        self.assertEqual(i18n.normalizar("en-US"), "en")
        self.assertEqual(i18n.normalizar("pt_BR"), "pt-BR")
        with self.assertRaises(Exception):
            i18n.validar("xx")


class TestModelos(unittest.TestCase):
    def test_todo_modelo_tem_versao_em_ingles(self):
        faltam = []
        for pasta in ("documentos", "agentes", "perfis/convencoes"):
            for arq in (TEMPLATES / pasta).rglob("*.md"):
                rel = arq.relative_to(TEMPLATES)
                if not (TEMPLATES / "en" / rel).exists():
                    faltam.append(str(rel))
        self.assertEqual(faltam, [])

    def test_modelos_em_ingles_mantem_marcadores(self):
        for arq in (TEMPLATES / "en").rglob("*.md"):
            pt, en = ler(TEMPLATES / arq.relative_to(TEMPLATES / "en")), ler(arq)
            with self.subTest(arq=str(arq.relative_to(TEMPLATES))):
                self.assertEqual(set(re.findall(r"\{\{\w+\}\}", pt)), set(re.findall(r"\{\{\w+\}\}", en)))
                self.assertEqual(pt.count("```mermaid"), en.count("```mermaid"))
                self.assertNotIn("[PREENCHER", en)
                for marcador in ("prumo:figma", "prumo:gerado"):
                    self.assertEqual(marcador in pt, marcador in en, marcador)


class TestCatalogosEmIngles(unittest.TestCase):
    def test_todo_texto_dos_catalogos_tem_traducao(self):
        from prumo_cli import entrevista, formulario
        textos = formulario.textos_catalogo("en")
        faltam = set()

        def varrer(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in formulario.CAMPOS_DE_TEXTO and isinstance(v, str):
                        if v not in textos and "{valor}" not in v:
                            faltam.add(v)
                    else:
                        varrer(v)
            elif isinstance(o, list):
                for v in o:
                    varrer(v)
        varrer(formulario.carregar_catalogos())
        varrer(entrevista.carregar_perguntas())
        self.assertEqual(sorted(faltam), [], "acrescente em templates/en/catalogos/textos.json")

    def test_catalogos_em_ingles_mantem_ids(self):
        from prumo_cli import entrevista, formulario
        pt, en = formulario.carregar_catalogos(), formulario.carregar_catalogos("en")
        for nome in pt:
            self.assertEqual([i["id"] for i in pt[nome]], [i["id"] for i in en[nome]])
        self.assertEqual(en["rnf"][0]["categoria"], "Usability")
        q = entrevista.carregar_perguntas("en")
        self.assertEqual([x["id"] for x in q], [x["id"] for x in entrevista.carregar_perguntas()])
        self.assertNotRegex(q[0]["pergunta"], r"[ãçõé]")


class TestProjetoEmIngles(unittest.TestCase):
    def test_todos_os_perfis_em_ingles(self):
        for perfil in mp.listar_perfis():
            with self.subTest(perfil=perfil["id"]), tempfile.TemporaryDirectory() as tmp:
                p = criar_en(tmp, perfil["id"])
                self.assertEqual(p.idioma, "en")
                self.assertEqual(p.config["idioma"], "en")
                for arq in sorted(p.raiz.rglob("*.md")):
                    rel = p.rel(arq)
                    texto = ler(arq)
                    self.assertNotRegex(texto, r"\{\{\w+\}\}", rel)
                    self.assertNotIn("[PREENCHER", texto, rel)
                    achados = estilo.checar(texto, vagos=not rel.endswith("00-briefing.md"), idioma="en")
                    self.assertEqual(achados, [], rel)
                for arq in [p.raiz / "AGENTS.md", p.raiz / "CLAUDE.md", p.raiz / "README.md", *(p.raiz / ".claude").rglob("*.md")]:
                    sem_codigo = re.sub(r"`[^`]*`|\]\([^)]*\)|\b[\w-]+\.md\b", "", ler(arq))
                    self.assertNotRegex(sem_codigo, r"[ãõçáéíóúâêô]", p.rel(arq))  # sobrou português no kit
                self.assertIn("Golden rule", ler(p.raiz / "AGENTS.md"))
                self.assertTrue(tem_lacuna(ler(p.docs / "01-visao.md")))
                erros = [m for g, m in validacao.validar(p) if g == "erro"]
                self.assertEqual(erros, [], perfil["id"])

    def test_estilo_em_ingles(self):
        texto = "# T\n\nIt is important to note that the system is intuitive.\n\nUse it in order to save time.\n"
        msgs = [m for _, m in estilo.checar(texto, idioma="en")]
        self.assertTrue(any("intuitive" in m for m in msgs))
        self.assertTrue(any("in order to" in m for m in msgs))
        self.assertEqual(estilo.checar("# T\n\nThe page loads in 2 s.\n", idioma="en"), [])

    def test_hook_responde_em_ingles(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = criar_en(tmp, "minimo")
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(p.raiz), PYTHONIOENCODING="utf-8")
            entrada = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
            r = subprocess.run([sys.executable, str(p.raiz / ".claude" / "hooks" / "guarda_comandos.py")],
                               input=json.dumps(entrada).encode(), capture_output=True, env=env, timeout=60)
            self.assertEqual(r.returncode, 2)
            msg = r.stderr.decode("utf-8")
            self.assertNotRegex(msg, r"[ãçõé]", msg)


class TestGeracaoEmIngles(unittest.TestCase):
    def test_formulario_gera_documentos_em_ingles(self):
        import copy
        from test_prumo import FORMULARIO
        from prumo_cli import formulario, geracao
        with tempfile.TemporaryDirectory() as tmp:
            p = criar_en(tmp, "web-fullstack")
            formulario.salvar(p, copy.deepcopy(FORMULARIO))
            r = geracao.gerar(p)
            self.assertIn("docs/02-requisitos.md", r["alterados"])
            self.assertEqual(geracao.gerar(p)["alterados"], [])  # idempotente
            self.assertEqual([m for g, m in validacao.validar(p) if g == "erro"], [])
            req = ler(p.docs / "02-requisitos.md")
            self.assertIn("| ID | Description | Priority | Source |", req)
            self.assertIn("The system must allow users to", req)
            uc = ler(p.docs / "03-casos-de-uso.md")
            self.assertIn("#### Main flow", uc)
            self.assertIn("| Primary actor |", uc)
            self.assertIn("**Estimate:**", ler(p.docs / "08-backlog.md"))
            for arq in p.docs.rglob("*.md"):
                self.assertNotIn("[PREENCHER", ler(arq), p.rel(arq))
            seg = ler(p.docs / "12-seguranca.md")
            self.assertIn("Stolen session", seg)  # ameaça do catálogo de logins, em inglês
            self.assertIn("Usability", ler(p.docs / "02-requisitos.md"))


class TestCliEmIngles(unittest.TestCase):
    def rodar(self, *args, idioma="en"):
        env = dict(os.environ, PRUMO_IDIOMA=idioma, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, str(RAIZ / "prumo.py"), *args], capture_output=True, env=env, timeout=60)

    def test_ajuda_em_ingles(self):
        saida = self.rodar("--help").stdout.decode("utf-8")
        self.assertIn("usage", saida.lower())
        self.assertNotIn("mostra a versão", saida)
        self.assertIn("mostra a versão", self.rodar("--help", idioma="pt-BR").stdout.decode("utf-8"))

    def test_novo_com_idioma(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "p"
            r = self.rodar("novo", str(destino), "--perfil", "minimo", "--nome", "P", "--cliente", "C", "--sem-git",
                           "--idioma", "en", idioma="pt-BR")
            self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8"))
            self.assertEqual(json.loads(ler(destino / "projeto.prumo.json"))["idioma"], "en")
            self.assertIn("[FILL", ler(destino / "docs" / "01-visao.md"))


if __name__ == "__main__":
    unittest.main()
