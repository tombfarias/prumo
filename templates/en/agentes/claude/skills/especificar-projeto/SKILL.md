---
name: especificar-projeto
description: Runs the full project specification, from briefing to backlog and proposal, step by step, with validation and a pause for user review between steps. Use when asked to specify the project, document the system from scratch or "run the Prumo flow".
---

# Specify the project (full flow)

You run the specification of `{{projeto}}` in steps. Each step has its own skill with the detailed instructions. **Do not skip steps** and **do not move on before the user reviews** the previous step, unless they ask to go straight through.

## Before starting

1. Run `{{prumo}} status` to see which documents exist and how many `[FILL]` gaps each one has.
2. Read `docs/00-briefing.md`. If it is empty and there is no `especificacao.prumo.json` (the interface form), ask the user for the client's notes (e-mails, transcribed audio, messages) and fill in the briefing first, without inventing anything.
3. If `projeto.prumo.json` has `"existente": true`, the code already existed: first run the `mapear-projeto-existente` skill (the documents describe what exists) and use the flow below only for the new work.
4. Read `projeto.prumo.json` to know which documents belong to this profile. Skip the steps whose documents do not exist.

## Steps

| # | Step | Skill | Documents |
|---|---|---|---|
| 1 | Vision and requirements | `levantar-requisitos` | 01-visao.md, 02-requisitos.md |
| 2 | Use cases | `especificar-casos-de-uso` | 03-casos-de-uso.md |
| 3 | Interface (if any) | `especificar-interface` | 05-interface.md |
| 4 | UML modeling | `modelar-uml` | 04-uml/*.md |
| 5 | Database | `modelar-banco` | 06-banco-de-dados.md |
| 6 | Architecture | `planejar-arquitetura` | 07-arquitetura.md, docs/adr/ |
| 7 | Backlog and estimates | `gerar-backlog` | 08-backlog.md |
| 8 | Test plan | `planejar-testes` | 09-plano-de-testes.md |
| 9 | Commercial proposal | `proposta-comercial` | 10-proposta-comercial.md, orcamento.md |

## At the end of each step

1. Run `{{prumo}} validar` and fix the errors (undefined IDs, invalid Mermaid).
2. Show the user a short summary: what was created, gaps left and the questions for the client that came up (recorded in section 9 of the briefing).
3. Ask whether you can move on to the next step.

## At the end of the flow

- Run `{{prumo}} rastreabilidade` and `{{prumo}} orcamento`.
- Suggest to the user which documents to send to the client for approval. After approval, **the user** runs `prumo aprovar <file>`; you do not approve documents.
