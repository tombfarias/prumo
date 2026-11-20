## Convenções do perfil: API REST

### Estrutura sugerida (Node.js + TypeScript)

```text
src/
  modulos/<modulo>/      # rotas, controlador, serviço, repositório e schemas do módulo
  compartilhado/         # erros, middlewares, utilitários
  config/                # leitura e validação de variáveis de ambiente
  servidor.ts
prisma/schema.prisma     # modelo de dados e migrações
tests/
```

Início rápido: `npm init -y`, depois instale `fastify`, `typescript`, `tsx`, `zod`, `vitest` e `prisma`; rode `npx prisma init`.
Alternativa em Python: `pip install "fastapi[standard]" sqlalchemy alembic pytest` e `fastapi dev`.

### Padrões

- Rotas REST no plural (`/clientes`, `/clientes/{id}`); códigos HTTP corretos (201 na criação, 204 sem corpo, 404, 409 em conflito, 422 em validação).
- Validação de entrada com schema (zod/pydantic) na borda; o serviço recebe dados já validados.
- Erros em formato único: `{ "erro": { "codigo": "...", "mensagem": "...", "detalhes": [] } }`.
- Paginação por `?pagina=&por_pagina=` com metadados na resposta.
- Documentação OpenAPI gerada a partir dos schemas e publicada em `/docs` fora de produção.
- Regra de negócio fica no serviço, nunca no controlador nem no repositório. Cite o ID da regra (`// RN-003`).
- Migrações versionadas; nunca altere uma migração já aplicada em produção.

### Segurança

- Autenticação por JWT de curta duração + refresh token, ou sessão com cookie `HttpOnly`.
- Rate limit nas rotas de autenticação; CORS restrito às origens conhecidas.
- Segredos só em variáveis de ambiente; mantenha `.env.example` atualizado.

### Testes

- Unitários para serviços e regras de negócio; integração com banco real de teste (container) para repositórios e rotas.
- Comandos sugeridos para `projeto.prumo.json`: formatar `npx prettier --write {arquivo}`, lint `npx eslint {arquivo}`, testar `npm test`.
