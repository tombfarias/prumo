---
name: planejar-testes
description: Escreve o plano de testes (09-plano-de-testes.md) com estratégia, ferramentas e casos de teste CT-xxx ligados às histórias e casos de uso, incluindo o roteiro de homologação com o cliente. Use quando pedirem plano de testes, casos de teste, critérios de homologação ou QA.
---

# Planejar testes

## Entradas

Backlog (critérios de aceite), casos de uso (fluxos de exceção), regras de negócio e RNF.

## Procedimento

1. **Estratégia:** preencha a tabela de níveis com as ferramentas da stack (ex.: Vitest/Jest/pytest, Testing Library, Playwright/Maestro).
2. **Casos de teste** (`### CT-00N — O que é verificado`):
   - linha `**Verifica:**` com as HU, UC, RF e RN cobertos;
   - tipo (unitário, integração, ponta a ponta, aceitação) e se é automatizado (com o caminho do arquivo quando existir);
   - pré-condição, passos e resultado esperado objetivos.
3. **Cobertura mínima, proporcional ao projeto:** cada critério de aceite das histórias Must tem um CT (critérios simples da mesma história podem ficar no mesmo CT); cada RN tem um teste unitário; cada fluxo de exceção relevante tem um teste. Histórias Could ganham CTs só se entrarem no escopo.
   - Para agrupar casos por épico ou história, use títulos como "## Testes do épico EP-01" ou "Testes de HU-003": não comece um título ou a primeira coluna de uma tabela com um ID definido em outro documento.
4. **Homologação:** roteiro para o cliente (casos de aceitação em linguagem não técnica) e critério de aceite da entrega.
5. Rode `{{prumo}} rastreabilidade` e confira "histórias sem caso de teste".

## Saída

Resumo: CTs criados por tipo, histórias sem cobertura, ambientes e dados de teste necessários.
