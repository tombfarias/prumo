---
name: especificar-casos-de-uso
description: Writes the use cases (03-casos-de-uso.md) from the requirements, with actors, Mermaid diagram, main, alternative and exception flows, and traceability to RF/RN/TL. Use when asked for use cases, user flows or system scenarios.
---

# Specify use cases

## Inputs

`docs/02-requisitos.md` (RF, RN), `docs/01-visao.md` (users) and, if it exists, `docs/05-interface.md` (screens).

## Procedure

1. **Actors.** List human actors (by role, not by person) and external systems.
2. **Identify the use cases** by grouping RFs that form a complete actor goal ("Issue invoice", not "Click issue"). Simple CRUDs can be a single "Manage X" case with flows for create/update/delete/view.
3. **Diagram.** Update the Mermaid flowchart in section 2: actors outside the system `subgraph`, one `((UC-00N Name))` node per use case, actor–case links. Use `-.->|include|` and `-.->|extend|` when it makes sense.
4. **Specification of each case** in the template format (`### UC-00N — Name`):
   - "Requirements covered" row with all RF/RNF covered; "Business rules" with the RN applied; "Screens" with the TL-xxx from `05-interface.md` when they already exist (otherwise `—`: the interface step fills it in later);
   - numbered main flow, alternating actor and system, from 4 to 12 steps;
   - alternative flows referencing the source step (`AF-01 (step 3)`);
   - exception flows for validation, permission denied, integration failure and unavailability.
5. **Coverage.** Every Must or Should RF must be in at least one use case. Run `{{prumo}} rastreabilidade` and check the problems section.

## Quality

- Steps describe intent, not interface ("enters the customer data", not "clicks the blue button").
- No new requirements here: if something comes up that is not in 02-requisitos.md, stop and ask the user whether it should become an RF.

## Output

`{{prumo}} validar` with no errors and a summary: use cases created, RFs still uncovered, questions.
