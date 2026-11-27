# Sequence Diagrams — {{projeto}}

<!--
One diagram per relevant use case (main flow + important exceptions).
Title of each section: "## Sequence — UC-001 Name". Real participants from the architecture
(Frontend, API, Service, Database, external systems).
Syntax: https://mermaid.js.org/syntax/sequenceDiagram.html
-->

## Sequence — UC-001 [FILL: name]

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant F as Frontend
    participant A as API
    participant B as Database
    U->>F: Fills in the form
    F->>A: POST /resource
    A->>A: Validates data
    alt valid data
        A->>B: INSERT
        B-->>A: id
        A-->>F: 201 Created
        F-->>U: Success message
    else invalid data
        A-->>F: 422 Validation errors
        F-->>U: Shows errors
    end
```

[FILL: notes on transactions, idempotency, timeouts]
