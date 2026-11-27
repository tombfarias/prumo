# Deployment Diagram — {{projeto}}

<!--
Where each component runs in production: providers, containers, domains, CDN,
managed database, queues, file storage, and how deployment happens.
-->

## 1. Production environment

```mermaid
flowchart TB
    user(["User"]) -- "HTTPS" --> cdn["CDN / Reverse proxy"]
    subgraph cloud["Cloud provider"]
        cdn --> app["Application container"]
        app --> db[("Managed PostgreSQL")]
        app --> storage[("File storage")]
    end
    ci["CI/CD"] -- "deploy" --> app
```

## 2. Environments

| Environment | URL | Infrastructure | Notes |
|---|---|---|---|
| Development | localhost | [FILL] | |
| Staging | [FILL] | [FILL] | Client validation |
| Production | [FILL] | [FILL] | |
