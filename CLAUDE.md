# Prumo — instruções para desenvolver o próprio Prumo

O Prumo é um kit em Python (só biblioteca padrão, 3.9+) que cria e mantém projetos freelance com especificação,
rastreabilidade e um kit de agentes (skills, subagentes, hooks) para o Claude Code. Visão geral em `docs/arquitetura-do-prumo.md`.

## Mapa

- `prumo_cli/` — CLI (`cli.py`), criação de projetos (`projeto.py`), rastreabilidade (`rastreio.py`), validação e
  contexto (`validacao.py`), orçamento/horas/exportação (`gestao.py`), Figma (`figma.py`), segurança (`seguranca.py`),
  ponte com o Claude Code (`claude.py`), servidor da interface (`servidor.py`) e a interface (`gui/index.html`, HTML/CSS/JS puro).
- `templates/documentos/` — modelos de especificação; `templates/perfis/` — perfis e convenções por stack;
  `templates/agentes/` — AGENTS.md, CLAUDE.md, skills, subagentes, hooks e settings copiados para cada projeto.
- `powershell/` — módulo `Prumo.psm1` e instalador. `build.ps1` — executáveis. `.github/workflows/ci.yml` — testes e build.

## Regras

- Sem dependências externas no Prumo: só a biblioteca padrão (o executável empacota tudo).
- Todo texto voltado ao usuário em português do Brasil.
- Mudou modelo, perfil, hook ou skill? Rode `python -m unittest discover -s tests -v` (os testes criam projetos de todos os perfis
  e validam que não sobram marcadores `{{...}}` nem IDs órfãos).
- Hooks (`templates/agentes/claude/hooks/`) rodam no computador do usuário: só biblioteca padrão, nada de rede, rápidos e
  silenciosos quando não têm nada a dizer. Código de saída 2 bloqueia; mensagens em stderr.
- Arquivos `.ps1`/`.psm1` são gravados em UTF-8 **com BOM** (o Windows PowerShell 5.1 precisa disso para ler acentos).
- Skills deste repositório: `gerar-executavel`, `criar-perfil`, `criar-modelo-documento` e `usar-prumo`.
