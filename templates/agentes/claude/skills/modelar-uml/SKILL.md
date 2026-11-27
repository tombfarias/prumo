---
name: modelar-uml
description: Produz os 14 diagramas da UML 2.5 em Mermaid (classes, objetos, pacotes, componentes, estrutura composta, implantação, perfil, casos de uso, sequência, comunicação, tempo, visão geral de interação, estados, atividades) em docs/04-uml/, coerentes com casos de uso e requisitos. Use quando pedirem diagramas UML, modelo de domínio, sequência, componentes ou qualquer outro tipo UML.
---

# Modelar UML

## Entradas

`docs/03-casos-de-uso.md`, `docs/02-requisitos.md` e, para componentes/pacotes/implantação, `docs/07-arquitetura.md` se já existir.
Só trabalhe nos arquivos de `docs/04-uml/` que existem no projeto (o perfil já escolheu os que valem a pena).
Faça na ordem da tabela: os estruturais primeiro (o domínio), depois os comportamentais (que usam os nomes do domínio).

## Diagramas (UML 2.5)

| Tipo UML | Arquivo | Mermaid | O que modelar |
|---|---|---|---|
| Classes | `classes.md` | `classDiagram` | Domínio: entidades (substantivos dos UCs), atributos essenciais, operações de negócio, enumerações, multiplicidades. Sem framework. |
| Objetos | `objetos.md` | `classDiagram` com `class c1["c1 : Classe"]` | Instâncias de exemplo com valores, uma por cenário que testa uma RN ou multiplicidade. |
| Pacotes | `pacotes.md` | `flowchart` + `subgraph` | Pacotes = pastas/módulos de `07-arquitetura.md`; setas `-.->` «import»/«use»; sem ciclos. Tabela "pode/não pode depender". |
| Componentes | `componentes.md` | `flowchart` | Aplicações, módulos e integrações, com o protocolo de cada ligação. |
| Estrutura composta | `estrutura-composta.md` | `flowchart` + `subgraph` | Só componentes com partes internas relevantes: partes `nome : Tipo [mult]`, portas `(("porta"))`, conectores. |
| Implantação | `implantacao.md` | `flowchart` | Onde cada componente roda: provedor, containers, banco gerenciado, CDN, CI/CD. |
| Perfil | `perfil-uml.md` | `classDiagram` com `<<metaclass>>`/`<<stereotype>>` | Só os estereótipos usados nos outros diagramas, com valores etiquetados e a regra que impõem ao código. |
| Casos de uso | `../03-casos-de-uso.md` | `flowchart` | Já feito na etapa de casos de uso; só confira se bate com as sequências. |
| Sequência | `sequencia.md` | `sequenceDiagram` | Um por UC Must, participantes reais; `alt`/`opt` para alternativos e exceções. Título `## Sequência — UC-00N Nome`. |
| Comunicação | `comunicacao.md` | `flowchart` com rótulos `"1: msg"`, `"1.1: msg"` | UCs onde o acoplamento importa; mesmas mensagens da sequência. Título `## Comunicação — UC-00N Nome`. |
| Tempo | `tempo.md` | tabela + `gantt` (`dateFormat X`, eixo em segundos) | Timeouts, SLAs, expiração, agendamentos; cada restrição cita RNF/RN. A tabela é a fonte de verdade. |
| Visão geral de interação | `visao-geral-interacao.md` | `flowchart TD` | Jornada entre UCs: nós `ref: UC-00N`, decisões, fork/join; detalhes ficam nas sequências. |
| Máquina de estados | `estados.md` | `stateDiagram-v2` | Entidades com ciclo de vida. Cada transição ligada a um passo de UC ou RN. |
| Atividades | `atividades.md` | `flowchart` | Processos de negócio ponta a ponta, inclusive etapas manuais fora do sistema. |

Diagrama sem conteúdo real no projeto (ex.: nada com prazo para `tempo.md`): escreva uma linha dizendo por quê e remova o exemplo; não invente.

## Regras de sintaxe Mermaid (evite erros de renderização)

- Comece o bloco com o tipo: `classDiagram`, `sequenceDiagram`, `stateDiagram-v2`, `flowchart LR|TD`, `erDiagram`, `gantt`.
- Em `flowchart`, textos com espaços, acentos, parênteses, dois-pontos ou barras vão entre aspas: `a["Texto (com parênteses)"]`.
- IDs de nós sem espaços nem acentos (`cadastro_cliente`, não `cadastro cliente`).
- Não use `end` como ID de nó (é palavra reservada); use `fim`.
- Em `classDiagram`, genéricos com `~` (`List~Pedido~`), não `<>`; rótulo de instância com `class id["id : Classe"]`.
- Em `sequenceDiagram`, mensagens de retorno com `-->>`.

## Coerência

- Classes ↔ tabelas de `06-banco-de-dados.md` (quando houver): nomes equivalentes. Objetos usam só classes e atributos de `classes.md`.
- Cada caso de uso Must aparece em pelo menos um diagrama de sequência; comunicação e visão geral citam os mesmos UC-xxx.
- Componentes e pacotes ↔ seção "Módulos" e estrutura de pastas de `07-arquitetura.md`.
- Estereótipos usados em qualquer diagrama estão definidos em `perfil-uml.md`.

## Saída

Rode `{{prumo}} validar` (verifica os blocos Mermaid) e `{{prumo}} diagramas` para extrair os `.mmd`. Se o projeto usa Figma, ofereça publicar os diagramas no FigJam com a skill `diagramas-figjam`.
