# Class Diagram (Domain Model) — {{projeto}}

<!--
Model the domain entities and their relationships from the use cases
(recurring nouns = class candidates; verbs = operation candidates).
Keep it consistent with 06-banco-de-dados.md when there is persistence.
Syntax: https://mermaid.js.org/syntax/classDiagram.html
-->

## 1. Diagram

<!-- prumo:gerado:diagrama -->
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
<!-- prumo:gerado:fim -->

## 2. Responsibilities

<!-- prumo:gerado:responsabilidades -->
| Class | Responsibility | Related use cases |
|---|---|---|
| [FILL] | [FILL] | [FILL: UC-xxx] |
<!-- prumo:gerado:fim -->

## 3. Design notes

[FILL: invariants, aggregates, value objects, modeling decisions]
