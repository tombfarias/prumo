# Prumo — instruções para desenvolver o próprio Prumo

O Prumo é um kit em Python (só biblioteca padrão, 3.9+) que cria e mantém projetos freelance com especificação,
rastreabilidade e um kit de agentes (skills, subagentes, hooks) para o Claude Code. Visão geral em `docs/arquitetura-do-prumo.md`.

## Mapa

- `prumo_cli/` — CLI (`cli.py`), criação de projetos (`projeto.py`), rastreabilidade (`rastreio.py`), validação e
  contexto (`validacao.py`), orçamento/horas/exportação (`gestao.py`), Figma (`figma.py`), segurança (`seguranca.py`),
  formulário de especificação (`formulario.py`, desenho em `docs/formulario-de-especificacao.md`),
  ponte com o Claude Code (`claude.py`), servidor da interface (`servidor.py`) e a interface (`gui/index.html`, HTML/CSS/JS puro,
  com o `mermaid.min.js` embutido para desenhar diagramas).
- `templates/documentos/` — modelos de especificação; `templates/perfis/` — perfis e convenções por stack;
  `templates/catalogos/` — opções do formulário (stacks, integrações, logins, RNFs, tipos de campo) e o que cada uma implica;
  `templates/agentes/` — AGENTS.md, CLAUDE.md, skills, subagentes, hooks e settings copiados para cada projeto.
- `.githooks/` — guarda de privacidade (`privacidade.py`) usado pelos hooks do git (instalados em `.git/hooks`), pelo hook do Claude (`.claude/settings.json`) e pelo CI.
- `tools/cores.py` — verifica a paleta da interface (contraste WCAG e daltonismo); roda nos testes.
- `powershell/` — módulo `Prumo.psm1` e instalador. `build.ps1` — executáveis. `.github/workflows/ci.yml` — testes e build.

## Regras

- **O repositório é público (licença MIT).** Nada pessoal do autor ou da máquina dele vai para o GitHub (arquivos, commits, PRs, issues, releases): siga a skill `projeto-publico`. Em cada clone, `python .githooks/privacidade.py instalar`; nunca use `--no-verify`.
- Sem dependências externas no Prumo: só a biblioteca padrão (o executável empacota tudo).
- Todo texto voltado ao usuário em português do Brasil.
- Mudou modelo, perfil, hook ou skill? Rode `python -m unittest discover -s tests -v` (os testes criam projetos de todos os perfis
  e validam que não sobram marcadores `{{...}}` nem IDs órfãos).
- Hooks (`templates/agentes/claude/hooks/`) rodam no computador do usuário: só biblioteca padrão, nada de rede, rápidos e
  silenciosos quando não têm nada a dizer. Código de saída 2 bloqueia; mensagens em stderr.
- Arquivos `.ps1`/`.psm1` são gravados em UTF-8 **com BOM** (o Windows PowerShell 5.1 precisa disso para ler acentos).
- Mudou cor da interface? Rode `python tools/cores.py`. Mudou algo importante? Atualize a documentação (`docs/`, README, este arquivo) no mesmo PR.
- Skills deste repositório: `gerar-executavel`, `criar-perfil`, `criar-modelo-documento`, `usar-prumo` e `projeto-publico`.
