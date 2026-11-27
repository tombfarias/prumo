# Activity Diagrams (Processes) — {{projeto}}

<!--
End-to-end business processes, including steps outside the system (manual ones).
Useful to validate with the client "how it works today" and "how it will work".
Syntax: https://mermaid.js.org/syntax/flowchart.html
-->

## Process — [FILL: process name]

```mermaid
flowchart TD
    inicio([Start]) --> a1[Customer sends a request]
    a1 --> d1{Data complete?}
    d1 -- No --> a2[Ask for the missing data]
    a2 --> a1
    d1 -- Yes --> a3[Record in the system]
    a3 --> a4[Notify the person in charge]
    a4 --> fim([Finish])
```

[FILL: owner of each step, SLAs, automation points]
