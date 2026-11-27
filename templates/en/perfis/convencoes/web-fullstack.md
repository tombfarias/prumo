## Profile conventions: full-stack web application

### Suggested structure (Next.js App Router)

```text
src/
  app/                   # routes; each folder = URL segment
    (public)/ (dashboard)/ # route groups by area
    api/                 # route handlers, only when a public API is needed
  components/ui/         # reusable interface components
  components/<domain>/   # business components
  server/                # services, data access, server actions
  lib/                   # utilities, validation (zod), Prisma client
prisma/schema.prisma
tests/                   # unit (vitest) and e2e (Playwright)
```

Quick start: `npx create-next-app@latest` (TypeScript, ESLint, Tailwind, App Router, `src/` folder), `npx prisma init`, `npm init playwright@latest`.

### Patterns

- Server Components by default; `"use client"` only where there is interaction or state in the browser.
- Mutations through server actions or route handlers, always with zod validation and a permission check on the server.
- Screen components follow the Figma design (skill `implementar-tela-figma`); use the design system tokens, never loose colors or spacing.
- Each screen implements the empty, loading, error and success states.
- Accessibility: semantic elements, `label` on every field, visible focus, AA contrast.
- Cite the screen and the use case in the page component (`// TL-002 · UC-004`).

### Security

- Authentication with Auth.js; authorization checked on the server in each action, not only by hiding buttons.
- Never expose secrets in `NEXT_PUBLIC_*` variables.

### Tests

- Vitest for logic; Playwright for the journeys of the Must use cases.
- Suggested commands: format `npx prettier --write {arquivo}`, lint `npx eslint {arquivo}`, test `npm test`.
