---
name: planejar-arquitetura
description: Define a arquitetura (07-arquitetura.md) e registra decisões em ADRs: stack com versões, estrutura de pastas, módulos, integrações, segurança, ambientes e CI/CD. Use quando pedirem arquitetura, escolha de stack, estrutura do projeto ou decisões técnicas.
---

# Planejar a arquitetura

## Entradas

Requisitos (especialmente RNF), casos de uso, modelo de dados, diagramas de componentes/implantação e a stack sugerida em `AGENTS.md`.

## Procedimento

1. **Estilo arquitetural** adequado ao porte: para projetos freelance, prefira monólito modular bem organizado a microsserviços, salvo motivo forte.
2. **Stack:** confirme a stack do perfil ou proponha ajuste justificado pelos requisitos. Informe versões estáveis atuais (verifique na documentação oficial; não chute versões).
3. **Estrutura de pastas** concreta (árvore) seguindo as convenções do perfil em `AGENTS.md`.
4. **Módulos:** cada módulo com responsabilidade e casos de uso que atende.
5. **Integrações externas:** autenticação, limites, custos e tratamento de falhas.
6. **Segurança:** autenticação, autorização (matriz de perfis), segredos, dados sensíveis.
7. **Operação:** ambientes, logs, monitoramento, CI/CD, custo mensal estimado de infraestrutura (o cliente precisa saber).
8. **ADRs:** para cada decisão relevante e difícil de reverter (banco, provedor de hospedagem, autenticação, multi-tenant, framework), rode `{{prumo}} adr "título"`, preencha o arquivo criado em `docs/adr/` e liste-o na seção 8.
9. **Comandos do projeto:** proponha ao usuário os valores de `comandos` (formatar, lint, testar) em `projeto.prumo.json` de acordo com a stack.

## Saída

`{{prumo}} validar` sem erros; resumo da stack, ADRs criados e custo estimado de infraestrutura.
