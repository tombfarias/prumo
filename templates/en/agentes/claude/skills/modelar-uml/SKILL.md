---
name: modelar-uml
description: Produces the 14 UML 2.5 diagrams in Mermaid (class, object, package, component, composite structure, deployment, profile, use case, sequence, communication, timing, interaction overview, state, activity) in docs/04-uml/, consistent with use cases and requirements. Use when asked for UML diagrams, domain model, sequence, components or any other UML type.
---

# Model UML

## Inputs

`docs/03-casos-de-uso.md`, `docs/02-requisitos.md` and, for components/packages/deployment, `docs/07-arquitetura.md` if it already exists.
Work only on the `docs/04-uml/` files that exist in the project (the profile already chose the ones worth it).
Follow the table order: structural first (the domain), then behavioral (which use the domain names).

## Diagrams (UML 2.5)

| UML type | File | Mermaid | What to model |
|---|---|---|---|
| Class | `classes.md` | `classDiagram` | Domain: entities (nouns of the UCs), essential attributes, business operations, enumerations, multiplicities. No framework. |
| Object | `objetos.md` | `classDiagram` with `class c1["c1 : Class"]` | Sample instances with values, one per scenario that tests an RN or multiplicity. |
| Package | `pacotes.md` | `flowchart` + `subgraph` | Packages = folders/modules of `07-arquitetura.md`; `-.->` arrows «import»/«use»; no cycles. "May/must not depend" table. |
| Component | `componentes.md` | `flowchart` | Applications, modules and integrations, with the protocol of each link. |
| Composite structure | `estrutura-composta.md` | `flowchart` + `subgraph` | Only components with relevant internal parts: parts `name : Type [mult]`, ports `(("port"))`, connectors. |
| Deployment | `implantacao.md` | `flowchart` | Where each component runs: provider, containers, managed database, CDN, CI/CD. |
| Profile | `perfil-uml.md` | `classDiagram` with `<<metaclass>>`/`<<stereotype>>` | Only the stereotypes used in the other diagrams, with tagged values and the rule they impose on the code. |
| Use case | `../03-casos-de-uso.md` | `flowchart` | Already done in the use case step; just check it matches the sequences. |
| Sequence | `sequencia.md` | `sequenceDiagram` | One per Must UC, real participants; `alt`/`opt` for alternatives and exceptions. Title `## Sequence — UC-00N Name`. |
| Communication | `comunicacao.md` | `flowchart` with labels `"1: msg"`, `"1.1: msg"` | UCs where coupling matters; same messages as the sequence. Title `## Communication — UC-00N Name`. |
| Timing | `tempo.md` | table + `gantt` (`dateFormat X`, axis in seconds) | Timeouts, SLAs, expiration, schedules; each constraint cites an RNF/RN. The table is the source of truth. |
| Interaction overview | `visao-geral-interacao.md` | `flowchart TD` | Journey between UCs: `ref: UC-00N` nodes, decisions, fork/join; details stay in the sequences. |
| State machine | `estados.md` | `stateDiagram-v2` | Entities with a lifecycle. Each transition linked to a UC step or RN. |
| Activity | `atividades.md` | `flowchart` | End-to-end business processes, including manual steps outside the system. |

A diagram with no real content in the project (e.g. nothing with deadlines for `tempo.md`): write one line saying why and remove the example; do not invent.

## Mermaid syntax rules (avoid rendering errors)

- Start the block with the type: `classDiagram`, `sequenceDiagram`, `stateDiagram-v2`, `flowchart LR|TD`, `erDiagram`, `gantt`.
- In `flowchart`, texts with spaces, accents, parentheses, colons or slashes go in quotes: `a["Text (with parentheses)"]`.
- Node IDs without spaces or accents (`customer_signup`, not `customer signup`).
- Do not use `end` as a node ID or as its prefix (it is a reserved word); use `finish`.
- In `classDiagram`, generics with `~` (`List~Order~`), not `<>`; instance label with `class id["id : Class"]`.
- In `sequenceDiagram`, return messages with `-->>`.

## Consistency

- Classes ↔ tables in `06-banco-de-dados.md` (when there are any): equivalent names. Objects use only classes and attributes from `classes.md`.
- Each Must use case appears in at least one sequence diagram; communication and overview cite the same UC-xxx.
- Components and packages ↔ "Modules" section and folder structure in `07-arquitetura.md`.
- Stereotypes used in any diagram are defined in `perfil-uml.md`.

## Output

Run `{{prumo}} validar` (checks the Mermaid blocks) and `{{prumo}} diagramas` to extract the `.mmd` files. If the project uses Figma, offer to publish the diagrams to FigJam with the `diagramas-figjam` skill.
