---
name: especificar-interface
description: Especifica a interface (05-interface.md) a partir dos requisitos e casos de uso, com inventário de telas TL-xxx, mapa de navegação em Mermaid, conteúdo e componentes de cada tela, estados e diretrizes de acessibilidade e responsividade. Use quando pedirem telas, páginas, wireframes, mapa do site, fluxo de navegação ou design system.
---

# Especificar a interface

## Entradas

`docs/02-requisitos.md` (RF, RNF), `docs/03-casos-de-uso.md` (se existir) e o pedido do cliente em `docs/00-briefing.md` (páginas, referências visuais, identidade).

## Procedimento

1. **Inventário de telas** (tabela da seção 2, entre os marcadores `prumo:figma`): uma linha por tela ou página, com ID `TL-001`, `TL-002`... na primeira coluna. Em sites, cada página e cada landing page é uma tela; telas de sistema agrupam o que o usuário vê junto (listagem e filtros na mesma tela). Na coluna "Casos de uso", cite os UC (ou, sem casos de uso, os RF) que a tela atende. Sem Figma, use `—` em "Página do Figma", "Link" e "Imagem".
   - Se o inventário já veio do Figma (`prumo figma telas`, com links preenchidos), mantenha as linhas e complete só a coluna "Casos de uso".
   - Se existir `docs/03-casos-de-uso.md`, atualize a linha "Telas" de cada caso de uso com as TL que o atendem (ou `—`).
2. **Mapa de navegação** (seção 3): troque o exemplo do modelo por um `flowchart` com as telas reais (`tl1["TL-001 Home"]`), as ligações entre elas e, quando houver, as entradas externas (anúncio, link de WhatsApp, e-mail).
3. **Detalhe de cada tela** (seção 4, uma subseção `### Tela TL-00N — Nome` por tela; o ID é definido no inventário, por isso o título começa por "Tela"): objetivo, blocos de conteúdo na ordem em que aparecem, ações (botões, formulários e para onde levam), dados exibidos, estados (vazio, carregando, erro, sucesso, quando se aplicam) e os RF/RNF/UC atendidos.
4. **Design system** (seção 1): preencha só o que o cliente informou (identidade, cores, fontes, referências) ou o que o perfil já define. O resto entra como proposta marcada ("Proposta: ...") ou como pergunta na seção 9 do briefing. Biblioteca de componentes só se fizer sentido para a stack.
5. **Diretrizes** (seção 5): acessibilidade com critério verificável (contraste WCAG AA, foco visível, `prefers-reduced-motion` quando houver animação), responsividade (dispositivos prioritários) e quem fornece textos e imagens.

## Qualidade

- A interface atende aos requisitos; não crie telas ou funções que o cliente não pediu. Se faltar uma tela óbvia (confirmação de envio, página de erro), inclua-a como Could e cite o RF relacionado.
- Todo RF que o usuário vê na tela aparece em pelo menos uma tela.
- Descreva conteúdo e comportamento, não pixels: o layout visual vem do Figma ou do designer.

## Saída

`{{prumo}} validar` sem erros e um resumo: telas criadas, RF sem tela e dúvidas sobre conteúdo e identidade visual.
