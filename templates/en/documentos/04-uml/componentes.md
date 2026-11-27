# Component Diagram — {{projeto}}

<!--
Structural view: applications, services, internal modules and external integrations,
with the protocol of each link. Must match 07-arquitetura.md.
-->

## 1. Components and dependencies

```mermaid
flowchart LR
    subgraph cliente["Client"]
        web["Web application"]
    end
    subgraph servidor["Server"]
        api["REST API"]
        auth["Authentication module"]
        jobs["Asynchronous processing"]
    end
    db[("Database")]
    ext["External service"]
    web -- "HTTPS/JSON" --> api
    api --> auth
    api --> db
    api -- "queue" --> jobs
    jobs -- "HTTPS" --> ext
```

## 2. Description

| Component | Responsibility | Technology |
|---|---|---|
| [FILL] | [FILL] | [FILL] |
