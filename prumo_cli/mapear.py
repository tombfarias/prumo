"""Projetos que já existem: detecta a stack pelo código e instala o Prumo sem sobrescrever nada do cliente."""

import fnmatch
import json
import os
import re
from pathlib import Path

from .util import ARQUIVO_PROJETO, TEMPLATES, ErroPrumo, aviso, gravar, hoje_br, ler, ler_json, tabela_markdown

MAPA = "docs/00-mapa-do-codigo.md"
LIMITE_ARQUIVOS = 30000
IGNORAR_PASTAS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "out", "target", "coverage", ".next", ".nuxt",
    ".svelte-kit", ".astro", ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".tox", ".gradle", ".idea", ".vscode", ".dart_tool", "Pods", "bin", "obj", ".terraform", ".cache", ".turbo",
    ".expo", "deps", "_build", ".prumo", ".claude",
}
NAO_CODIGO = {"docs", "doc", "public", "static", "assets", ".github", ".gitlab", "scripts"}
LINGUAGENS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro",
    ".php": "PHP", ".rb": "Ruby", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".cs": "C#",
    ".fs": "F#", ".swift": "Swift", ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir", ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".hpp": "C++", ".scala": "Scala", ".lua": "Lua", ".r": "R",
    ".html": "HTML", ".css": "CSS", ".scss": "CSS", ".sql": "SQL", ".sh": "Shell", ".ps1": "PowerShell",
}
# dependência -> (id no catálogo de stacks do formulário ou nome livre, camada)
FRAMEWORKS_NODE = {
    "next": ("nextjs", "web"), "nuxt": ("nuxt", "web"), "astro": ("astro", "site"), "@sveltejs/kit": ("SvelteKit", "web"),
    "@remix-run/react": ("Remix", "web"), "@angular/core": ("Angular", "frontend"), "vue": ("Vue", "frontend"),
    "react": ("react-vite", "frontend"), "svelte": ("Svelte", "frontend"), "expo": ("expo", "mobile"),
    "react-native": ("React Native", "mobile"), "electron": ("Electron", "desktop"),
    "express": ("express", "backend"), "fastify": ("fastify", "backend"), "@nestjs/core": ("nestjs", "backend"),
    "koa": ("Koa", "backend"), "hono": ("Hono", "backend"), "@supabase/supabase-js": ("supabase", "servico"),
    "firebase": ("firebase", "servico"), "prisma": ("prisma", "orm"), "@prisma/client": ("prisma", "orm"),
    "drizzle-orm": ("drizzle", "orm"), "typeorm": ("TypeORM", "orm"), "sequelize": ("Sequelize", "orm"),
    "mongoose": ("mongodb", "banco"), "pg": ("postgresql", "banco"), "mysql2": ("mysql", "banco"),
    "better-sqlite3": ("sqlite", "banco"), "vitest": ("vitest", "testes"), "jest": ("jest", "testes"),
    "@playwright/test": ("playwright", "testes"), "discord.js": ("Discord.js", "bot"), "telegraf": ("Telegraf", "bot"),
}
FRAMEWORKS_PY = {
    "django": ("django", "web"), "fastapi": ("fastapi", "backend"), "flask": ("Flask", "backend"),
    "sqlalchemy": ("sqlalchemy", "orm"), "alembic": ("sqlalchemy", "orm"), "psycopg": ("postgresql", "banco"),
    "psycopg2": ("postgresql", "banco"), "pymongo": ("mongodb", "banco"), "pytest": ("pytest", "testes"),
    "streamlit": ("Streamlit", "web"), "python-telegram-bot": ("python-telegram-bot", "bot"),
    "discord.py": ("discord.py", "bot"), "selenium": ("Selenium", "bot"), "playwright": ("Playwright (Python)", "bot"),
    "celery": ("Celery", "backend"),
}
FRAMEWORKS_PHP = {"laravel/framework": ("laravel", "web"), "symfony/framework-bundle": ("Symfony", "web"),
                  "phpunit/phpunit": ("phpunit", "testes")}
FRAMEWORKS_TEXTO = {  # manifestos sem dependências estruturadas: procura o nome no texto
    "Gemfile": {"rails": ("Ruby on Rails", "web"), "sinatra": ("Sinatra", "backend"), "rspec": ("RSpec", "testes")},
    "mix.exs": {":phoenix": ("Phoenix", "web"), ":ecto": ("Ecto", "orm")},
    "go.mod": {"gin-gonic/gin": ("Gin", "backend"), "labstack/echo": ("Echo", "backend"), "gofiber/fiber": ("Fiber", "backend"),
               "gorm.io": ("GORM", "orm")},
    "Cargo.toml": {"axum": ("Axum", "backend"), "actix-web": ("Actix Web", "backend"), "tauri": ("Tauri", "desktop"),
                   "diesel": ("Diesel", "orm"), "sqlx": ("SQLx", "orm")},
    "pom.xml": {"spring-boot": ("Spring Boot", "backend"), "quarkus": ("Quarkus", "backend")},
    "build.gradle": {"spring-boot": ("Spring Boot", "backend"), "com.android": ("Android", "mobile"), "ktor": ("Ktor", "backend")},
    "build.gradle.kts": {"spring-boot": ("Spring Boot", "backend"), "com.android": ("Android", "mobile"), "ktor": ("Ktor", "backend")},
    "pubspec.yaml": {"flutter:": ("flutter", "mobile")},
}
OFICIAIS = {"go", "rust", "elixir", "dart", "deno"}  # formatador/analisador oficial da linguagem
EXECUTOR_NODE = {"npm": "npx", "pnpm": "pnpm exec", "yarn": "yarn", "bun": "bunx"}
CHAVES_DOC = [  # (rótulo, padrões de caminho relativos, em minúsculas)
    ("Pontos de entrada", ["main.*", "index.*", "app.*", "server.*", "manage.py", "program.cs", "*/main.*", "src/main.*",
                           "src/index.*", "src/app.*", "src/server.*", "cmd/*/main.go", "lib/main.dart"]),
    ("Rotas e APIs", ["*routes*", "*router*", "*controllers*", "*/api/*", "*urls.py", "*handlers*", "*endpoints*"]),
    ("Modelos e banco", ["*models*", "*entities*", "*schema.prisma", "*migrations*", "*/db/*", "*schema.sql",
                         "*database*", "*drizzle*", "*repositories*"]),
    ("Telas e componentes", ["*/pages/*", "*/views/*", "*/screens/*", "*/components/*", "*/templates/*", "app/**/page.*"]),
    ("Testes", ["test/*", "tests/*", "__tests__/*", "*_test.*", "*.test.*", "*.spec.*", "spec/*", "e2e/*"]),
    ("Infraestrutura e CI", ["dockerfile", "docker-compose*", "compose.y*ml", ".github/workflows/*", ".gitlab-ci.yml",
                             "vercel.json", "netlify.toml", "fly.toml", "render.yaml", "railway.json", "procfile",
                             "*.tf", "k8s/*", "nginx*.conf"]),
    ("Configuração", [".env.example", ".env.sample", "*.config.*", "settings.py", "config/*", "appsettings*.json"]),
]


def _ferramentas():
    return ler_json(TEMPLATES / "catalogos" / "ferramentas.json", {}).get("itens", [])


def _stacks_catalogo():
    return {i["id"]: i for i in ler_json(TEMPLATES / "catalogos" / "stacks.json", {}).get("itens", [])}


def _palavra(texto, termo):
    return re.search(r"(?<![\w.#+])" + re.escape(termo) + r"(?![\w#+])", texto) is not None


def ferramentas_da_stack(texto):
    """IDs das ferramentas citadas no texto livre da stack, na ordem em que aparecem."""
    texto = (texto or "").lower()
    achadas = []
    for f in _ferramentas():
        posicoes = [texto.find(t) for t in f.get("palavras", []) if _palavra(texto, t)]
        if posicoes:
            achadas.append((min(posicoes), f["id"]))
    return [i for _p, i in sorted(achadas)]


def comandos_das_ferramentas(ids):
    """Para cada comando (formatar, lint, testar), o da primeira ferramenta que tiver um."""
    por_id = {f["id"]: f for f in _ferramentas()}
    saida = {"formatar": "", "lint": "", "testar": ""}
    for i in ids:
        for chave, cmd in (por_id.get(i, {}).get("comandos") or {}).items():
            if cmd and not saida.get(chave):
                saida[chave] = cmd
    return saida


def convencoes_das_ferramentas(ids):
    por_id = {f["id"]: f for f in _ferramentas()}
    linhas = []
    for i in ids:
        f = por_id.get(i)
        if not f:
            continue
        cmds = [f"{k}: `{v}`" for k, v in (f.get("comandos") or {}).items() if v]
        linha = f"- **{f['nome']}:** " + (f.get("convencao", "") + " " if f.get("convencao") else "")
        if cmds:
            linha += "Comandos de referência: " + ", ".join(cmds) + "."
        linhas.append(linha.rstrip())
    return "\n".join(linhas)


# ---------------------------------------------------------------- varredura

def _varrer(raiz):
    arquivos, pastas_topo, truncado = [], set(), False
    for atual, dirs, nomes in os.walk(raiz):
        dirs[:] = sorted(d for d in dirs if d not in IGNORAR_PASTAS and not d.endswith(".egg-info"))
        rel_atual = Path(atual).relative_to(raiz)
        if rel_atual == Path("."):
            pastas_topo.update(dirs)
        for n in sorted(nomes):
            arquivos.append((rel_atual / n).as_posix())
            if len(arquivos) >= LIMITE_ARQUIVOS:
                return arquivos, pastas_topo, True
    return arquivos, pastas_topo, truncado


def _ler_texto(caminho, limite=200_000):
    try:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            return f.read(limite)
    except OSError:
        return ""


def _deps_python(raiz):
    texto = " ".join(_ler_texto(raiz / n) for n in ("pyproject.toml", "requirements.txt", "requirements-dev.txt",
                                                      "setup.py", "setup.cfg", "Pipfile")).lower()
    nomes = set(re.findall(r"(?<![\w.-])([a-z0-9][a-z0-9_.-]*)\s*(?:[<>=!~\[;\"',]|$)", texto, flags=re.M))
    return nomes, texto


def detectar(pasta):
    """Lê a pasta (sem executar nada) e devolve linguagens, stack, comandos, pastas e arquivos-chave."""
    raiz = Path(pasta).resolve()
    if not raiz.is_dir():
        raise ErroPrumo(f"Pasta não encontrada: {raiz}")
    arquivos, pastas_topo, truncado = _varrer(raiz)
    nomes_raiz = {a for a in arquivos if "/" not in a}

    contagem = {}
    pastas_com_codigo = set()
    for a in arquivos:
        ling = LINGUAGENS.get(Path(a).suffix.lower())
        if ling:
            contagem[ling] = contagem.get(ling, 0) + 1
            if "/" in a and ling not in ("HTML", "CSS", "SQL", "Shell", "PowerShell"):
                pastas_com_codigo.add(a.split("/", 1)[0])
    linguagens = sorted(contagem.items(), key=lambda x: -x[1])

    ferramentas = []
    for f in _ferramentas():
        if any(fnmatch.fnmatch(n, m) for m in f.get("marcadores", []) for n in nomes_raiz):
            ferramentas.append(f["id"])

    frameworks = {}  # nome/id -> camada

    def achou(par):
        frameworks.setdefault(par[0], par[1])

    gerenciador = ""
    comandos = {"formatar": "", "lint": "", "testar": ""}
    scripts = {}
    pacote = ler_json(raiz / "package.json", None) if "package.json" in nomes_raiz else None
    if isinstance(pacote, dict):
        deps = {**(pacote.get("dependencies") or {}), **(pacote.get("devDependencies") or {})}
        for dep, par in FRAMEWORKS_NODE.items():
            if dep in deps:
                achou(par)
        if "react" in deps and any(k in deps for k in ("next", "expo", "react-native", "@remix-run/react")):
            frameworks.pop("react-vite", None)
        if "vue" in deps and "nuxt" in deps:
            frameworks.pop("Vue", None)
        gerenciador = next((g for arq, g in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun"),
                                             ("bun.lock", "bun")) if arq in nomes_raiz), "npm")
        exe = EXECUTOR_NODE[gerenciador]
        scripts = pacote.get("scripts") or {}
        rodar = "npm run" if gerenciador == "npm" else gerenciador
        if "@biomejs/biome" in deps:
            comandos["formatar"] = f"{exe} biome format --write {{arquivo}}"
            comandos["lint"] = f"{exe} biome lint {{arquivo}}"
        if "prettier" in deps:
            comandos["formatar"] = f"{exe} prettier --write {{arquivo}}"
        if "eslint" in deps:
            comandos["lint"] = f"{exe} eslint {{arquivo}}"
        if "test" in scripts and "no test specified" not in str(scripts["test"]):
            comandos["testar"] = "npm test" if gerenciador == "npm" else f"{gerenciador} test"
        elif "vitest" in deps:
            comandos["testar"] = f"{exe} vitest run"
        elif "jest" in deps:
            comandos["testar"] = f"{exe} jest"
        if not comandos["lint"] and "lint" in scripts:
            comandos["lint"] = f"{rodar} lint"

    if "python" in ferramentas or "manage.py" in nomes_raiz:
        if "python" not in ferramentas:
            ferramentas.append("python")
        deps_py, texto_py = _deps_python(raiz)
        for dep, par in FRAMEWORKS_PY.items():
            if dep in deps_py:
                achou(par)
        if "manage.py" in nomes_raiz:
            achou(FRAMEWORKS_PY["django"])
        prefixo = "uv run " if "uv.lock" in nomes_raiz else ("poetry run " if "poetry.lock" in nomes_raiz else "")
        gerenciador = gerenciador or ("uv" if prefixo.startswith("uv") else "poetry" if prefixo else "pip")
        if "ruff" in deps_py or "[tool.ruff" in texto_py or "ruff.toml" in nomes_raiz:
            comandos["formatar"] = comandos["formatar"] or f"{prefixo}ruff format {{arquivo}}"
            comandos["lint"] = comandos["lint"] or f"{prefixo}ruff check {{arquivo}}"
        elif "black" in deps_py:
            comandos["formatar"] = comandos["formatar"] or f"{prefixo}black -q {{arquivo}}"
        if not comandos["lint"] and "flake8" in deps_py:
            comandos["lint"] = f"{prefixo}flake8 {{arquivo}}"
        if not comandos["testar"]:
            if "pytest" in deps_py or "[tool.pytest" in texto_py or "pytest.ini" in nomes_raiz:
                comandos["testar"] = f"{prefixo}pytest -q"
            elif "manage.py" in nomes_raiz:
                comandos["testar"] = f"{prefixo}python manage.py test"
            elif "tests" in pastas_topo:
                comandos["testar"] = f"{prefixo}python -m pytest -q"

    if "composer.json" in nomes_raiz:
        comp = ler_json(raiz / "composer.json", {}) or {}
        deps = {**(comp.get("require") or {}), **(comp.get("require-dev") or {})}
        for dep, par in FRAMEWORKS_PHP.items():
            if dep in deps:
                achou(par)
        gerenciador = gerenciador or "composer"
        if "laravel/pint" in deps:
            comandos["formatar"] = comandos["formatar"] or "./vendor/bin/pint {arquivo}"
        if "laravel" in frameworks:
            comandos["testar"] = comandos["testar"] or "php artisan test"
    if "wp-config.php" in nomes_raiz or "wp-content" in pastas_topo or any(a.endswith("/style.css") and "wp-content/themes/" in a for a in arquivos[:5000]):
        achou(("wordpress", "site"))

    for manifesto, mapa in FRAMEWORKS_TEXTO.items():
        if manifesto in nomes_raiz:
            texto = _ler_texto(raiz / manifesto).lower()
            for termo, par in mapa.items():
                if termo in texto:
                    achou(par)

    # O que os manifestos não disseram sai do catálogo: o teste padrão da linguagem e, só nas linguagens com
    # formatador oficial, formatar/lint. Num projeto existente não se impõe um formatador que ele não usa.
    analisadas = {"node", "python", "php"}
    for f in ferramentas:
        padrao = comandos_das_ferramentas([f])
        for chave in comandos:
            if comandos[chave] or not padrao[chave] or f in analisadas:
                continue
            if chave == "testar" or f in OFICIAIS:
                comandos[chave] = padrao[chave]
    if "Makefile" in nomes_raiz and not comandos["testar"]:
        if re.search(r"^test:", _ler_texto(raiz / "Makefile"), flags=re.M):
            comandos["testar"] = "make test"

    pastas_codigo = sorted(p for p in pastas_com_codigo if p not in NAO_CODIGO and p in pastas_topo) or ["."]
    chave = {rot: [] for rot, _ in CHAVES_DOC}
    for a in arquivos:
        baixo = a.lower()
        for rot, padroes in CHAVES_DOC:
            if len(chave[rot]) < 15 and any(fnmatch.fnmatch(baixo, p) for p in padroes):
                if rot in ("Rotas e APIs", "Modelos e banco", "Telas e componentes") and not Path(a).suffix.lower() in LINGUAGENS \
                        and not baixo.endswith(".prisma"):
                    continue
                chave[rot].append(a)
                break

    resultado = {
        "pasta": str(raiz),
        "nome": raiz.name,
        "arquivos": len(arquivos),
        "truncado": truncado,
        "linguagens": [{"linguagem": l, "arquivos": n} for l, n in linguagens],
        "ferramentas": ferramentas,
        "frameworks": [{"nome": _nome_stack(k), "id": k, "camada": c} for k, c in frameworks.items()],
        "gerenciador": gerenciador,
        "scripts": {k: str(v) for k, v in list(scripts.items())[:20]},
        "comandos": comandos,
        "pastas_topo": sorted(pastas_topo),
        "pastas_codigo": pastas_codigo,
        "arquivos_chave": {k: v for k, v in chave.items() if v},
        "git": (raiz / ".git").exists(),
        "ja_e_prumo": (raiz / ARQUIVO_PROJETO).exists(),
    }
    resultado["stack"] = texto_stack(resultado)
    resultado["perfil"] = perfil_sugerido(resultado)
    return resultado


def _nome_stack(ident):
    item = _stacks_catalogo().get(ident)
    return item["nome"] if item else ident


def texto_stack(det):
    nomes = [f["nome"] for f in det["frameworks"] if f["camada"] != "testes"]
    if not nomes:
        nomes = [l["linguagem"] for l in det["linguagens"][:3] if l["linguagem"] not in ("HTML", "CSS", "Shell", "SQL")]
    if not nomes and det["linguagens"]:
        nomes = [det["linguagens"][0]["linguagem"]]
    principal = next((l["linguagem"] for l in det["linguagens"] if l["linguagem"] not in ("HTML", "CSS", "Shell", "SQL")), "")
    if principal and principal.lower() not in " ".join(nomes).lower():
        nomes.insert(0, principal)
    return " + ".join(dict.fromkeys(nomes)) or "[PREENCHER: stack não detectada]"


def perfil_sugerido(det):
    camadas = {f["camada"] for f in det["frameworks"]}
    if "mobile" in camadas:
        return "app-mobile"
    if "site" in camadas and not camadas & {"backend", "web", "orm", "banco"}:
        return "site-institucional"
    if "web" in camadas or ({"frontend", "backend"} <= camadas):
        return "web-fullstack"
    if "backend" in camadas or "orm" in camadas:
        return "api-rest"
    if "bot" in camadas:
        return "automacao-bot"
    if "frontend" in camadas:
        return "site-institucional"
    langs = {l["linguagem"] for l in det["linguagens"]}
    if langs and langs <= {"HTML", "CSS", "JavaScript"}:
        return "site-institucional"
    if det["ferramentas"]:
        return "automacao-bot" if det["ferramentas"][0] == "python" else "minimo"
    return "minimo"


# ---------------------------------------------------------------- documento do mapa

def arvore(raiz, profundidade=2, limite=60):
    raiz = Path(raiz)
    linhas = []

    def andar(pasta, nivel):
        try:
            itens = sorted(pasta.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return
        for p in itens:
            if len(linhas) >= limite:
                return
            if p.name in IGNORAR_PASTAS or (p.name.startswith(".") and p.name not in (".github",)):
                continue
            if p.is_dir():
                linhas.append("  " * nivel + p.name + "/")
                if nivel + 1 < profundidade:
                    andar(p, nivel + 1)
            elif nivel == 0:
                linhas.append(p.name)

    andar(raiz, 0)
    if len(linhas) >= limite:
        linhas.append("...")
    return "\n".join(linhas)


def texto_mapa(det, prumo="prumo"):
    raiz = Path(det["pasta"])
    p = [
        "# Mapa do código",
        "",
        f"> Gerado pelo Prumo em {hoje_br()} a partir do código que já existia (nada foi executado). Não edite: rode "
        f"`{prumo} mapear --atualizar` para refazer. A especificação em `docs/` descreve o sistema como ele é hoje; "
        "o procedimento está na skill `mapear-projeto-existente`.",
        "",
        "## Resumo",
        "",
        tabela_markdown(["", ""], [
            ["Stack detectada", det["stack"]],
            ["Perfil sugerido", det["perfil"]],
            ["Gerenciador de pacotes", det["gerenciador"] or "—"],
            ["Arquivos lidos", f"{det['arquivos']}{' (limite atingido)' if det['truncado'] else ''}"],
            ["Pastas de código", ", ".join(f"`{x}`" for x in det["pastas_codigo"])],
            ["Git", "sim" if det["git"] else "não"],
        ]),
        "",
        "## Linguagens",
        "",
        tabela_markdown(["Linguagem", "Arquivos"], [[l["linguagem"], l["arquivos"]] for l in det["linguagens"][:12]])
        if det["linguagens"] else "Nenhum arquivo de código reconhecido.",
        "",
        "## Frameworks e bibliotecas",
        "",
        tabela_markdown(["Item", "Camada"], [[f["nome"], f["camada"]] for f in det["frameworks"]])
        if det["frameworks"] else "Nenhum reconhecido pelos manifestos (package.json, pyproject.toml, composer.json...).",
        "",
        "## Comandos usados pelos hooks",
        "",
        "Detectados pelos manifestos e gravados em `projeto.prumo.json` → `comandos`. Confira se rodam na sua máquina.",
        "",
        tabela_markdown(["Uso", "Comando"], [[k, f"`{v}`" if v else "—"] for k, v in det["comandos"].items()]),
        "",
    ]
    if det["scripts"]:
        p += ["Scripts do `package.json`: " + ", ".join(f"`{k}`" for k in det["scripts"]) + ".", ""]
    p += ["## Estrutura", "", "```text", arvore(raiz) or "(vazia)", "```", "", "## Arquivos-chave", ""]
    if det["arquivos_chave"]:
        for rot, lista in det["arquivos_chave"].items():
            p.append(f"- **{rot}:** " + ", ".join(f"`{a}`" for a in lista))
    else:
        p.append("Nenhum reconhecido.")
    p += ["", "## Por onde começar a leitura", "",
          "1. Manifestos e configuração (acima) para confirmar a stack.",
          "2. Modelos e migrações → `docs/06-banco-de-dados.md` e `docs/04-uml/classes.md`.",
          "3. Rotas, telas e testes → requisitos (RF), casos de uso (UC) e telas (TL).",
          "4. Infraestrutura → `docs/07-arquitetura.md` e `docs/04-uml/implantacao.md`.", ""]
    return "\n".join(p)


# ---------------------------------------------------------------- mesclas sem sobrescrever

INICIO, FIM = "<!-- prumo:inicio -->", "<!-- prumo:fim -->"


def mesclar_bloco(caminho, bloco):
    """Acrescenta (ou atualiza) um bloco entre marcadores no fim de um arquivo do cliente, sem mexer no resto."""
    caminho = Path(caminho)
    novo = f"{INICIO}\n{bloco.strip()}\n{FIM}\n"
    if not caminho.exists():
        gravar(caminho, novo)
        return "criado"
    texto = ler(caminho)
    if INICIO in texto and FIM in texto:
        antes, resto = texto.split(INICIO, 1)
        depois = resto.split(FIM, 1)[1].lstrip("\n")
        gravar(caminho, antes + novo + depois)
        return "atualizado"
    gravar(caminho, texto.rstrip("\n") + "\n\n" + novo)
    return "acrescentado"


def mesclar_settings(caminho, gerado):
    """Junta as permissões e os hooks do Prumo ao settings.json que o projeto já tinha."""
    caminho = Path(caminho)
    novo = json.loads(gerado)
    if not caminho.exists():
        gravar(caminho, gerado)
        return "criado"
    try:
        atual = json.loads(ler(caminho))
    except ValueError:
        alternativo = caminho.with_name("settings.prumo.json")
        gravar(alternativo, gerado)
        aviso(f"{caminho.name} não é um JSON válido; as configurações do Prumo foram para {alternativo.name}.")
        return "separado"
    perm = atual.setdefault("permissions", {})
    for tipo, lista in (novo.get("permissions") or {}).items():
        existentes = perm.setdefault(tipo, [])
        existentes += [x for x in lista if x not in existentes]
    hooks = atual.setdefault("hooks", {})
    for evento, grupos in (novo.get("hooks") or {}).items():
        lista = hooks.setdefault(evento, [])
        ja = json.dumps(lista)
        lista += [g for g in grupos if not all(h["command"] in ja for h in g.get("hooks", []))]
    gravar(caminho, json.dumps(atual, ensure_ascii=False, indent=2) + "\n")
    return "mesclado"


# ---------------------------------------------------------------- instalação no projeto existente

BLOCO_AGENTES = """## Projeto existente (mapeado pelo Prumo)

- O código já existia quando o Prumo foi instalado. O mapa da stack, dos comandos e dos arquivos-chave está em `{mapa}`.
- Primeiro passo: `/mapear-projeto-existente` (ou `{prumo} claude mapear`) para descrever em `docs/` o sistema **como ele é hoje**, citando o arquivo de onde cada item saiu.
- Até a especificação estar revisada, **não altere código**. Depois, pedidos novos do cliente viram histórias (HU) ou registros de mudança (`{prumo} mudanca "título"`).
- Siga as convenções que o código já usa (nomes, pastas, estilo, bibliotecas), mesmo que a stack do perfil sugira outra.
"""


def mapear_projeto(pasta, perfil_id=None, nome=None, cliente="", stack=None, autor=None, comandos=None,
                   python=None, hooks_via=None, figma=None):
    """Instala o Prumo num projeto que já tem código: detecta, cria só o que falta e mescla o resto."""
    from . import projeto as mp
    from .util import comando_prumo

    raiz = Path(pasta).resolve()
    det = detectar(raiz)
    if det["ja_e_prumo"]:
        return atualizar_mapa(mp.Projeto(raiz), det)
    perfil_id = perfil_id or det["perfil"]
    cmds = dict(det["comandos"])
    cmds.update({k: v for k, v in (comandos or {}).items() if v is not None})
    projeto = mp.criar_projeto(
        raiz, perfil_id, nome=nome or det["nome"], cliente=cliente, stack=stack or det["stack"], autor=autor,
        figma=figma, git=False, python=python, hooks_via=hooks_via, forcar=True, existente=True,
        comandos=cmds, pastas_codigo=det["pastas_codigo"], ferramentas=det["ferramentas"],
    )
    projeto.config["mapeamento"] = _resumo_mapeamento(det)
    projeto.salvar()
    gravar(raiz / MAPA, texto_mapa(det, comando_prumo(projeto.config.get("python"))))
    return projeto, det


def atualizar_mapa(projeto, det=None):
    from .util import comando_prumo
    det = det or detectar(projeto.raiz)
    projeto.config["mapeamento"] = _resumo_mapeamento(det)
    atuais = projeto.config.setdefault("comandos", {})
    for k, v in det["comandos"].items():
        if v and not atuais.get(k):
            atuais[k] = v
    projeto.salvar()
    gravar(projeto.raiz / MAPA, texto_mapa(det, comando_prumo(projeto.config.get("python"))))
    return projeto, det


def _resumo_mapeamento(det):
    from .util import agora_iso
    return {"em": agora_iso(), "stack": det["stack"], "perfil_sugerido": det["perfil"],
            "ferramentas": det["ferramentas"], "gerenciador": det["gerenciador"], "arquivos": det["arquivos"]}
