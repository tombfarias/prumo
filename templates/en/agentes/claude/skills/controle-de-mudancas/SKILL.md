---
name: controle-de-mudancas
description: Handles client change requests after the specification was approved, recording a change request (CM-xxx) with impact analysis on requirements, use cases, stories, screens, data, deadline and cost. Use when the client asks for something new or different from what was agreed, or when an approved document needs to change.
---

# Change control

In freelance projects, an unrecorded change becomes a loss. This skill ensures every scope change is analyzed and approved before it enters the project.

## Procedure

1. **Record:** run `{{prumo}} mudanca "short title"` and fill in the file created in `docs/mudancas/` with the description in the client's words and the reason.
2. **Classify:** is it a defect fix (the system does not do what was specified; not a change), a clarification (the document was ambiguous) or a scope change (something new or different)?
3. **Analyze impact:** walk the traceability (`{{prumo}} rastreabilidade`) and list each affected RF, RN, UC, TL, HU, CT, table and ADR, with the change needed.
4. **Estimate:** extra hours (create the new HUs in the CM itself as a proposal), impact on the milestone deadlines and on cost (hourly rate from `prumo orcamento`).
5. **Present to the user** a summary to send to the client: what changes, how much it costs, how much it delays, alternatives (do it now, phase 2, simplified version).

## After client approval

Only the user removes the protection: `prumo desaprovar <file>`. Then update the affected documents citing the `CM-xxx` (e.g. in the Source column of the requirements), mark the CM as approved, and the user approves again: `prumo aprovar <file>`.

Never edit approved documents or implement the change before the approval is recorded.
