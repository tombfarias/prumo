# Security — {{projeto}}

<!--
Living document. Updated on every significant change by the `revisar-seguranca` skill
(the Prumo hook asks for the review automatically). Findings use IDs SEG-001, SEG-002...
and cite the affected story or use case, so they enter traceability.
Severity: Critical, High, Medium, Low. Status: open, fixing, fixed, accepted (risk taken).
-->

## 1. Attack surface

<!-- prumo:gerado:superficie -->
| Entry point | Exposure | Authentication | Data handled |
|---|---|---|---|
| [FILL: public API, form, webhook, admin panel...] | [FILL: internet / internal network] | [FILL] | [FILL] |
<!-- prumo:gerado:fim -->

## 2. Threats and controls

<!-- Use STRIDE as a guide: spoofing, tampering, repudiation, information disclosure,
denial of service, elevation of privilege. -->

<!-- prumo:gerado:ameacas -->
| Threat | Where | Control adopted | Verified in |
|---|---|---|---|
| [FILL: access to another customer's data (IDOR)] | [FILL] | [FILL: owner check on every query] | [FILL: CT-xxx] |
<!-- prumo:gerado:fim -->

## 3. Base checklist (OWASP Top 10)

- [ ] Access control checked on the server on every route/action (A01)
- [ ] Passwords with a strong hash; sensitive data encrypted in transit and at rest (A02)
- [ ] Parameterized queries / ORM; no input concatenated into SQL, shell or HTML (A03)
- [ ] Rate limits and business rules against abuse (A04)
- [ ] Secure configuration: no debug mode in production, restricted CORS, security headers (A05)
- [ ] Dependencies audited and up to date (A06)
- [ ] Authentication: session/JWT with expiry, brute-force protection (A07)
- [ ] Integrity: secrets out of the code, protected deploy pipeline (A08)
- [ ] Security logs without sensitive data; alerts for repeated failures (A09)
- [ ] Requests to external URLs validated (SSRF) (A10)

## 4. Findings

### SEG-001 — [FILL: finding title]

**Severity:** [FILL] · **Status:** open · **Affects:** [FILL: HU-xxx / UC-xxx]

- **Description:** [FILL]
- **Evidence:** [FILL: file:line]
- **Fix:** [FILL]

## 5. Review history

| Date | Scope reviewed | Tools | Findings |
|---|---|---|---|
| {{data}} | Document created | — | — |
