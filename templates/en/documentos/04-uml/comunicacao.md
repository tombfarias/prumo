# Communication Diagrams — {{projeto}}

<!--
The same interaction as a sequence diagram, but focused on the links between objects.
Use it when "who talks to whom" (coupling) matters, not the timeline. Numbered messages (1, 1.1, 2...).
Title of each section: "## Communication — UC-001 Name". Syntax: flowchart with edge labels.
-->

## Communication — UC-001 [FILL: name]

```mermaid
flowchart LR
    u(["user : User"])
    f["screen : Frontend"]
    a["api : API"]
    s["service : OrderService"]
    b[("db : Database")]
    u -- "1: submit form" --> f
    f -- "2: POST /orders" --> a
    a -- "2.1: create(data)" --> s
    s -- "2.1.1: save(order)" --> b
    a -. "3: 201 Created" .-> f
```

[FILL: notes on coupling or objects with many links]
