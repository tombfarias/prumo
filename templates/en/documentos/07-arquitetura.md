# Architecture — {{projeto}}

| Field | Value |
|---|---|
| Profile | {{perfil_nome}} |
| Proposed stack | {{stack}} |
| Version | 0.1 |

<!--
Explains HOW the system will be built. Relevant decisions that are hard to reverse
become ADRs in docs/adr/ (`prumo adr "title"`) and are listed in section 8.
-->

## 1. Overview

[FILL: architectural style (modular monolith, SPA + API, serverless...) and why]

## 2. Stack

<!-- prumo:gerado:stack -->
| Layer | Technology | Version | Rationale |
|---|---|---|---|
| [FILL] | [FILL] | [FILL] | [FILL] |
<!-- prumo:gerado:fim -->

## 3. Folder structure

```text
[FILL: directory tree of the code]
```

## 4. Modules and responsibilities

| Module | Responsibility | Use cases |
|---|---|---|
| [FILL] | [FILL] | [FILL: UC-xxx] |

## 5. External integrations

<!-- prumo:gerado:integracoes -->
| System | Purpose | Protocol / authentication | Failure handling |
|---|---|---|---|
| [FILL] | [FILL] | [FILL] | [FILL: retry, queue, fallback] |
<!-- prumo:gerado:fim -->

## 6. Security

<!-- prumo:gerado:seguranca -->
- **Authentication:** [FILL]
- **Authorization / access profiles:** [FILL]
- **Secrets:** environment variables; never versioned (`.env` stays out of git, `.env.example` documents the keys).
- **Sensitive data:** [FILL: encryption, masking in logs]
<!-- prumo:gerado:fim -->

## 7. Quality and operations

- **Code standards:** see AGENTS.md
- **Tests:** see 09-plano-de-testes.md
- **Logs and monitoring:** [FILL]
- **CI/CD:** [FILL: build, test and deploy pipeline]
- **Environments:** see 04-uml/implantacao.md

## 8. Architecture decisions (ADRs)

| ADR | Title | Status |
|---|---|---|
| [FILL: ADR-xxx, created with `prumo adr`] | [FILL] | Proposed |
