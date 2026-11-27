---
name: gerar-backlog
description: Quebra os casos de uso em épicos e histórias de usuário (08-backlog.md) com critérios de aceite em Dado/Quando/Então, estimativas em horas, prioridade e marcos de entrega; depois gera o orçamento. Use quando pedirem backlog, histórias, estimativas, planejamento de sprints ou cronograma.
---

# Gerar o backlog

## Entradas

Casos de uso, requisitos, arquitetura e, se houver, telas (05-interface.md).

## Procedimento

1. **Épicos** (`EP-01`...): um por área funcional ou marco de entrega.
2. **Histórias** (`### HU-00N — Título`): cada história entrega valor verificável e cabe em até 2 dias de trabalho (≤ 16h). Divida as maiores.
   - Linha de rastreio: `**Épico:** EP-0N · **Casos de uso:** UC-00N · **Requisitos:** RF-00N`.
   - Formato "Como / quero / para".
   - Critérios de aceite em Dado/Quando/Então, cobrindo fluxo principal e as exceções do caso de uso.
   - `**Estimativa:** 6h` (formato lido por `prumo orcamento`), prioridade MoSCoW e status `a fazer`.
   - Nos títulos dos épicos ou em outras tabelas, não comece a linha pelo ID já definido (use "Épico EP-01 — ..."): cada ID é definido uma vez.
3. **Escopo base e opcionais.** A prioridade da história segue a do requisito: Must e Should formam o escopo base; **Could são opcionais** e `prumo orcamento` os soma à parte, fora do total. Won't não entra no orçamento. Liste os opcionais numa seção própria, com as horas de cada um, para o cliente escolher.
4. **Histórias técnicas** só as necessárias para entregar o escopo (configuração, deploy, migração de dados quando houver). CI/CD, monitoramento, rotinas de LGPD e afins na medida do porte: em projetos pequenos, um item simples ou opcional. Elas citam os RNF atendidos.
5. **Estimativas:** some tempo de testes e revisão a cada história. Registre premissas da estimativa quando houver incerteza alta e sinalize as histórias de maior risco. Não escreva percentual de contingência próprio: a contingência vem da configuração e aparece em `docs/orcamento.md`.
6. **Marcos** (`M1`, `M2`...): agrupe épicos em entregas que o cliente consegue validar, com percentual de pagamento sugerido.
7. Rode `{{prumo}} orcamento` para gerar `docs/orcamento.md` e `{{prumo}} rastreabilidade` para ver casos de uso sem história.

## Saída

Resumo: número de histórias por épico e por prioridade, horas do escopo base e dos opcionais e histórias sem estimativa.
