---
name: revisar-conformidade
description: Reviews whether the code implements exactly what the specification asks (acceptance criteria, exception flows, business rules, screens, data model) and points out divergences, test gaps and security risks. Use after implementing a story, before a delivery or when asked for a code review against the specification.
---

# Review compliance with the specification

Optional argument: story ID (`HU-003`) or use case ID. Without an argument, review the uncommitted changes (`git diff`) and those of the last commit.

## Procedure

1. Build the trail with `{{prumo}} contexto HU-00N` (HU → UC → RF/RN → TL → CT), without loading whole documents.
2. For **each acceptance criterion** and **each flow** of the UC, find where the code meets it and which test covers it. Mark: met, partial, missing or divergent.
3. For **each RN** cited: is it implemented in the right place (service/domain layer) and tested?
4. **Data:** migrations consistent with `06-banco-de-dados.md`; personal data protected as the privacy section requires.
5. **Screens:** empty/loading/error/success states; basic accessibility; fidelity to Figma, if there is a link.
6. **Security:** authorization on the server, input validation, secrets out of the code, nothing sensitive in logs.
7. **Scope:** code that implements something not specified is also a divergence (it may be an unrecorded scope change).
8. Run tests, lint and `{{prumo}} validar`.

## Report

Table `Item | Status | Evidence (file:line / test) | Suggested action`, followed by the divergences that need a decision from the user. Do not fix anything unless the user asks; this skill only reviews.
