# Diagrama de Estrutura Composta — {{projeto}}

<!--
Estrutura interna de um componente/classe complexo: partes, portas (pontos de interação) e conectores.
Use para os componentes de componentes.md que têm partes internas relevantes (ex.: serviço com fila e workers).
Notação: subgraph = classificador; nós = partes ("nome : Tipo"); círculos = portas.
-->

## Estrutura interna — [PREENCHER: componente]

```mermaid
flowchart LR
    porta_http(("http"))
    subgraph servico["«componente» ServicoDePedidos"]
        controlador["ctrl : Controlador"]
        fila["fila : FilaDeMensagens"]
        worker["worker : Processador [1..4]"]
        controlador -- "enfileira" --> fila
        fila -- "consome" --> worker
    end
    porta_pagamento(("pagamento"))
    porta_http --- controlador
    worker --- porta_pagamento
```

| Parte / porta | Tipo | Multiplicidade | Interface oferecida/requerida |
|---|---|---|---|
| [PREENCHER] | [PREENCHER] | [PREENCHER] | [PREENCHER] |
