# Diagramas de Sequência — {{projeto}}

<!--
Um diagrama por caso de uso relevante (fluxo principal + exceções importantes).
Título de cada seção: "## Sequência — UC-001 Nome". Participantes reais da arquitetura
(Frontend, API, Serviço, Banco, sistemas externos).
Sintaxe: https://mermaid.js.org/syntax/sequenceDiagram.html
-->

## Sequência — UC-001 [PREENCHER: nome]

```mermaid
sequenceDiagram
    autonumber
    actor U as Usuário
    participant F as Frontend
    participant A as API
    participant B as Banco de dados
    U->>F: Preenche o formulário
    F->>A: POST /recurso
    A->>A: Valida dados
    alt dados válidos
        A->>B: INSERT
        B-->>A: id
        A-->>F: 201 Created
        F-->>U: Mensagem de sucesso
    else dados inválidos
        A-->>F: 422 Erros de validação
        F-->>U: Exibe erros
    end
```

[PREENCHER: notas sobre transações, idempotência, timeouts]
