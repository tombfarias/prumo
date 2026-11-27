# {{projeto}}

@AGENTS.md

## Claude Code specifics

- **Full specification flow:** `/especificar-projeto` (or ask "specify the project"). Each step also has its own skill (`/levantar-requisitos`, `/especificar-casos-de-uso`, `/modelar-uml`...).
- **Implementation:** `/implementar-historia HU-001`; then `/revisar-conformidade`.
- **Subagents** in `.claude/agents/`: `analista-requisitos`, `arquiteto`, `revisor-conformidade` and `testador`. Delegate the long steps to them to preserve the main context.
- **Active hooks** (`.claude/settings.json`):
  - block destructive commands, reading/editing `.env` and credentials, and editing approved or generated documents;
  - format and run the lint after each edit (configure `comandos` in `projeto.prumo.json`);
  - **after a significant change**, prevent ending until the documentation is updated (`/atualizar-documentacao`) and security is reviewed (`/revisar-seguranca`);
  - inject a summary of the specification state at the start of each session;
  - log activity for `prumo horas` and, if enabled in `hooks.testes_ao_parar`, run the tests before ending.
{{figma_claude}}
