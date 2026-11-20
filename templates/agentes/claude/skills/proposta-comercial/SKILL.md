---
name: proposta-comercial
description: Monta a proposta comercial (10-proposta-comercial.md) para o cliente a partir da visão, do backlog e do orçamento gerado pelo Prumo, em linguagem não técnica. Use quando pedirem proposta, orçamento para o cliente, cronograma comercial ou condições de pagamento.
---

# Proposta comercial

## Entradas

`docs/01-visao.md` (escopo e fora do escopo), `docs/08-backlog.md` (épicos e marcos) e `docs/orcamento.md`. Se `orcamento.md` não existir ou estiver desatualizado, rode `{{prumo}} orcamento` antes.

## Procedimento

1. Escreva para o cliente, não para desenvolvedores: benefícios e resultados, sem jargão.
2. **Escopo incluído** = épicos do backlog; **não incluído** = seção "Fora do escopo" da visão, mais itens comuns que o cliente pode presumir (hospedagem, domínio, conteúdo, fotos, manutenção mensal).
3. **Cronograma** = marcos do backlog, com prazo e percentual de pagamento.
4. **Investimento:** use os totais de `docs/orcamento.md`. Não invente valores. Se o valor da hora não estiver configurado, pergunte ao usuário.
5. **Custos recorrentes do cliente** (hospedagem, APIs pagas, lojas de apps) vêm de `07-arquitetura.md`.
6. Preencha garantia, suporte, mudanças de escopo e propriedade intelectual com as condições que o usuário informar; na falta delas, deixe `[PREENCHER]` e pergunte. Lembre o usuário de revisar os termos (não é aconselhamento jurídico).

## Saída

Proposta sem lacunas, ou com uma lista objetiva do que o usuário precisa decidir.
