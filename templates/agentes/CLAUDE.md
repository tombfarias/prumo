# {{projeto}}

@AGENTS.md

## Específico do Claude Code

- **Fluxo de especificação completo:** `/especificar-projeto` (ou peça "especifique o projeto"). Cada etapa também tem a sua skill (`/levantar-requisitos`, `/especificar-casos-de-uso`, `/modelar-uml`...).
- **Implementação:** `/implementar-historia HU-001`; depois `/revisar-conformidade`.
- **Subagentes** em `.claude/agents/`: `analista-requisitos`, `arquiteto`, `revisor-conformidade` e `testador`. Delegue a eles as etapas longas para preservar o contexto principal.
- **Hooks ativos** (`.claude/settings.json`):
  - bloqueiam comandos destrutivos, leitura/edição de `.env` e credenciais, e edição de documentos aprovados ou gerados;
  - formatam e rodam o lint após cada edição (configure `comandos` em `projeto.prumo.json`);
  - **após uma mudança significativa**, impedem o encerramento até a documentação ser atualizada (`/atualizar-documentacao`) e a segurança revisada (`/revisar-seguranca`);
  - injetam um resumo do estado da especificação no início de cada sessão;
  - registram a atividade para `prumo horas` e, se ligado em `hooks.testes_ao_parar`, rodam os testes antes de encerrar.
{{figma_claude}}
