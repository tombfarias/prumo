---
name: revisar-seguranca
description: Looks for security flaws in recent changes (access control, injection, secrets, dependencies, configuration, personal data), following the OWASP Top 10, and records the SEG-xxx findings in docs/12-seguranca.md. Use when the Prumo hook asks for it after a significant change, before a delivery or when asked for a security review.
---

# Review security

Default scope: the files the hook reported or, without that list, the uncommitted changes and the last commit (`git diff`, `git diff HEAD~1`). Before a delivery, review the whole project.

## 1. Automatic scan

1. Run `{{prumo}} seguranca` (looks for secrets in the code, SQL/shell built from external input, `eval`, TLS disabled, open CORS, debug mode, unescaped HTML and the like). Handle each result: confirm it or dismiss it as a false positive, with a justification.
2. Audit the dependencies with the stack's tool, if available: `npm audit --omit=dev`, `pnpm audit`, `pip-audit`, `composer audit`, `dotnet list package --vulnerable`, `flutter pub outdated`.

## 2. Manual review of the changed files

For each file, check what applies:

- **Access control (A01):** every route/action checks authentication **and** authorization on the server; IDs coming from the client are checked against the resource owner (IDOR).
- **Injection (A03):** parameterized queries/ORM; no user input concatenated into SQL, shell, file paths, HTML or templates.
- **Authentication (A07):** passwords with bcrypt/argon2; tokens with expiration; brute-force protection; password recovery without leaking whether the e-mail exists.
- **Data (A02, privacy):** personal data and secrets do not appear in logs, error responses or the frontend; HTTPS; what is sensitive is encrypted.
- **Configuration (A05):** debug off in production, restricted CORS, security headers, generic error messages for the user.
- **Input and files:** schema validation; uploads with a size limit, verified type and a server-generated name; the server never follows arbitrary user URLs (SSRF, A10).
- **Secrets (A08):** no key in the code or in the git history; everything in environment variables documented in `.env.example`.
- **Abuse (A04):** rate limits on login, signup, e-mail/SMS sending and expensive endpoints.

## 3. Record

In `docs/12-seguranca.md`:

- Each confirmed finding becomes `### SEG-00N — Title` with severity (Critical, High, Medium, Low), status, what it **affects** (HU/UC), evidence (`file:line`) and proposed fix.
- Update the attack surface and the threats table if new entry points came up.
- Add a row to the review history (date, scope, tools, number of findings).

## 4. Fix or escalate

- **Critical or High** findings: tell the user right away, with the suggested fix. Fix it if the fix is local and does not change specified behavior; otherwise, ask for authorization.
- Do not mark as fixed without a test or evidence of the fix.
- Run `{{prumo}} validar` at the end and summarize: findings by severity, what was fixed and what depends on the user.
