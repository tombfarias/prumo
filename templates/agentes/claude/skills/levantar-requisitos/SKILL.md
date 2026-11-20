---
name: levantar-requisitos
description: Transforma o briefing e as anotações do cliente no Documento de Visão (01-visao.md) e na Especificação de Requisitos (02-requisitos.md), com IDs RF/RNF/RN e perguntas em aberto. Use ao iniciar a especificação, ao receber novas informações do cliente ou quando pedirem requisitos.
---

# Levantar requisitos

## Entradas

- `docs/00-briefing.md` (obrigatório) e qualquer material que o usuário colar na conversa.
- Se o usuário trouxer material novo do cliente, **primeiro** registre-o no briefing (seção 10, reunião do dia), com as palavras do cliente.

## Procedimento

1. **Visão (`docs/01-visao.md`).** Preencha todas as seções a partir do briefing. Seja específico: nomes reais de perfis de usuário, números do negócio, prazos. A seção "Fora do escopo" é obrigatória: liste o que o cliente pode presumir que está incluído e não está (app mobile, integração X, migração de dados, treinamento...).
2. **Requisitos funcionais.** Um comportamento verificável por linha, começando por "O sistema deve...". Numere em sequência (RF-001, RF-002...) sem pular. Classifique com MoSCoW. Na coluna Origem, cite de onde veio (briefing, reunião de dd/mm, sugestão técnica).
3. **Requisitos não funcionais.** Sempre considere: segurança, privacidade (LGPD), desempenho, disponibilidade, compatibilidade de navegadores/dispositivos, acessibilidade, backup. Cada RNF precisa de métrica ou critério verificável.
4. **Regras de negócio.** Separe regras (cálculos, limites, prazos, permissões) dos requisitos. Dê um exemplo concreto para cada RN.
5. **Glossário.** Todo termo do negócio que aparecer mais de uma vez.
6. **Perguntas.** Toda lacuna que depende do cliente vira uma pergunta objetiva na seção 9 do briefing (de preferência de múltipla escolha). Não preencha lacunas com suposições: deixe `[PREENCHER: ...]` com a pergunta correspondente.

## Qualidade

- Requisito ambíguo ("rápido", "fácil", "moderno") → reescreva com critério mensurável ou transforme em pergunta.
- Requisitos que são soluções técnicas ("usar React") → vão para restrições da visão, não para RF.
- Verifique se cada capacidade da visão (seção 5.1) tem pelo menos um RF.

## Saída

Rode `{{prumo}} validar` e apresente: quantidade de RF/RNF/RN por prioridade, a lista de perguntas ao cliente e os riscos identificados.
