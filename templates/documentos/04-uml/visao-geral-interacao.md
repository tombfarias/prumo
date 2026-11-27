# Visão Geral de Interação — {{projeto}}

<!--
Fluxo de controle entre interações: cada nó "ref" aponta para um diagrama de sequência (sequencia.md) ou de comunicação.
Mostra a jornada completa (ordem dos casos de uso, decisões, paralelismo) sem repetir os detalhes de cada interação.
Sintaxe: flowchart; nós "ref" em retângulos, decisões em losango, paralelismo com fork/join.
-->

## Jornada — [PREENCHER: nome, ex.: compra completa]

```mermaid
flowchart TD
    inicio((" ")) --> login["ref: UC-001 Autenticar"]
    login --> autenticado{"autenticado?"}
    autenticado -- "não" --> fim_erro(((" ")))
    autenticado -- "sim" --> carrinho["ref: UC-002 Montar carrinho"]
    carrinho --> fork[" "]
    fork --> pagamento["ref: UC-003 Pagar"]
    fork --> estoque["ref: UC-004 Reservar estoque"]
    pagamento --> join[" "]
    estoque --> join
    join --> fim(((" ")))
```

| Nó | Diagrama detalhado |
|---|---|
| [PREENCHER: UC-001] | [PREENCHER: sequencia.md — Sequência — UC-001] |
