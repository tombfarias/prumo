# Arquitetura — {{projeto}}

| Campo | Valor |
|---|---|
| Perfil | {{perfil_nome}} |
| Stack proposta | {{stack}} |
| Versão | 0.1 |

<!--
Explica COMO o sistema será construído. Decisões relevantes e difíceis de reverter
viram ADRs em docs/adr/ (`prumo adr "título"`) e são listadas na seção 8.
-->

## 1. Visão geral

[PREENCHER: estilo arquitetural (monólito modular, SPA + API, serverless...) e por quê]

## 2. Stack

<!-- prumo:gerado:stack -->
| Camada | Tecnologia | Versão | Justificativa |
|---|---|---|---|
| [PREENCHER] | [PREENCHER] | [PREENCHER] | [PREENCHER] |
<!-- prumo:gerado:fim -->

## 3. Estrutura de pastas

```text
[PREENCHER: árvore de diretórios do código]
```

## 4. Módulos e responsabilidades

| Módulo | Responsabilidade | Casos de uso |
|---|---|---|
| [PREENCHER] | [PREENCHER] | [PREENCHER: UC-xxx] |

## 5. Integrações externas

<!-- prumo:gerado:integracoes -->
| Sistema | Finalidade | Protocolo / autenticação | Tratamento de falhas |
|---|---|---|---|
| [PREENCHER] | [PREENCHER] | [PREENCHER] | [PREENCHER: retry, fila, fallback] |
<!-- prumo:gerado:fim -->

## 6. Segurança

<!-- prumo:gerado:seguranca -->
- **Autenticação:** [PREENCHER]
- **Autorização / perfis de acesso:** [PREENCHER]
- **Segredos:** variáveis de ambiente; nunca versionadas (`.env` fica fora do git, `.env.example` documenta as chaves).
- **Dados sensíveis:** [PREENCHER: criptografia, mascaramento em logs]
<!-- prumo:gerado:fim -->

## 7. Qualidade e operação

- **Padrões de código:** ver AGENTS.md
- **Testes:** ver 09-plano-de-testes.md
- **Logs e monitoramento:** [PREENCHER]
- **CI/CD:** [PREENCHER: pipeline de build, testes e deploy]
- **Ambientes:** ver 04-uml/implantacao.md

## 8. Decisões arquiteturais (ADRs)

| ADR | Título | Status |
|---|---|---|
| [PREENCHER: ADR-xxx, criado com `prumo adr`] | [PREENCHER] | Proposta |
