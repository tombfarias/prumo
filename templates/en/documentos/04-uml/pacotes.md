# Package Diagram — {{projeto}}

<!--
Logical organization of the code into packages/modules and the allowed dependencies between them.
It must match the folder structure and the modules in 07-arquitetura.md: it is the "who may import whom" rule.
Dependency = dashed arrow with «import» or «use». Cycles between packages are forbidden.
-->

## 1. Packages and dependencies

```mermaid
flowchart TB
    subgraph presentation["«package» presentation"]
        screens["screens"]
        routes["routes"]
    end
    subgraph application["«package» application"]
        usecases["use_cases"]
    end
    subgraph domain["«package» domain"]
        entities["entities"]
        rules["rules"]
    end
    subgraph infra["«package» infrastructure"]
        repos["repositories"]
        integrations["integrations"]
    end
    presentation -. "«use»" .-> application
    application -. "«import»" .-> domain
    infra -. "«import»" .-> domain
    application -. "«use» (via interfaces)" .-> infra
```

## 2. Dependency rules

| Package | Folder | May depend on | Must not depend on |
|---|---|---|---|
| [FILL: domain] | [FILL: src/domain] | nothing | [FILL: infrastructure, presentation] |
