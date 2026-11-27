---
name: implementar-historia
description: Implements a user story (HU-xxx) following the specification trail (UC, RF, RN, screens, data model), tests first, IDs in the code and a traceable commit. Use when asked to implement, code or develop a story, feature or use case.
---

# Implement a story

Expected argument: the story ID (e.g. `HU-003`). If it is missing, ask which one, listing the highest-priority `to do` stories.

## 1. Load the trail

1. Run `{{prumo}} contexto HU-00N`: it brings, without the rest of the documents, the story and the UCs, RF/RNF/RN, screens, tests and epic linked to it.
2. If you need more, read only the relevant sections of `06-banco-de-dados.md`, `07-arquitetura.md` and the ADRs (search for the entity/module names).
3. Check the **Definition of Ready**: if there is `[FILL]` or a contradiction in the trail, **stop** and ask the user before coding.

## 2. Plan

List for the user, in a few lines: files to create/change, migrations, tests (with the matching CT-xxx) and risks. In large stories, wait for the go-ahead.

## 3. Tests first

Write the tests from the acceptance criteria and the CTs in `09-plano-de-testes.md`, with the ID in the test (`// CT-004` or `# CT-004`). Confirm they fail for the right reason.

## 4. Implement

- Follow the conventions in `AGENTS.md` and the architecture's structure.
- Cite the rule where it is implemented (`// RN-002`).
- Screens: if the screen has a Figma link, use the `implementar-tela-figma` skill.
- Migrations through the ORM, consistent with the data model. If the model needs to change, stop and warn (the document may be approved).

## 5. Close

1. Run the tests, the lint and `{{prumo}} validar`.
2. Follow `atualizar-documentacao` (documents affected by the implementation) and `revisar-seguranca` (changed files). The Prumo hook requires this when the change is significant.
3. Update the story status in the backlog to `in review` (if the document is approved, tell the user instead of editing).
4. Run `{{prumo}} rastreabilidade`.
5. Suggest the commit message: `feat(HU-003): <summary>` with the UCs in the body. Commit only if the user asks.
6. Recommend running `/revisar-conformidade HU-003` (or the `revisor-conformidade` subagent).
