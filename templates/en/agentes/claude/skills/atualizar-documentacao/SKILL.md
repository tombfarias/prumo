---
name: atualizar-documentacao
description: Updates the specification documents affected by a significant code change (database, routes, screens, dependencies, infrastructure, tests, configuration), keeping docs and code consistent. Use when the Prumo hook asks for it, when finishing a story or when asked to sync the documentation with the code.
---

# Update the documentation after a change

The specification is the source of truth only if it follows the code. This skill closes the loop after each significant change.

## 1. Find what changed

- Use the file list the hook reported or, without it, `git status` and `git diff` (include new files).
- For each file, find which specification items it belongs to: IDs cited in the code (`// RN-002`, `// TL-003`) and the story in progress. Use `{{prumo}} contexto <ID>` to see only the blocks linked to each item, instead of opening whole documents.

## 2. Decide which documents to update

| Code change | Documents to review |
|---|---|
| Migrations, schema, models, entities | `06-banco-de-dados.md` (ER, dictionary, indexes, privacy), `04-uml/classes.md`, `04-uml/objetos.md` |
| Routes, endpoints, controllers, screens, page components | `03-casos-de-uso.md` (flows), `04-uml/sequencia.md`, `04-uml/comunicacao.md`, `04-uml/visao-geral-interacao.md`, `05-interface.md` |
| New or changed business rule | `02-requisitos.md` (RN), use cases that apply it |
| New dependency, external service, structure change | `07-arquitetura.md` (+ ADR with `{{prumo}} adr`), `04-uml/componentes.md`, `04-uml/pacotes.md`, `04-uml/estrutura-composta.md` |
| Timeout, schedule, queue, deadline, SLA | `04-uml/tempo.md`, `02-requisitos.md` (RNF/RN) |
| Docker, CI/CD, hosting | `04-uml/implantacao.md`, `07-arquitetura.md`, `11-entrega.md` |
| New environment variable | `.env.example`, `07-arquitetura.md` (secrets), `11-entrega.md`, `README.md` |
| New or changed tests | `09-plano-de-testes.md` (CT-xxx with the test path) |
| Story done or in review | `08-backlog.md` (status) |
| New install or run command, or convention | `README.md`, `AGENTS.md` |

Consider only the documents that exist in the project (`projeto.prumo.json` → `documentos`).

## 3. Update

- Edit only what is needed, keeping the format and the existing IDs. New items get the next free ID in the sequence.
- An **approved document** (`projeto.prumo.json` → `aprovados`) cannot be edited (the hook blocks it). If the change alters what was approved, it is a scope change: follow the `controle-de-mudancas` skill and tell the user.
- If the code diverges from the specification with no recorded reason, **do not adjust the document to "match"**: point out the divergence to the user. They decide whether the code or the specification is wrong.
- Changed Mermaid diagrams must stay valid.

## 4. Check

1. `{{prumo}} validar` with no errors.
2. `{{prumo}} rastreabilidade` regenerated.
3. Summarize for the user: documents updated (with the reason), divergences found and what depends on client approval.
