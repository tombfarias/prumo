---
name: modelar-banco
description: Modela o banco de dados (06-banco-de-dados.md): diagrama ER em Mermaid, dicionário de dados, índices, DDL de referência, privacidade/LGPD e política de migrações. Use quando pedirem modelo de dados, tabelas, esquema do banco ou migrações.
---

# Modelar o banco de dados

## Entradas

`docs/04-uml/classes.md` (se existir), `docs/03-casos-de-uso.md`, `docs/02-requisitos.md` (RNF de desempenho, LGPD) e a stack em `AGENTS.md`.

## Procedimento

1. **Entidades e relacionamentos.** Derive do modelo de domínio. Normalize até a 3FN; desnormalize só com motivo registrado (desempenho de relatório, por exemplo).
2. **Diagrama ER** (`erDiagram`): nomes de entidades em MAIÚSCULAS_COM_SUBLINHADO, atributos com tipo e marcadores `PK`, `FK`, `UK`.
3. **Dicionário de dados:** uma tabela por entidade com coluna, tipo do SGBD escolhido, nulidade, padrão, restrições e descrição.
4. **Convenções:** chave primária `id` (UUID ou bigint, conforme a stack), `criado_em`/`atualizado_em` em UTC, exclusão lógica (`excluido_em`) quando houver histórico, valores monetários em `numeric(12,2)` ou centavos inteiros.
5. **Índices:** para cada consulta frequente dos casos de uso (listagens com filtro, buscas, joins), registre o índice e o UC que o justifica.
6. **DDL de referência** coerente com o diagrama. As migrações oficiais ficam no código, geradas pelo ORM.
7. **LGPD:** liste todo dado pessoal com finalidade, base legal, retenção e proteção (hash, criptografia, mascaramento). Dados sensíveis (saúde, biometria, etc.) exigem atenção especial: sinalize ao usuário.
8. **Migrações e backup:** ferramenta, como aplicar, política de rollback, seeds, frequência de backup.

## Saída

`{{prumo}} validar` sem erros; resumo com número de tabelas, dados pessoais identificados e decisões que merecem ADR (por exemplo, multi-tenant por schema ou por coluna).
