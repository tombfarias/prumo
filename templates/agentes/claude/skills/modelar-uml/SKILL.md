---
name: modelar-uml
description: Produz os diagramas UML em Mermaid (classes, sequência, estados, atividades, componentes, implantação) em docs/04-uml/, coerentes com os casos de uso e requisitos. Use quando pedirem diagramas UML, modelo de domínio, diagrama de sequência ou de componentes.
---

# Modelar UML

## Entradas

`docs/03-casos-de-uso.md`, `docs/02-requisitos.md` e, para componentes/implantação, `docs/07-arquitetura.md` se já existir.
Só trabalhe nos arquivos de `docs/04-uml/` que existem no projeto.

## Diagramas

| Arquivo | O que modelar |
|---|---|
| `classes.md` | Modelo de domínio: entidades (substantivos dos UCs), atributos essenciais, operações de negócio, enumerações, multiplicidades. Sem detalhes de framework. |
| `sequencia.md` | Um diagrama por caso de uso Must, com os participantes reais da arquitetura; use `alt`/`opt` para fluxos alternativos e de exceção. Título: `## Sequência — UC-00N Nome`. |
| `estados.md` | Entidades com ciclo de vida. Cada transição ligada a um passo de UC ou RN. |
| `atividades.md` | Processos de negócio ponta a ponta, inclusive etapas manuais fora do sistema. |
| `componentes.md` | Aplicações, módulos e integrações, com o protocolo de cada ligação. |
| `implantacao.md` | Onde cada componente roda: provedor, containers, banco gerenciado, CDN, CI/CD. |

## Regras de sintaxe Mermaid (evite erros de renderização)

- Comece o bloco com o tipo: `classDiagram`, `sequenceDiagram`, `stateDiagram-v2`, `flowchart LR|TD`, `erDiagram`.
- Em `flowchart`, textos com espaços, acentos, parênteses ou barras vão entre aspas: `a["Texto (com parênteses)"]`.
- IDs de nós sem espaços nem acentos (`cadastro_cliente`, não `cadastro cliente`).
- Não use `end` como ID de nó (é palavra reservada); use `fim`.
- Em `classDiagram`, genéricos com `~` (`List~Pedido~`), não `<>`.
- Em `sequenceDiagram`, mensagens de retorno com `-->>`.

## Coerência

- Classes ↔ tabelas de `06-banco-de-dados.md` (quando houver): nomes equivalentes.
- Cada caso de uso Must aparece em pelo menos um diagrama de sequência.
- Componentes ↔ seção "Módulos" de `07-arquitetura.md`.

## Saída

Rode `{{prumo}} validar` (verifica os blocos Mermaid) e `{{prumo}} diagramas` para extrair os `.mmd`. Se o projeto usa Figma, ofereça publicar os diagramas no FigJam com a skill `diagramas-figjam`.
