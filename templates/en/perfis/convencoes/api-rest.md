## Profile conventions: REST API

### Suggested structure (Node.js + TypeScript)

```text
src/
  modules/<module>/      # module routes, controller, service, repository and schemas
  shared/                # errors, middlewares, utilities
  config/                # reading and validating environment variables
  server.ts
prisma/schema.prisma     # data model and migrations
tests/
```

Quick start: `npm init -y`, then install `fastify`, `typescript`, `tsx`, `zod`, `vitest` and `prisma`; run `npx prisma init`.
Python alternative: `pip install "fastapi[standard]" sqlalchemy alembic pytest` and `fastapi dev`.

### Patterns

- Plural REST routes (`/customers`, `/customers/{id}`); correct HTTP codes (201 on creation, 204 without body, 404, 409 on conflict, 422 on validation).
- Input validation with a schema (zod/pydantic) at the edge; the service receives already validated data.
- Errors in a single format: `{ "error": { "code": "...", "message": "...", "details": [] } }`.
- Pagination with `?page=&per_page=` and metadata in the response.
- OpenAPI documentation generated from the schemas and published at `/docs` outside production.
- Business rules live in the service, never in the controller or the repository. Cite the rule ID (`// RN-003`).
- Versioned migrations; never change a migration already applied in production.

### Security

- Authentication with a short-lived JWT + refresh token, or a session with an `HttpOnly` cookie.
- Rate limit on authentication routes; CORS restricted to known origins.
- Secrets only in environment variables; keep `.env.example` up to date.

### Tests

- Unit tests for services and business rules; integration with a real test database (container) for repositories and routes.
- Suggested commands for `projeto.prumo.json`: format `npx prettier --write {arquivo}`, lint `npx eslint {arquivo}`, test `npm test`.
