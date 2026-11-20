---
name: controle-de-mudancas
description: Trata pedidos de alteração do cliente depois que a especificação foi aprovada, registrando um pedido de mudança (CM-xxx) com análise de impacto em requisitos, casos de uso, histórias, telas, dados, prazo e custo. Use quando o cliente pedir algo novo ou diferente do combinado, ou quando um documento aprovado precisar mudar.
---

# Controle de mudanças

Em projetos freelance, mudança não registrada vira prejuízo. Esta skill garante que toda alteração de escopo seja analisada e aprovada antes de entrar no projeto.

## Procedimento

1. **Registrar:** rode `{{prumo}} mudanca "título curto"` e preencha o arquivo criado em `docs/mudancas/` com a descrição nas palavras do cliente e o motivo.
2. **Classificar:** é correção de defeito (o sistema não faz o que foi especificado; não é mudança), esclarecimento (o documento era ambíguo) ou mudança de escopo (algo novo ou diferente)?
3. **Analisar impacto:** percorra a rastreabilidade (`{{prumo}} rastreabilidade`) e liste cada RF, RN, UC, TL, HU, CT, tabela e ADR afetado, com a alteração necessária.
4. **Estimar:** horas adicionais (crie as HUs novas no próprio CM como proposta), impacto no prazo dos marcos e no custo (valor da hora de `prumo orcamento`).
5. **Apresentar ao usuário** um resumo para enviar ao cliente: o que muda, quanto custa, quanto atrasa, alternativas (fazer agora, fase 2, versão simplificada).

## Depois da aprovação do cliente

Só o usuário remove a proteção: `prumo desaprovar <arquivo>`. Então atualize os documentos afetados citando o `CM-xxx` (ex.: na coluna Origem dos requisitos), marque o CM como aprovado, e o usuário aprova de novo: `prumo aprovar <arquivo>`.

Nunca edite documentos aprovados nem implemente a mudança antes da aprovação registrada.
