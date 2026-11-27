# Object Diagram — {{projeto}}

<!--
A snapshot of the class model at one moment: concrete instances with values, to validate
multiplicities and business rules (RN) with real examples before coding. Use the names from classes.md.
Notation: "name : Class"; attributes with values. Syntax: classDiagram with labels (https://mermaid.js.org/syntax/classDiagram.html)
-->

## Scenario — [FILL: sample situation, e.g. paid order with two items] (UC-001)

```mermaid
classDiagram
    direction LR
    class c1["c1 : Customer"] {
        name = "Mary Smith"
        active = true
    }
    class o1["o1 : Order"] {
        number = 1001
        status = Paid
        total = 150.00
    }
    class i1["i1 : OrderItem"] {
        quantity = 2
        price = 50.00
    }
    class i2["i2 : OrderItem"] {
        quantity = 1
        price = 50.00
    }
    c1 --> o1 : placed
    o1 *-- i1
    o1 *-- i2
```

| Object | Rule checked |
|---|---|
| [FILL: o1] | [FILL: RN-xxx — total = sum of the items] |
