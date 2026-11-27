---
name: planejar-arquitetura
description: Defines the architecture (07-arquitetura.md) and records decisions in ADRs: stack with versions, folder structure, modules, integrations, security, environments and CI/CD. Use when asked for architecture, stack choice, project structure or technical decisions.
---

# Plan the architecture

## Inputs

Requirements (especially RNFs), use cases, data model, component/deployment diagrams and the stack suggested in `AGENTS.md`.

## Procedure

1. **Architectural style** suited to the size: for freelance projects, prefer a well-organized modular monolith to microservices, unless there is a strong reason.
2. **Stack:** confirm the profile's stack or propose an adjustment justified by the requirements. State current stable versions (check the official documentation; do not guess versions).
3. **Folder structure** concrete (tree) following the profile's conventions in `AGENTS.md`.
4. **Modules:** each module with its responsibility and the use cases it serves.
5. **External integrations:** authentication, limits, costs and failure handling.
6. **Security:** authentication, authorization (profile matrix), secrets, sensitive data.
7. **Operation:** environments, logs, monitoring, CI/CD, estimated monthly infrastructure cost (the client needs to know).
8. **ADRs:** for each relevant decision that is hard to reverse (database, hosting provider, authentication, multi-tenant, framework), run `{{prumo}} adr "title"`, fill in the file created in `docs/adr/` and list it in section 8.
9. **Project commands:** propose to the user the `comandos` values (format, lint, test) in `projeto.prumo.json` according to the stack.

## Output

`{{prumo}} validar` with no errors; summary of the stack, ADRs created and estimated infrastructure cost.
