# State Diagrams — {{projeto}}

<!--
For entities with a lifecycle (order, ticket, subscription, payment...).
Each transition must match a use case step or a business rule (RN).
Syntax: https://mermaid.js.org/syntax/stateDiagram.html
-->

## States — [FILL: entity]

```mermaid
stateDiagram-v2
    [*] --> Open
    Open --> Paid: payment confirmed
    Open --> Canceled: cancellation requested
    Paid --> Shipped: dispatch
    Shipped --> Delivered: delivery confirmed
    Canceled --> [*]
    Delivered --> [*]
```

| Transition | Trigger | Business rule |
|---|---|---|
| [FILL] | [FILL] | [FILL: RN-xxx] |
