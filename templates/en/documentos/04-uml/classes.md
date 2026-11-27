# Class Diagram (Domain Model) — {{projeto}}

<!--
Model the domain entities and their relationships from the use cases
(recurring nouns = class candidates; verbs = operation candidates).
Keep it consistent with 06-banco-de-dados.md when there is persistence.
Syntax: https://mermaid.js.org/syntax/classDiagram.html
-->

## 1. Diagram

```mermaid
classDiagram
    direction LR
    class Customer {
        +UUID id
        +String name
        +String email
        +register()
    }
    class Order {
        +UUID id
        +Date date
        +OrderStatus status
        +calculateTotal() Decimal
    }
    class OrderStatus {
        <<enumeration>>
        OPEN
        PAID
        CANCELLED
    }
    Customer "1" --> "0..*" Order : places
    Order --> OrderStatus
```

## 2. Responsibilities

| Class | Responsibility | Related use cases |
|---|---|---|
| [FILL] | [FILL] | [FILL: UC-xxx] |

## 3. Design notes

[FILL: invariants, aggregates, value objects, modeling decisions]
