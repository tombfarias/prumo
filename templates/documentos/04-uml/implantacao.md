# Diagrama de Implantação — {{projeto}}

<!--
Onde cada componente roda em produção: provedores, containers, domínios, CDN,
banco gerenciado, filas, armazenamento de arquivos, e como o deploy acontece.
-->

## 1. Ambiente de produção

```mermaid
flowchart TB
    usuario(["Usuário"]) -- "HTTPS" --> cdn["CDN / Proxy reverso"]
    subgraph nuvem["Provedor de nuvem"]
        cdn --> app["Container da aplicação"]
        app --> db[("PostgreSQL gerenciado")]
        app --> storage[("Armazenamento de arquivos")]
    end
    ci["CI/CD"] -- "deploy" --> app
```

## 2. Ambientes

| Ambiente | URL | Infraestrutura | Observações |
|---|---|---|---|
| Desenvolvimento | localhost | [PREENCHER] | |
| Homologação | [PREENCHER] | [PREENCHER] | Validação com o cliente |
| Produção | [PREENCHER] | [PREENCHER] | |
