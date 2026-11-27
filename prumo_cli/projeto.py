"""Criação e manutenção de projetos: perfis, documentos, kit de agentes, aprovações e registros."""

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import mapear
from .util import (
    ARQUIVO_PROJETO, CONGELADO, RAIZ_KIT, python_disponivel, TEMPLATES, URL_PRUMO, VERSAO, ErroPrumo, agora_iso, aviso,
    comando_prumo, comando_python, config_freelancer, contar_lacunas, git_usuario, gravar, gravar as _gravar,
    carimbo, gravar_json, guardar_copia, hash_conteudo, hash_texto, hoje_br, info, ler, ler_json, renderizar, slug,
)

DESCRICOES = {
    "00-briefing": "Anotações do cliente, restrições, perguntas em aberto e registro de reuniões",
    "01-visao": "Propósito, problema, usuários, escopo (dentro e fora), riscos",
    "02-requisitos": "Requisitos funcionais (RF), não funcionais (RNF), regras de negócio (RN), glossário",
    "03-casos-de-uso": "Atores, diagrama e especificação dos casos de uso (UC)",
    "04-uml/classes": "Modelo de domínio (diagrama de classes)",
    "04-uml/objetos": "Instâncias de exemplo que validam o modelo de classes",
    "04-uml/pacotes": "Pacotes/módulos e dependências permitidas",
    "04-uml/componentes": "Componentes e integrações",
    "04-uml/estrutura-composta": "Partes, portas e conectores internos de componentes",
    "04-uml/implantacao": "Ambientes e infraestrutura",
    "04-uml/perfil-uml": "Estereótipos e valores etiquetados usados nos diagramas",
    "04-uml/sequencia": "Diagramas de sequência por caso de uso",
    "04-uml/comunicacao": "Vínculos e mensagens numeradas entre objetos por caso de uso",
    "04-uml/tempo": "Estados ao longo do tempo, prazos e timeouts",
    "04-uml/visao-geral-interacao": "Jornada entre interações (refs para sequências)",
    "04-uml/estados": "Ciclo de vida das entidades",
    "04-uml/atividades": "Processos de negócio",
    "05-interface": "Design system, inventário de telas (TL) ligado ao Figma, navegação",
    "06-banco-de-dados": "Diagrama ER, dicionário, índices, consultas críticas, cargas, LGPD, migrações",
    "07-arquitetura": "Stack, estrutura de pastas, módulos, segurança, operação, ADRs",
    "08-backlog": "Épicos (EP), histórias (HU) com critérios de aceite e estimativas, marcos",
    "09-plano-de-testes": "Estratégia e casos de teste (CT), homologação",
    "10-proposta-comercial": "Proposta para o cliente: escopo, cronograma, investimento, condições",
    "11-entrega": "Implantação, checklist de entrega, manual de operação",
    "00-mapa-do-codigo": "Projeto existente: stack, comandos, estrutura e arquivos-chave detectados (gerado por `prumo mapear`)",
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
        ctx["projeto_existente"] = ("\n" + renderizar(mapear.BLOCO_AGENTES, dict(ctx, mapa=mapear.MAPA))) if c.get("existente") else ""
        ctx["lista_documentos"] = _lista_documentos(c.get("documentos") or [])
        ctx["lista_skills"] = _lista_skills(self.skills_do_kit())
        ctx["convencoes"] = renderizar(ler(TEMPLATES / "perfis" / "convencoes" / perfil["convencoes"]), ctx).strip()
        extras = mapear.convencoes_das_ferramentas(c.get("ferramentas") or [])
        if extras:
            ctx["convencoes"] += "\n\n### Ferramentas da stack deste projeto\n\n" + extras
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

    def instalar_kit_agentes(self, incluir_settings=True, sobrescrever=True, forcar=False):
        """Copia skills, subagentes, hooks e instruções do kit para o projeto. Retorna os arquivos escritos.

        Nunca perde trabalho do usuário: o Prumo guarda em .prumo/kit.json o hash do que gravou. Arquivo que o
        usuário editou depois disso fica como está e a versão nova vai para .prumo/kit-novo/ (lista em
        self.kit_preservados). Com forcar=True o arquivo é sobrescrito, mas antes copiado para .prumo/backup/.
        """
        ctx = self.contexto()
        base = TEMPLATES / "agentes"
        arquivo_manifesto = self.raiz / ".prumo" / "kit.json"
        manifesto = ler_json(arquivo_manifesto, {}) if arquivo_manifesto.exists() else {}
        if not isinstance(manifesto, dict):
            manifesto = {}
        escritos, self.kit_preservados, self.kit_backups = [], [], []
        backup = f"backup/{carimbo()}"

        def escrever(destino, texto, forcar_escrita=sobrescrever):
            rel = destino
            destino = self.raiz / destino
            novo_hash = hash_texto(texto)
            if destino.exists():
                if not forcar_escrita:
                    return
                atual = hash_conteudo(destino)
                if atual == novo_hash:
                    manifesto[rel] = novo_hash
                    return
                if atual != manifesto.get(rel):  # editado pelo usuário (ou de antes do manifesto)
                    if not forcar:
                        gravar(self.raiz / ".prumo" / "kit-novo" / rel, texto)
                        self.kit_preservados.append(rel)
                        return
                    self.kit_backups.append(guardar_copia(self.raiz, rel, backup))
            gravar(destino, texto)
            manifesto[rel] = novo_hash
            escritos.append(rel)

        for skill in self.skills_do_kit():
            escrever(f".claude/skills/{skill.name}/SKILL.md", renderizar(ler(skill / "SKILL.md"), ctx))
        for agente in sorted((base / "claude" / "agents").glob("*.md")):
            escrever(f".claude/agents/{agente.name}", renderizar(ler(agente), ctx))
        # Hooks importam prumo_comum.py: atualizam juntos ou nenhum (versões misturadas quebrariam as guardas).
        hooks = [(f".claude/hooks/{h.name}", ler(h)) for h in sorted((base / "claude" / "hooks").glob("*.py"))]

        def editado(rel, texto):
            destino = self.raiz / rel
            if not destino.exists():
                return False
            atual = hash_conteudo(destino)
            return atual != hash_texto(texto) and atual != manifesto.get(rel)

        algum_editado = sobrescrever and not forcar and any(editado(rel, texto) for rel, texto in hooks)
        for rel, texto in hooks:
            destino = self.raiz / rel
            if algum_editado and destino.exists() and hash_conteudo(destino) != hash_texto(texto):
                gravar(self.raiz / ".prumo" / "kit-novo" / rel, texto)
                self.kit_preservados.append(rel)
            elif not algum_editado or not destino.exists():
                escrever(rel, texto)
        if incluir_settings:
            escrever(".claude/settings.json", self.settings_claude())
        if self.figma_ativo():
            escrever(".mcp.json", ler(base / "mcp.json"), forcar_escrita=False)
        gravar_json(arquivo_manifesto, manifesto)
        return escritos

    def listar_kit(self):
        """Arquivos do kit do Claude neste projeto, com descrição e se diferem do modelo do Prumo."""
        ctx = self.contexto()
        base = TEMPLATES / "agentes"
        eventos = {}
        try:
            settings = json.loads(ler(self.raiz / ".claude" / "settings.json"))
            for evento, grupos in (settings.get("hooks") or {}).items():
                for grupo in grupos:
                    for h in grupo.get("hooks", []):
                        m = re.search(r"hooks[/\\](\w+)\.py|\bhook\s+(\w+)", h.get("command", ""))
                        if m:
                            nome = m.group(1) or m.group(2)
                            rotulo = evento + (f" ({grupo['matcher']})" if grupo.get("matcher") else "")
                            eventos.setdefault(nome, []).append(rotulo)
        except (FileNotFoundError, json.JSONDecodeError, ErroPrumo):
            pass

        itens = []

        def item(tipo, nome, rel, modelo_texto, descricao=""):
            arq = self.raiz / rel
            if not arq.exists():
                estado = "ausente"
            elif modelo_texto is None:
                estado = "próprio"
            else:
                estado = "igual ao kit" if ler(arq).replace("\r\n", "\n") == modelo_texto else "modificado"
            if arq.exists() and not descricao and rel.endswith(".md"):
                descricao = _frontmatter(ler(arq)).get("description", "")
            itens.append({"tipo": tipo, "nome": nome, "arquivo": rel, "estado": estado, "descricao": descricao,
                          "eventos": eventos.get(nome, []) if tipo == "hook" else []})

        modelos = {}
        for skill in self.skills_do_kit():
            texto = renderizar(ler(skill / "SKILL.md"), ctx)
            modelos[f".claude/skills/{skill.name}/SKILL.md"] = ("skill", skill.name, texto)
        for agente in sorted((base / "claude" / "agents").glob("*.md")):
            modelos[f".claude/agents/{agente.name}"] = ("subagente", agente.stem, renderizar(ler(agente), ctx))
        for hook in sorted((base / "claude" / "hooks").glob("*.py")):
            texto = ler(hook)
            doc = re.match(r'\s*"""(.*?)"""', texto, flags=re.S)
            modelos[f".claude/hooks/{hook.name}"] = ("hook", hook.stem, texto, doc.group(1).strip().split("\n")[0] if doc else "")
        for rel, dados in modelos.items():
            item(dados[0], dados[1], rel, dados[2], dados[3] if len(dados) > 3 else "")
        # arquivos criados no próprio projeto (skills, subagentes ou hooks a mais)
        for padrao, tipo in ((".claude/skills/*/SKILL.md", "skill"), (".claude/agents/*.md", "subagente"), (".claude/hooks/*.py", "hook")):
            for arq in sorted(self.raiz.glob(padrao)):
                rel = self.rel(arq)
                if rel not in modelos:
                    nome = arq.parent.name if tipo == "skill" else arq.stem
                    item(tipo, nome, rel, None)
        # num projeto mapeado, se o cliente já tinha CLAUDE.md/AGENTS.md, a versão do Prumo fica em *.prumo.md
        lado = lambda nome: nome.replace(".md", ".prumo.md") if (self.raiz / nome.replace(".md", ".prumo.md")).exists() else nome
        item("instruções", lado("CLAUDE.md"), lado("CLAUDE.md"), renderizar(ler(base / "CLAUDE.md"), ctx), "Instruções que o Claude Code lê em toda sessão")
        item("instruções", lado("AGENTS.md"), lado("AGENTS.md"), renderizar(ler(base / "AGENTS.md"), ctx), "Regras do projeto para qualquer agente de IA")
        item("configuração", "settings.json", ".claude/settings.json", self.settings_claude(), "Permissões e ligação dos hooks aos eventos do Claude Code")
        return itens


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
        primeira = re.sub(r"\s*\([^()]{40,}\)", "", primeira)  # enumerações longas ficam só na skill (AGENTS.md é lido sempre)
        linhas.append(f"| `{skill.name}` | {primeira}. | `.claude/skills/{skill.name}/SKILL.md` |")
    return "\n".join(linhas)


# ---------------------------------------------------------------- criação

def criar_projeto(destino, perfil_id, nome=None, cliente="", stack=None, autor=None, figma=None,
                  figma_url="", git=True, python=None, hooks_absolutos=False, hooks_via=None, forcar=False,
                  comandos=None, existente=False, pastas_codigo=None, ferramentas=None):
    """Cria o projeto. Com existente=True (prumo mapear), não sobrescreve nenhum arquivo que já esteja na pasta."""
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
    # Stack fora do perfil: os comandos sugeridos vêm das ferramentas citadas no texto (Go, Rust, Elixir...).
    if ferramentas is None:
        ferramentas = mapear.ferramentas_da_stack(stack) if stack and stack != perfil["stack"] else []
    sugeridos = perfil.get("comandos_sugeridos", {})
    if ferramentas and not existente:
        sugeridos = mapear.comandos_das_ferramentas(ferramentas)
    if existente:
        documentos.insert(0, mapear.MAPA)

    existia = destino.exists()
    vazia = not existia or not any(destino.iterdir())
    try:
        return _criar(destino, perfil, freelancer, nome, cliente, stack, autor, usar_figma, figma_url, documentos,
                      git, python, hooks_absolutos, hooks_via, comandos=comandos, existente=existente,
                      pastas_codigo=pastas_codigo, ferramentas=ferramentas, sugeridos=sugeridos)
    except BaseException:
        # Criação interrompida (erro, Ctrl+C): numa pasta que era nova/vazia, não deixa projeto pela metade.
        if vazia and destino.exists():
            if existia:
                for item in destino.iterdir():
                    shutil.rmtree(item, ignore_errors=True) if item.is_dir() else item.unlink()
            else:
                shutil.rmtree(destino, ignore_errors=True)
        raise


def _criar(destino, perfil, freelancer, nome, cliente, stack, autor, usar_figma, figma_url, documentos,
           git, python, hooks_absolutos, hooks_via, comandos=None, existente=False, pastas_codigo=None,
           ferramentas=(), sugeridos=None):
    backup = f"backup/{carimbo()}"

    def gravar(caminho, texto):
        """Em pasta já existente (--forcar), guarda uma cópia de qualquer arquivo do usuário antes de trocá-lo."""
        caminho = Path(caminho)
        if caminho.is_file() and caminho.read_bytes().replace(b"\r\n", b"\n") != texto.encode("utf-8"):
            copia = guardar_copia(destino, caminho.relative_to(destino).as_posix(), backup)
            aviso(f"{caminho.name} já existia; cópia guardada em {copia}.")
        _gravar(caminho, texto)

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
        "comandos": {"formatar": "", "lint": "", "testar": "", **(comandos or {})},
        "comandos_sugeridos": sugeridos,
        "ferramentas": ferramentas,
        "existente": bool(existente),
        "hooks": {
            "registrar_horas": True, "testes_ao_parar": False, "comandos_permitidos": [],
            "revisao_pos_mudanca": True, "limite_arquivos": 3, "limite_linhas": 80, "caminhos_sensiveis": [],
            "extensoes_lint": perfil.get("extensoes_lint") or [],
        },
        "pastas_codigo": pastas_codigo or perfil.get("pastas") or ["src", "tests"],
        "figma": {"ativo": usar_figma, "arquivo": figma_url, "telas": {}},
        "orcamento": {"valor_hora": None, "contingencia_percentual": None},
        "claude": {"modelo": "", "max_turnos": None, "ferramentas_extras": []},
    }
    gravar_json(destino / ARQUIVO_PROJETO, config)
    projeto = Projeto(destino)
    ctx = projeto.contexto()

    def novo_arquivo(rel, texto):
        """Grava só se não existir (num projeto existente, nada do cliente é sobrescrito)."""
        alvo = destino / rel
        if existente and alvo.exists():
            pulados.append(rel)
            return False
        gravar(alvo, texto)
        escritos.append(rel)
        return True

    escritos, pulados = [], []
    for doc in perfil["documentos"]:
        texto = renderizar(ler(TEMPLATES / "documentos" / f"{doc}.md"), ctx)
        if doc == "05-interface" and figma_url:
            texto = texto.replace("| Arquivo do Figma | [PREENCHER: URL] |", f"| Arquivo do Figma | {figma_url} |")
        novo_arquivo(f"docs/{doc}.md", texto)
    for pasta, modelo, prefixo in (("adr", "adr", "ADR"), ("mudancas", "mudanca", "CM")):
        ctx_modelo = dict(ctx, id=f"{prefixo}-NNN", titulo="Título")
        novo_arquivo(f"docs/{pasta}/_modelo.md", renderizar(ler(TEMPLATES / "documentos" / f"{modelo}.md"), ctx_modelo))

    _limpar_exemplos_orfaos(projeto, [destino / r for r in escritos if r.startswith("docs/")])
    from .geracao import selar_arquivo
    for rel in escritos:
        if rel.startswith("docs/"):
            selar_arquivo(destino / rel)  # hash dos blocos prumo:gerado: `prumo gerar` sabe que ninguém mexeu
    base = TEMPLATES / "agentes"
    agentes = renderizar(ler(base / "AGENTS.md"), ctx)
    if existente:
        for arq, texto in (("AGENTS.md", agentes), ("CLAUDE.md", renderizar(ler(base / "CLAUDE.md"), ctx))):
            if novo_arquivo(arq, texto):
                continue
            # O arquivo do cliente fica intacto; o do Prumo vai ao lado e é importado num bloco no fim.
            lado = arq.replace(".md", ".prumo.md")
            gravar(destino / lado, texto)
            mapear.mesclar_bloco(destino / arq, f"## Prumo\n\n@{lado}")
            escritos.append(lado)
        mapear.mesclar_bloco(destino / ".gitignore", ler(base / "gitignore"))
    else:
        gravar(destino / "AGENTS.md", agentes)
        gravar(destino / "CLAUDE.md", renderizar(ler(base / "CLAUDE.md"), ctx))
        gravar(destino / ".gitignore", ler(base / "gitignore"))
    novo_arquivo("README.md", renderizar(ler(base / "README.md"), ctx))
    if not (destino / ".env.example").exists():
        gravar(destino / ".env.example", "# Variáveis de ambiente do projeto (sem valores reais). Copie para .env.\n")
    projeto.instalar_kit_agentes(incluir_settings=not existente)
    if projeto.kit_preservados:
        aviso(f"{len(projeto.kit_preservados)} arquivo(s) do kit já existiam e foram mantidos; "
              "a versão do Prumo está em .prumo/kit-novo/.")
    if existente:
        mapear.mesclar_settings(destino / ".claude" / "settings.json", projeto.settings_claude())
        projeto.pulados = pulados
        return projeto
    for pasta in config["pastas_codigo"]:
        (destino / pasta).mkdir(parents=True, exist_ok=True)
        gravar(destino / pasta / ".gitkeep", "")

    if git and shutil.which("git") and not (destino / ".git").exists():
        _git_inicial(destino, nome)
    return projeto


def _limpar_exemplos_orfaos(projeto, arquivos=None):
    """Nos modelos, exemplos citam IDs de documentos que o perfil pode não ter (ex.: UC-001 no perfil mínimo).
    Só mexe nos arquivos que o Prumo acabou de gravar (num projeto existente, os docs do cliente ficam intactos)."""
    from . import rastreio
    orfaos = set(rastreio.analisar_projeto(projeto).indefinidos())
    if not orfaos:
        return
    padrao = re.compile(r"\b(" + "|".join(re.escape(o) for o in orfaos) + r")\b")
    for arq in (projeto.arquivos_docs() if arquivos is None else arquivos):
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
    from .geracao import selar
    gravar(destino, selar(renderizar(ler(TEMPLATES / "documentos" / f"{doc_id}.md"), projeto.contexto())))
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
    info("  2. Preencha a aba Formulário da interface (ou cole as anotações do cliente em docs/00-briefing.md).")
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
