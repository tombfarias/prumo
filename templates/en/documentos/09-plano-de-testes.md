# Test Plan — {{projeto}}

<!--
Test cases CT-001... In each case block, cite what it verifies (HU, UC, RF, RN).
Whenever the test is automated, also cite the test file and write the CT ID
in a comment inside the test (e.g. `// CT-001`), so traceability can find it.
-->

## 1. Strategy

| Level | Tool | Scope | Target |
|---|---|---|---|
| Unit | [FILL] | Business rules and pure functions | [FILL: e.g. 80% of the RN] |
| Integration | [FILL] | API + database, external integrations (with test doubles) | Main flows |
| End to end | [FILL: Playwright, Cypress, Maestro...] | Critical journeys of the use cases | Main flow of each Must UC |

## 2. Environments and test data

[FILL: test database, seeds, test accounts, integration sandboxes]

## 3. Test cases

### CT-001 — [FILL: what is verified]

**Verifies:** HU-001, UC-001 · **Type:** acceptance · **Automated:** [FILL: yes (file path) / no]

- **Precondition:** [FILL]
- **Steps:** [FILL]
- **Expected result:** [FILL]

## 4. User acceptance with the client

- **Environment:** [FILL]
- **Script:** the acceptance test cases marked above
- **Delivery acceptance criterion:** [FILL: e.g. no open critical defect; minor defects with a fix deadline]
- **Defect log:** [FILL: where the client reports]
