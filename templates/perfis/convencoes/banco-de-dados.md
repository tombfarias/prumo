## Convenções do perfil: banco de dados

### Estrutura sugerida

```text
db/migrations/           # migrações dbmate: AAAAMMDDHHMMSS_descricao.sql
db/seeds/                # dados iniciais e de exemplo (idempotentes)
db/schema.sql            # esquema atual gerado por `dbmate dump` (não edite à mão)
sql/views/               # views e funções (CREATE OR REPLACE)
sql/relatorios/          # consultas de relatório, uma por arquivo, com o ID do requisito no cabeçalho
sql/cargas/              # cargas/ETL: staging → validação → tabela final
tests/                   # testes pgTAP (*.sql)
.sqlfluff                # [sqlfluff] dialect = postgres
```

Início rápido: instale o PostgreSQL e o [dbmate](https://github.com/amacneil/dbmate); `pip install sqlfluff`;
no banco de teste, `CREATE EXTENSION pgtap;` (pacote `postgresql-<versão>-pgtap`) e instale o `pg_prove` (`cpan TAP::Parser::SourceHandler::pgTAP`).
`DATABASE_URL` no `.env`; `dbmate new <descricao>`, `dbmate up`, `dbmate rollback`, `dbmate status`.
MySQL: troque `--dialect postgres` por `--dialect mysql` nos comandos e teste com pytest.

### Padrões

- Nomes em snake_case, tabelas no singular, PK `id` (`bigint generated always as identity` ou `uuid`), FK `<tabela>_id`,
  índices `ix_<tabela>_<colunas>`, únicas `uq_...`, checks `ck_...`. Datas `timestamptz` em UTC; dinheiro `numeric(12,2)`.
- Toda migração tem `-- migrate:up` e `-- migrate:down` e roda numa transação. Nunca edite migração já aplicada; crie outra.
- Mudança incompatível: expandir → migrar dados → contrair, em deploys separados. Em tabela grande, `CREATE INDEX CONCURRENTLY`
  (fora de transação: `-- migrate:up transaction:false`) e preenchimento em lotes.
- Restrições no banco (NOT NULL, FK, CHECK, UNIQUE): a regra de negócio que o banco garante cita o ID (`-- RN-003`).
- Consultas: colunas explícitas (nada de `SELECT *` em views e relatórios), `EXPLAIN (ANALYZE, BUFFERS)` em toda consulta
  crítica, registrando o resultado em `06-banco-de-dados.md` (seção 5). Paginação por chave (`WHERE id > $1`) em listas grandes.
- Cargas idempotentes: chave natural + `INSERT ... ON CONFLICT`; rejeitados em tabela de quarentena com o motivo.

### Segurança

- Papéis separados (aplicação sem DDL, migração, leitura); nunca use o superusuário na aplicação nem em relatórios.
- Consultas parametrizadas sempre; SQL dinâmico só com `format('%I', ...)`/`quote_ident`.
- Dados pessoais: mínimo necessário, mascarados em views de relatório; nada de dump de produção em ambiente de teste sem anonimizar.
- Nunca rode `DROP`, `TRUNCATE` ou `DELETE`/`UPDATE` sem `WHERE` em produção; antes de mexer em produção, backup e confirmação do usuário.

### Testes

- pgTAP por arquivo em `tests/`: `BEGIN; SELECT plan(n); ... SELECT * FROM finish(); ROLLBACK;` (estrutura com `has_table`/`col_not_null`,
  regras com `throws_ok`, relatórios com `results_eq`). Banco de teste recriado do zero com `dbmate up` + seeds.
- Comandos sugeridos: formatar `sqlfluff format --dialect postgres {arquivo}`, lint `sqlfluff lint --dialect postgres {arquivo}`,
  testar `pg_prove -r tests` (conexão pelas variáveis `PGHOST`, `PGDATABASE`, `PGUSER`).
