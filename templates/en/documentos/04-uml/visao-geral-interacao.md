# Interaction Overview — {{projeto}}

<!--
Control flow between interactions: each "ref" node points to a sequence diagram (sequencia.md) or a communication diagram.
It shows the full journey (order of use cases, decisions, parallelism) without repeating the details of each interaction.
Syntax: flowchart; "ref" nodes in rectangles, decisions in diamonds, parallelism with fork/join.
-->

## Journey — [FILL: name, e.g. full purchase]

```mermaid
flowchart TD
    start((" ")) --> login["ref: UC-001 Authenticate"]
    login --> authenticated{"authenticated?"}
    authenticated -- "no" --> error_exit(((" ")))
    authenticated -- "yes" --> cart["ref: UC-002 Build cart"]
    cart --> fork[" "]
    fork --> payment["ref: UC-003 Pay"]
    fork --> stock["ref: UC-004 Reserve stock"]
    payment --> join[" "]
    stock --> join
    join --> finish(((" ")))
```

| Node | Detailed diagram |
|---|---|
| [FILL: UC-001] | [FILL: sequencia.md — Sequence — UC-001] |
