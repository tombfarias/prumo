---
name: levantar-requisitos
description: Transforma o briefing e as anotações do cliente no Documento de Visão (01-visao.md) e na Especificação de Requisitos (02-requisitos.md), com IDs RF/RNF/RN e perguntas em aberto. Use ao iniciar a especificação, ao receber novas informações do cliente ou quando pedirem requisitos.
---

# Levantar requisitos

## Entradas

- `docs/00-briefing.md` (obrigatório) e qualquer material que o usuário colar na conversa.
- `especificacao.prumo.json`, se existir: o formulário que o usuário preencheu na interface. Use os mesmos IDs das funcionalidades (RF-xxx) e regras (RN-xxx), a prioridade, o ator e os RNFs marcados; não os renumere.
- Se o usuário trouxer material novo do cliente, **primeiro** registre-o no briefing (seção 10, reunião do dia), com as palavras do cliente.

## Procedimento

1. **Visão (`docs/01-visao.md`).** Preencha a partir do briefing, sem completar com suposições. Seja específico com o que o cliente disse (perfis de usuário, números, prazos). O que ele não disse vira premissa marcada ("Premissa: ...") na seção 7 ou pergunta. A declaração do problema usa as palavras do cliente; se ele não descreveu o problema, deixe a lacuna ligada a uma pergunta. A seção "Fora do escopo" é obrigatória: liste o que o cliente pode presumir que está incluído e não está (app mobile, integração X, migração de dados, treinamento...).
2. **Requisitos funcionais.** Um comportamento verificável por linha, começando por "O sistema deve...". Numere em sequência (RF-001, RF-002...) sem pular. Classifique com MoSCoW: Must e Should são o escopo base; o que o cliente não pediu e você sugere entra como Could. Na coluna Origem, use: `Pedido` (está no briefing), `Reunião dd/mm`, `Premissa` (suposição a confirmar, cite a pergunta P-xx) ou `Sugestão técnica`.
3. **Requisitos não funcionais.** Considere segurança, privacidade (LGPD), desempenho, disponibilidade, compatibilidade, acessibilidade e backup, **na medida do porte do projeto**: um bot simples não precisa do mesmo conjunto de um SaaS. Cada RNF precisa de métrica ou critério verificável.
4. **Regras de negócio.** Separe regras (cálculos, limites, prazos, permissões) dos requisitos. Dê um exemplo concreto para cada RN. Regra que depende de resposta do cliente fica como premissa, citando a pergunta.
5. **Glossário.** Todo termo do negócio que aparecer mais de uma vez.
6. **Perguntas.** Toda lacuna que depende do cliente vira uma linha na tabela da seção 9 do briefing: ID `P-01`, pergunta objetiva (de preferência com alternativas), se bloqueia a proposta e o que impacta (RF, RN, estimativa). Marque como bloqueantes só as que mudam escopo ou preço. Não preencha lacunas com suposições silenciosas: ou premissa explícita, ou `[PREENCHER: ...]` com a pergunta correspondente.

## Qualidade

- Requisito ambíguo ("rápido", "fácil", "moderno") → reescreva com critério mensurável ou transforme em pergunta.
- Requisitos que são soluções técnicas ("usar React") → não são RF. Se o cliente impôs a tecnologia, vai para as restrições da visão; se é sugestão sua ou do perfil, vai para as premissas.
- Verifique se cada capacidade da visão (seção 5.1) tem pelo menos um RF e se cada item explícito do pedido do cliente aparece em algum RF, RNF ou restrição.
- Proporcional ao pedido: um pedido de duas frases gera uma especificação curta e muitas perguntas, não dezenas de requisitos inventados.

## Saída

Rode `{{prumo}} validar` e apresente: quantidade de RF/RNF/RN por prioridade, a lista de perguntas ao cliente e os riscos identificados.
