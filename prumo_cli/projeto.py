"""Criação e manutenção de projetos: perfis, documentos, kit de agentes, aprovações e registros."""

import re
import shutil
import subprocess
from pathlib import Path

from .util import (
    ARQUIVO_PROJETO, CONGELADO, RAIZ_KIT, python_disponivel, TEMPLATES, URL_PRUMO, VERSAO, ErroPrumo, agora_iso, aviso,
    comando_prumo, comando_python, config_freelancer, contar_lacunas, git_usuario, gravar,
    gravar_json, hash_conteudo, hoje_br, info, ler, ler_json, renderizar, slug,
)

DESCRICOES = {
    "00-briefing": "Anotações do cliente, restrições, perguntas em aberto e registro de reuniões",
    "01-visao": "Propósito, problema, usuários, escopo (dentro e fora), riscos",
    "02-requisitos": "Requisitos funcionais (RF), não funcionais (RNF), regras de negócio (RN), glossário",
    "03-casos-de-uso": "Atores, diagrama e especificação dos casos de uso (UC)",
    "04-uml/classes": "Modelo de domínio (diagrama de classes)",
    "04-uml/sequencia": "Diagramas de sequência por caso de uso",
    "04-uml/estados": "Ciclo de vida das entidades",
    "04-uml/atividades": "Processos de negócio",
    "04-uml/componentes": "Componentes e integrações",
    "04-uml/implantacao": "Ambientes e infraestrutura",
    "05-interface": "Design system, inventário de telas (TL) ligado ao Figma, navegação",
    "06-banco-de-dados": "Diagrama ER, dicionário de dados, índices, LGPD, migrações",
    "07-arquitetura": "Stack, estrutura de pastas, módulos, segurança, operação, ADRs",
    "08-backlog": "Épicos (EP), histórias (HU) com critérios de aceite e estimativas, marcos",
    "09-plano-de-testes": "Estratégia e casos de teste (CT), homologação",
    "10-proposta-comercial": "Proposta para o cliente: escopo, cronograma, investimento, condições",
    "11-entrega": "Implantação, checklist de entrega, manual de operação",
    "12-seguranca": "Superfície de ataque, ameaças, checklist OWASP, achados (SEG) e histórico de revisões",
}
IGNORAR_DOCS = {"rastreabilidade.md", "orcamento.md"}


# ---------------------------------------------------------------- perfis

def listar_perfis():
    perfis = []
    for arq in sorted((TEMPLATES / "perfis").glob("*.json")):
        perfis.append(ler_json(arq))
    return perfis


def carregar_perfil(perfil_id):
    arq = TEMPLATES / "perfis" / f"{perfil_id}.json"
    if not arq.exists():
        nomes = ", ".join(p["id"] for p in listar_perfis())
        raise ErroPrumo(f"Perfil '{perfil_id}' não existe. Perfis disponíveis: {nomes}")
    return ler_json(arq)


def documentos_disponiveis():
    base = TEMPLATES / "documentos"
    ids = []
    for arq in sorted(base.rglob("*.md")):
        rel = arq.relative_to(base).with_suffix("").as_posix()
        if rel not in ("adr", "mudanca"):
            ids.append(rel)
    return ids


# ---------------------------------------------------------------- projeto

class Projeto:
    def __init__(self, raiz):
        self.raiz = Path(raiz).resolve()
        self.arquivo_config = self.raiz / ARQUIVO_PROJETO
        self.config = ler_json(self.arquivo_config, None)
        if self.config is None:
            raise ErroPrumo(f"{self.raiz} não é um projeto do Prumo (falta {ARQUIVO_PROJETO}).")

    @classmethod
    def localizar(cls, inicio=None):
        atual = Path(inicio or Path.cwd()).resolve()
        for pasta in [atual, *atual.parents]:
            if (pasta / ARQUIVO_PROJETO).exists():
                return cls(pasta)
        raise ErroPrumo(
            "Nenhum projeto do Prumo encontrado aqui nem nas pastas acima. "
            "Entre na pasta do projeto, use --projeto <pasta> ou crie um com `prumo novo`."
        )

    @property
    def docs(self):
        return self.raiz / "docs"

    def salvar(self):
        gravar_json(self.arquivo_config, self.config)

    def arquivos_docs(self):
        if not self.docs.is_dir():
            return []
        saida = []
        for arq in sorted(self.docs.rglob("*.md")):
            rel = arq.relative_to(self.docs)
            if rel.parts[0] == "diagramas" or arq.name in IGNORAR_DOCS or arq.name.startswith("_"):
                continue
            saida.append(arq)
        return saida

    def rel(self, caminho):
        return Path(caminho).resolve().relative_to(self.raiz).as_posix()

    def figma_ativo(self):
        return bool((self.config.get("figma") or {}).get("ativo"))

    def contexto(self):
        c = self.config
        perfil = carregar_perfil(c["perfil"])
        python = c.get("python") or comando_python()
        figma = self.figma_ativo()
        ctx = {
            "projeto": c["projeto"],
            "slug": c.get("slug", slug(c["projeto"])),
            "prefixo": c.get("slug", slug(c["projeto"])).replace("-", "_"),
            "cliente": c.get("cliente", ""),
            "autor": c.get("autor", ""),
            "data": hoje_br(),
            "perfil": perfil["id"],
            "perfil_nome": perfil["nome"],
            "stack": c.get("stack") or perfil["stack"],
            "python": python,
            "prumo": comando_prumo(python),
            "url_prumo": URL_PRUMO,
        }
        ctx["lista_documentos"] = _lista_documentos(c.get("documentos") or [])
        ctx["lista_skills"] = _lista_skills(self.skills_do_kit())
        ctx["convencoes"] = renderizar(ler(TEMPLATES / "perfis" / "convencoes" / perfil["convencoes"]), ctx).strip()
        ctx["comandos_figma"] = (
            f"| `{ctx['prumo']} figma telas` | Sincroniza o inventário de telas (TL) de `docs/05-interface.md` com o arquivo do Figma |\n"
            if figma else ""
        )
        ctx["figma_claude"] = (
            "- **Figma:** o servidor MCP oficial do Figma está em `.mcp.json` (remoto, `https://mcp.figma.com/mcp`). "
            "Na primeira vez, rode `/mcp`, escolha **figma** e autentique. Skills: `/implementar-tela-figma` e `/diagramas-figjam`.\n"
            if figma else ""
        )
        return ctx

    def skills_do_kit(self):
        """Skills do kit que este projeto recebe, conforme as condições de templates/agentes/kit.json."""
        regras = ler_json(TEMPLATES / "agentes" / "kit.json").get("skills", {})
        fatos = {"figma": self.figma_ativo(), "perfil": self.config.get("perfil", "")}
        return [d for d in sorted((TEMPLATES / "agentes" / "claude" / "skills").iterdir())
                if d.is_dir() and condicao_kit(regras.get(d.name, ""), fatos)]

    def comando_hook(self, nome, args=""):
        """Linha de comando de um hook: Python (padrão, portátil) ou o próprio prumo.exe (sem Python instalado)."""
        c = self.config
        sufixo = f" {args}" if args else ""
        if c.get("hooks_via") == "prumo":
            return f"{comando_prumo()} hook {nome}{sufixo}"
        python = c.get("python") or comando_python()
        base = self.raiz.as_posix() if c.get("hooks_absolutos") else "$CLAUDE_PROJECT_DIR"
        return f'{python} "{base}/.claude/hooks/{nome}.py"{sufixo}'

    def settings_claude(self):
        import json
        dados = json.loads(ler(TEMPLATES / "agentes" / "claude" / "settings.json"))
        for grupos in (dados.get("hooks") or {}).values():
            for grupo in grupos:
                for h in grupo.get("hooks", []):
                    cmd = h.get("command", "")
                    if cmd.startswith("HOOK:"):
                        nome, _, args = cmd[5:].partition(" ")
                        h["command"] = self.comando_hook(nome, args)
        return json.dumps(dados, ensure_ascii=False, indent=2) + "\n"

    # ------------------------------------------------------------ kit de agentes

    def instalar_kit_agentes(self, incluir_settings=True, sobrescrever=True):
        """Copia skills, subagentes, hooks e instruções do kit para o projeto. Retorna os arquivos escritos."""
        ctx = self.contexto()
        base = TEMPLATES / "agentes"
        escritos = []

        def escrever(destino, texto, forcar=sobrescrever):
            destino = self.raiz / destino
            if destino.exists() and not forcar:
                return
            gravar(destino, texto)
            escritos.append(self.rel(destino))

        for skill in self.skills_do_kit():
            escrever(f".claude/skills/{skill.name}/SKILL.md", renderizar(ler(skill / "SKILL.md"), ctx))
        for agente in sorted((base / "claude" / "agents").glob("*.md")):
            escrever(f".claude/agents/{agente.name}", renderizar(ler(agente), ctx))
        for hook in sorted((base / "claude" / "hooks").glob("*.py")):
            escrever(f".claude/hooks/{hook.name}", ler(hook))
        if incluir_settings:
            escrever(".claude/settings.json", self.settings_claude())
        if self.figma_ativo():
            escrever(".mcp.json", ler(base / "mcp.json"), forcar=False)
        return escritos


def _lista_documentos(documentos):
    linhas = ["| Documento | Conteúdo |", "|---|---|"]
    for doc in documentos:
        doc_id = doc[len("docs/"):-3] if doc.startswith("docs/") else doc
        linhas.append(f"| [`{doc}`]({doc}) | {DESCRICOES.get(doc_id, '')} |")
    linhas.append("| `docs/adr/`, `docs/mudancas/` | Decisões arquiteturais e pedidos de mudança (modelos em `_modelo.md`) |")
    linhas.append("| `docs/rastreabilidade.md`, `docs/orcamento.md` | Gerados pelo Prumo; não edite à mão |")
    return "\n".join(linhas)


def _frontmatter(texto):
    m = re.match(r"^---\s*\n(.*?)\n---", texto, flags=re.S)
    dados = {}
    if m:
        for linha in m.group(1).splitlines():
            if ":" in linha:
                k, v = linha.split(":", 1)
                dados[k.strip()] = v.strip()
    return dados


def condicao_kit(condicao, fatos):
    """Avalia uma condição do kit.json: vazia (sempre), `figma`, `perfil:<id>`; `!` nega. Desconhecida = falsa."""
    condicao = (condicao or "").strip()
    if not condicao:
        return True
    if condicao.startswith("!"):
        return not condicao_kit(condicao[1:], fatos)
    nome, _, valor = condicao.partition(":")
    if nome == "figma" and not valor:
        return bool(fatos.get("figma"))
    if nome == "perfil" and valor:
        return fatos.get("perfil") == valor
    return False


def _lista_skills(skills):
    linhas = ["| Skill | Quando usar | Arquivo |", "|---|---|---|"]
    for skill in skills:
        fm = _frontmatter(ler(skill / "SKILL.md"))
        primeira = fm.get("description", "").split(". ")[0].rstrip(".")
        linhas.append(f"| `{skill.name}` | {primeira}. | `.claude/skills/{skill.name}/SKILL.md` |")
    return "\n".join(linhas)


# ---------------------------------------------------------------- criação

def criar_projeto(destino, perfil_id, nome=None, cliente="", stack=None, autor=None, figma=None,
                  figma_url="", git=True, python=None, hooks_absolutos=False, hooks_via=None, forcar=False):
    destino = Path(destino).resolve()
    if destino.exists() and any(destino.iterdir()) and not forcar:
        raise ErroPrumo(f"A pasta {destino} já existe e não está vazia (use --forcar para usar mesmo assim).")
    if (destino / ARQUIVO_PROJETO).exists():
        raise ErroPrumo(f"{destino} já é um projeto do Prumo.")
    perfil = carregar_perfil(perfil_id)
    freelancer = config_freelancer()
    nome = nome or destino.name
    usar_figma = perfil.get("figma", False) if figma is None else figma
    usar_figma = usar_figma or bool(figma_url)
    documentos = [f"docs/{d}.md" for d in perfil["documentos"]]

    destino.mkdir(parents=True, exist_ok=True)
    config = {
        "prumo": VERSAO,
        "projeto": nome,
        "slug": slug(nome),
        "cliente": cliente or "[PREENCHER: cliente]",
        "autor": autor or freelancer.get("nome") or git_usuario() or "[PREENCHER: autor]",
        "perfil": perfil["id"],
        "stack": stack or perfil["stack"],
        "criado_em": agora_iso(),
        "python": python or comando_python(),
        "hooks_absolutos": bool(hooks_absolutos),
        "hooks_via": hooks_via or ("prumo" if CONGELADO and not python_disponivel() else "python"),
        "documentos": documentos,
        "aprovados": {},
        "comandos": {"formatar": "", "lint": "", "testar": ""},
        "comandos_sugeridos": perfil.get("comandos_sugeridos", {}),
        "hooks": {
            "registrar_horas": True, "testes_ao_parar": False, "comandos_permitidos": [],
            "revisao_pos_mudanca": True, "limite_arquivos": 3, "limite_linhas": 80, "caminhos_sensiveis": [],
        },
        "pastas_codigo": perfil.get("pastas") or ["src", "tests"],
        "figma": {"ativo": usar_figma, "arquivo": figma_url, "telas": {}},
        "orcamento": {"valor_hora": None, "contingencia_percentual": None},
        "claude": {"modelo": "", "max_turnos": None, "ferramentas_extras": []},
    }
    gravar_json(destino / ARQUIVO_PROJETO, config)
    projeto = Projeto(destino)
    ctx = projeto.contexto()

    for doc in perfil["documentos"]:
        texto = renderizar(ler(TEMPLATES / "documentos" / f"{doc}.md"), ctx)
        if doc == "05-interface" and figma_url:
            texto = texto.replace("| Arquivo do Figma | [PREENCHER: URL] |", f"| Arquivo do Figma | {figma_url} |")
        gravar(destino / "docs" / f"{doc}.md", texto)
    for pasta, modelo, prefixo in (("adr", "adr", "ADR"), ("mudancas", "mudanca", "CM")):
        ctx_modelo = dict(ctx, id=f"{prefixo}-NNN", titulo="Título")
        gravar(destino / "docs" / pasta / "_modelo.md", renderizar(ler(TEMPLATES / "documentos" / f"{modelo}.md"), ctx_modelo))

    _limpar_exemplos_orfaos(projeto)
    base = TEMPLATES / "agentes"
    gravar(destino / "AGENTS.md", renderizar(ler(base / "AGENTS.md"), ctx))
    gravar(destino / "CLAUDE.md", renderizar(ler(base / "CLAUDE.md"), ctx))
    gravar(destino / "README.md", renderizar(ler(base / "README.md"), ctx))
    gravar(destino / ".gitignore", ler(base / "gitignore"))
    gravar(destino / ".env.example", "# Variáveis de ambiente do projeto (sem valores reais). Copie para .env.\n")
    projeto.instalar_kit_agentes()
    for pasta in config["pastas_codigo"]:
        (destino / pasta).mkdir(parents=True, exist_ok=True)
        gravar(destino / pasta / ".gitkeep", "")

    if git and shutil.which("git") and not (destino / ".git").exists():
        _git_inicial(destino, nome)
    return projeto


def _limpar_exemplos_orfaos(projeto):
    """Nos modelos, exemplos citam IDs de documentos que o perfil pode não ter (ex.: UC-001 no perfil mínimo)."""
    from . import rastreio
    orfaos = set(rastreio.analisar_projeto(projeto).indefinidos())
    if not orfaos:
        return
    padrao = re.compile(r"\b(" + "|".join(re.escape(o) for o in orfaos) + r")\b")
    for arq in projeto.arquivos_docs():
        texto = ler(arq)
        novo = padrao.sub("—", texto)
        if novo != texto:
            gravar(arq, novo)


def _git_inicial(destino, nome):
    def git(*args):
        return subprocess.run(["git", *args], cwd=destino, capture_output=True, text=True)
    if git("init", "-b", "main").returncode != 0:
        git("init")
    git("add", "-A")
    r = git("commit", "-m", f"chore: estrutura inicial do projeto {nome} (Prumo)")
    if r.returncode != 0:
        aviso("repositório git criado, mas o commit inicial falhou (configure git user.name e user.email e faça o commit).")


# ---------------------------------------------------------------- documentos extras

def adicionar_documento(projeto, doc_id):
    disponiveis = documentos_disponiveis()
    if doc_id not in disponiveis:
        raise ErroPrumo(f"Documento '{doc_id}' não existe. Disponíveis: {', '.join(disponiveis)}")
    destino = projeto.docs / f"{doc_id}.md"
    if destino.exists():
        raise ErroPrumo(f"{projeto.rel(destino)} já existe.")
    gravar(destino, renderizar(ler(TEMPLATES / "documentos" / f"{doc_id}.md"), projeto.contexto()))
    rel = projeto.rel(destino)
    docs = projeto.config.setdefault("documentos", [])
    if rel not in docs:
        docs.append(rel)
        docs.sort()
    projeto.salvar()
    return rel


# ---------------------------------------------------------------- aprovação

def _caminho_doc(projeto, arquivo):
    p = Path(arquivo)
    candidatos = [p if p.is_absolute() else Path.cwd() / p, projeto.raiz / p, projeto.docs / p,
                  projeto.docs / (str(p) + ".md")]
    for c in candidatos:
        if c.exists() and c.is_file():
            return c.resolve()
    raise ErroPrumo(f"Documento não encontrado: {arquivo}")


def aprovar(projeto, arquivos, forcar=False):
    aprovados = projeto.config.setdefault("aprovados", {})
    feitos = []
    for arquivo in arquivos:
        caminho = _caminho_doc(projeto, arquivo)
        rel = projeto.rel(caminho)
        lacunas = contar_lacunas(ler(caminho))
        if lacunas and not forcar:
            raise ErroPrumo(f"{rel} ainda tem {lacunas} lacuna(s) [PREENCHER]. Complete ou use --forcar.")
        aprovados[rel] = {"data": agora_iso(), "sha256": hash_conteudo(caminho)}
        feitos.append(rel)
    projeto.salvar()
    return feitos


def desaprovar(projeto, arquivos):
    aprovados = projeto.config.setdefault("aprovados", {})
    feitos = []
    for arquivo in arquivos:
        try:
            rel = projeto.rel(_caminho_doc(projeto, arquivo))
        except ErroPrumo:
            rel = Path(arquivo).as_posix()
        if rel in aprovados:
            del aprovados[rel]
            feitos.append(rel)
        else:
            aviso(f"{rel} não estava aprovado.")
    projeto.salvar()
    return feitos


# ---------------------------------------------------------------- ADR e mudanças

def novo_registro(projeto, tipo, titulo):
    pasta, prefixo, modelo = {"adr": ("adr", "ADR", "adr"), "mudanca": ("mudancas", "CM", "mudanca")}[tipo]
    destino_pasta = projeto.docs / pasta
    destino_pasta.mkdir(parents=True, exist_ok=True)
    numeros = [int(m.group(1)) for a in destino_pasta.glob(f"{prefixo}-*.md")
               if (m := re.match(rf"{prefixo}-(\d+)", a.name))]
    ident = f"{prefixo}-{(max(numeros) + 1 if numeros else 1):03d}"
    ctx = dict(projeto.contexto(), id=ident, titulo=titulo)
    destino = destino_pasta / f"{ident}-{slug(titulo)}.md"
    gravar(destino, renderizar(ler(TEMPLATES / "documentos" / f"{modelo}.md"), ctx))
    return ident, projeto.rel(destino)


def ativar_figma(projeto, url=""):
    figma = projeto.config.setdefault("figma", {"ativo": False, "arquivo": "", "telas": {}})
    figma["ativo"] = True
    if url:
        figma["arquivo"] = url
    projeto.salvar()
    escritos = projeto.instalar_kit_agentes(incluir_settings=False)
    if not (projeto.docs / "05-interface.md").exists():
        escritos.append(adicionar_documento(projeto, "05-interface"))
    return escritos


def instrucoes_iniciais(projeto):
    p = comando_prumo(projeto.config.get("python"))
    info(f"Projeto criado em {projeto.raiz}")
    info("")
    info("Próximos passos:")
    info(f"  1. cd \"{projeto.raiz}\"")
    info("  2. Cole as anotações do cliente em docs/00-briefing.md (ou peça ao Claude para fazer isso).")
    info("  3. Abra o Claude Code na pasta (`claude`) e rode /especificar-projeto")
    info(f"     ou, pelo terminal/PowerShell: {p} claude especificar")
    info(f"  4. Acompanhe com `{p} status` e `{p} validar`.")
    sugeridos = projeto.config.get("comandos_sugeridos") or {}
    if any(sugeridos.values()):
        info("  5. Quando a stack estiver instalada, copie 'comandos_sugeridos' para 'comandos' em projeto.prumo.json")
        info("     para os hooks formatarem e rodarem o lint a cada edição.")
    if projeto.figma_ativo():
        info("  Figma: no Claude Code, rode /mcp, escolha 'figma' e autentique. Para o inventário de telas:")
        info(f"     defina FIGMA_TOKEN e rode `{p} figma telas <url-do-arquivo>`.")
