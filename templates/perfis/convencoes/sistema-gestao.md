## Convenções do perfil: sistema de gestão

### Estrutura sugerida

```text
frontend/                # React + Vite + TypeScript + shadcn/ui + TanStack Query
  src/paginas/ src/componentes/ src/servicos/ src/rotas/
backend/                 # NestJS + Prisma + PostgreSQL
  src/modulos/<modulo>/  # controller, service, dto, entidade
  prisma/
tests/                   # e2e (Playwright) das jornadas principais
```

Início rápido: `npm create vite@latest frontend -- --template react-ts`, `npx shadcn@latest init`, `npx @nestjs/cli new backend`.
Alternativas com painel pronto: `composer create-project laravel/laravel` + `composer require filament/filament`, ou Django + Django Admin.

### Padrões específicos de sistemas de gestão

- **Perfis de acesso (RBAC):** papéis e permissões modelados no banco; matriz papel × caso de uso documentada em 03-casos-de-uso.md.
- **Auditoria:** registrar quem criou/alterou/excluiu e quando (`criado_por`, `atualizado_em`, tabela de log para entidades críticas).
- **Exclusão lógica** (`excluido_em`) para entidades com histórico financeiro ou fiscal.
- **Listagens:** filtros, ordenação, paginação no servidor e exportação CSV/XLSX quando pedida.
- **Relatórios:** consultas pesadas fora da transação principal; considerar visões materializadas.
- **Valores monetários** em `decimal`/centavos inteiros, nunca `float`. Datas em UTC no banco, exibidas em America/Sao_Paulo.
- Formulários com máscara e validação brasileira quando aplicável (CPF/CNPJ, CEP, telefone).

### Testes

- Regras de negócio com testes unitários; fluxos de cadastro e permissões com e2e.
- Comandos sugeridos: formatar `npx prettier --write {arquivo}`, lint `npx eslint {arquivo}`, testar `npm test`.
