---
name: especificar-casos-de-uso
description: Escreve os casos de uso (03-casos-de-uso.md) a partir dos requisitos, com atores, diagrama Mermaid, fluxos principal, alternativos e de exceção, e rastreabilidade para RF/RN/TL. Use quando pedirem casos de uso, fluxos do usuário ou cenários do sistema.
---

# Especificar casos de uso

## Entradas

`docs/02-requisitos.md` (RF, RN), `docs/01-visao.md` (usuários) e, se existir, `docs/05-interface.md` (telas).

## Procedimento

1. **Atores.** Liste atores humanos (por papel, não por pessoa) e sistemas externos.
2. **Identifique os casos de uso** agrupando RFs que formam um objetivo completo do ator ("Emitir nota fiscal", não "Clicar em emitir"). CRUDs simples podem ser um único caso "Manter X" com fluxos para incluir/alterar/excluir/consultar.
3. **Diagrama.** Atualize o flowchart Mermaid da seção 2: atores fora do `subgraph` do sistema, um nó `((UC-00N Nome))` por caso de uso, ligações ator–caso. Use `-.->|inclui|` e `-.->|estende|` quando fizer sentido.
4. **Especificação de cada caso** no formato do modelo (`### UC-00N — Nome`):
   - linha "Requisitos atendidos" com todos os RF/RNF cobertos; "Regras de negócio" com as RN aplicadas; "Telas" com TL-xxx quando houver interface;
   - fluxo principal numerado, alternando ator e sistema, de 4 a 12 passos;
   - fluxos alternativos referenciando o passo de origem (`FA-01 (passo 3)`);
   - fluxos de exceção para validação, permissão negada, falha de integração e indisponibilidade.
5. **Cobertura.** Todo RF de prioridade Must ou Should deve estar em pelo menos um caso de uso. Rode `{{prumo}} rastreabilidade` e confira a seção de problemas.

## Qualidade

- Passos descrevem intenção, não interface ("informa os dados do cliente", não "clica no botão azul").
- Nada de requisitos novos aqui: se surgir algo que não está em 02-requisitos.md, pare e pergunte ao usuário se deve virar um RF.

## Saída

`{{prumo}} validar` sem erros e um resumo: casos de uso criados, RFs ainda sem cobertura, dúvidas.
