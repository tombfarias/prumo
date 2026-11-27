## Profile conventions: management system

### Suggested structure

```text
frontend/                # React + Vite + TypeScript + shadcn/ui + TanStack Query
  src/pages/ src/components/ src/services/ src/routes/
backend/                 # NestJS + Prisma + PostgreSQL
  src/modules/<module>/  # controller, service, dto, entity
  prisma/
tests/                   # e2e (Playwright) of the main journeys
```

Quick start: `npm create vite@latest frontend -- --template react-ts`, `npx shadcn@latest init`, `npx @nestjs/cli new backend`.
Alternatives with a ready-made admin: `composer create-project laravel/laravel` + `composer require filament/filament`, or Django + Django Admin.

### Patterns specific to management systems

- **Access profiles (RBAC):** roles and permissions modeled in the database; role × use case matrix documented in 03-casos-de-uso.md.
- **Audit:** record who created/changed/deleted and when (`created_by`, `updated_at`, log table for critical entities).
- **Soft delete** (`deleted_at`) for entities with financial or tax history.
- **Lists:** filters, sorting, server-side pagination and CSV/XLSX export when requested.
- **Reports:** heavy queries outside the main transaction; consider materialized views.
- **Money values** in `decimal`/integer cents, never `float`. Dates in UTC in the database, displayed in the client's time zone.
- Forms with local masks and validation when applicable (tax IDs, postal code, phone).

### Tests

- Business rules with unit tests; signup and permission flows with e2e.
- Suggested commands: format `npx prettier --write {arquivo}`, lint `npx eslint {arquivo}`, test `npm test`.
