# Diagrama de Componentes — {{projeto}}

<!--
Visão estrutural: aplicações, serviços, módulos internos e integrações externas,
com o protocolo de cada ligação. Deve bater com 07-arquitetura.md.
-->

## 1. Componentes e dependências

```mermaid
flowchart LR
    subgraph cliente["Cliente"]
        web["Aplicação web"]
    end
    subgraph servidor["Servidor"]
        api["API REST"]
        auth["Módulo de autenticação"]
        jobs["Processamento assíncrono"]
    end
    db[("Banco de dados")]
    ext["Serviço externo"]
    web -- "HTTPS/JSON" --> api
    api --> auth
    api --> db
    api -- "fila" --> jobs
    jobs -- "HTTPS" --> ext
```

## 2. Descrição

| Componente | Responsabilidade | Tecnologia |
|---|---|---|
| [PREENCHER] | [PREENCHER] | [PREENCHER] |
