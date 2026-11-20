# Diagramas de Atividades (Processos) — {{projeto}}

<!--
Processos de negócio ponta a ponta, incluindo etapas fora do sistema (manuais).
Útil para validar com o cliente o "como funciona hoje" e o "como vai funcionar".
Sintaxe: https://mermaid.js.org/syntax/flowchart.html
-->

## Processo — [PREENCHER: nome do processo]

```mermaid
flowchart TD
    inicio([Início]) --> a1[Cliente envia solicitação]
    a1 --> d1{Dados completos?}
    d1 -- Não --> a2[Solicitar complemento]
    a2 --> a1
    d1 -- Sim --> a3[Registrar no sistema]
    a3 --> a4[Notificar responsável]
    a4 --> fim([Fim])
```

[PREENCHER: responsáveis por etapa, SLAs, pontos de automação]
