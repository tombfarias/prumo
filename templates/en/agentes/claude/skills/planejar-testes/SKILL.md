---
name: planejar-testes
description: Writes the test plan (09-plano-de-testes.md) with strategy, tools and CT-xxx test cases linked to the stories and use cases, including the acceptance testing script with the client. Use when asked for a test plan, test cases, acceptance criteria for delivery or QA.
---

# Plan tests

## Inputs

Backlog (acceptance criteria), use cases (exception flows), business rules and RNFs.

## Procedure

1. **Strategy:** fill in the levels table with the stack's tools (e.g. Vitest/Jest/pytest, Testing Library, Playwright/Maestro).
2. **Test cases** (`### CT-00N — What is checked`):
   - `**Checks:**` line with the HU, UC, RF and RN covered;
   - type (unit, integration, end-to-end, acceptance) and whether it is automated (with the file path when it exists);
   - objective precondition, steps and expected result.
3. **Minimum coverage, proportional to the project:** each acceptance criterion of the Must stories has a CT (simple criteria of the same story can share a CT); each RN has a unit test; each relevant exception flow has a test. Could stories get CTs only if they enter the scope.
   - To group cases by epic or story, use titles like "## Tests for epic EP-01" or "Tests for HU-003": do not start a title or the first column of a table with an ID defined in another document.
4. **Acceptance testing:** script for the client (acceptance cases in non-technical language) and the delivery acceptance criterion.
5. Run `{{prumo}} rastreabilidade` and check "stories without a test case".

## Output

Summary: CTs created per type, stories without coverage, environments and test data needed.
