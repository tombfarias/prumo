---
name: mapear-projeto-existente
description: Reverse-engineers a project that already has code and describes in docs/ the system as it is today (requirements, use cases, UML, database, architecture, screens), citing the source file of each item, without changing the code. Use when Prumo was installed in an existing project, when asked to map, document or understand a system that already exists, or when taking over someone else's project.
---

# Map an existing project

`{{projeto}}` already had code when Prumo was installed. Your job is to **describe what exists**, not what should exist. The code is the source of facts; the client is the source of intentions.

## Before starting

1. Read `docs/00-mapa-do-codigo.md` (stack, commands, structure and key files detected). Do not redo that scan.
2. Check `projeto.prumo.json` → `comandos`. If any is wrong for this machine, fix it there and tell the user.
3. Read the README and the documentation the project already had. **Do not delete or rewrite** the client's files: Prumo only added blocks between `<!-- prumo:inicio -->` and `<!-- prumo:fim -->`.
4. **Do not change code** in this task. To scan many files, delegate to subagents (`analista-requisitos`, `arquiteto`) that return only the conclusion.

## Procedure (skip what the profile does not have)

| # | What to read in the code | Where to write |
|---|---|---|
| 1 | README, client issues/notes, what the user tells you | `docs/00-briefing.md` (context, existing integrations; what is unknown becomes a P-xx question) |
| 2 | Routes, controllers, handlers, screens, commands, jobs | `docs/02-requisitos.md`: one RF per observable behavior |
| 3 | Validations, calculations, permissions, limits in the code | `docs/02-requisitos.md`: RN, with the example taken from the code |
| 4 | Security config, cache, logs, timeouts, CI | RNF with the current value (e.g. "session expires in 30 min") |
| 5 | User roles, end-to-end flows | `docs/03-casos-de-uso.md` |
| 6 | Screens, pages and components | `docs/05-interface.md` (TL inventory) |
| 7 | Models, entities, migrations, schema | `docs/06-banco-de-dados.md` and `docs/04-uml/classes.md` |
| 8 | Multi-layer flows, entity states | `docs/04-uml/sequencia.md`, `estados.md`, `atividades.md` |
| 9 | Folders, modules, external integrations, Docker/CI, hosting | `docs/07-arquitetura.md`, `04-uml/componentes.md`, `04-uml/implantacao.md`; decisions already made become ADRs with status "Accepted" |
| 10 | Existing tests | `docs/09-plano-de-testes.md` (CTs linked to the RFs they already cover) |
| 11 | What the client asked for now (if anything) | `docs/08-backlog.md`: only the new work becomes HU; the existing does not |

## Rules

- **Source of each item:** in the Source column of the requirements use `Code: path/file` (e.g. `Code: src/routes/orders.ts`). In the other documents, cite the file in backticks next to the item.
- **Inferred is not confirmed:** behavior that looks like a bug, dead code or a rule with no clear reason becomes a question to the client (P-xx) and goes in as "Assumption", not as a firm requirement.
- **Faithful to the real stack:** the architecture describes the stack in the code, not the one suggested by the profile. If the project uses a convention (names, folders, style), record it in `docs/07-arquitetura.md` so the next implementations follow it.
- **Debts and risks:** problems found (outdated dependency, missing test, security flaw) go to the vision's risks or to `docs/12-seguranca.md` (SEG findings), never silently fixed.
- **Traceability:** where the code is touched in the future, comments with IDs (`// HU-003 · RN-002`) link code and documents. Do not go inserting IDs into the code now.
- Proportional to the system: a small project produces short documents. A section that does not apply: "Not applicable" and the reason.

## Output

Run `{{prumo}} validar` and `{{prumo}} rastreabilidade`. Answer in a few lines: how many RF/RN/UC/tables were mapped, the open questions for the client, risks found and the next step (usually review with the user and approve with `{{prumo}} aprovar`).
