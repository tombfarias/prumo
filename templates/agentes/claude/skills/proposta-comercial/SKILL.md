---
name: proposta-comercial
description: Monta a proposta comercial (10-proposta-comercial.md) para o cliente a partir da visão, do backlog e do orçamento gerado pelo Prumo, em linguagem não técnica. Use quando pedirem proposta, orçamento para o cliente, cronograma comercial ou condições de pagamento.
---

# Proposta comercial

## Entradas

`docs/01-visao.md` (escopo e fora do escopo), `docs/08-backlog.md` (épicos e marcos) e `docs/orcamento.md`. Se `orcamento.md` não existir ou estiver desatualizado, rode `{{prumo}} orcamento` antes.

## Procedimento

1. Escreva para o cliente, não para desenvolvedores: benefícios e resultados, sem jargão.
2. **Responda ao que o cliente pediu na proposta.** Se o pedido lista o que a proposta deve trazer (portfólio, tecnologias recomendadas, prazo, etapas, suporte...), cada item precisa de uma seção ou linha. Portfólio é do freelancer: deixe `[PREENCHER: links de projetos semelhantes]`.
3. **Escopo incluído** = épicos do escopo base; **opcionais** = histórias Could, cada uma com as horas, para o cliente escolher; **não incluído** = seção "Fora do escopo" da visão, mais itens comuns que o cliente pode presumir (hospedagem, domínio, conteúdo, fotos, manutenção mensal).
4. **Cronograma** = marcos do backlog, com prazo e percentual de pagamento. O prazo considera as horas com contingência.
5. **Investimento:** use os totais de `docs/orcamento.md` (escopo base com contingência; opcionais à parte). Não invente valores. Se o valor da hora não estiver configurado, deixe o cálculo indicado (`N h × valor da hora`).
6. **Custos recorrentes do cliente** (hospedagem, APIs pagas, lojas de apps) vêm de `07-arquitetura.md`.
7. **Perguntas bloqueantes:** liste, em linguagem simples, as perguntas da seção 9 do briefing marcadas como bloqueantes e diga o que pode mudar no preço conforme a resposta.
8. **Garantia, suporte, mudanças de escopo e propriedade intelectual:** use as condições que o usuário informar. Na falta delas, proponha termos usuais de freelance marcados como proposta (ex.: 30 dias de correção de defeitos após a entrega; código e direitos transferidos após a quitação; mudanças de escopo orçadas à parte) e lembre o usuário de revisá-los (não é aconselhamento jurídico).

## Saída

Proposta pronta para revisão, com lacunas só no que é do freelancer (valor da hora, portfólio, dados de contato) e uma lista objetiva do que o usuário precisa decidir.
