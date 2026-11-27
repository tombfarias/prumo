---
name: especificar-projeto
description: Conduz a especificação completa do projeto, do briefing ao backlog e à proposta, etapa por etapa, com validação e pausa para revisão do usuário entre as etapas. Use quando pedirem para especificar o projeto, documentar o sistema do zero ou "rodar o fluxo do Prumo".
---

# Especificar o projeto (fluxo completo)

Você conduz a especificação de `{{projeto}}` em etapas. Cada etapa tem uma skill própria com as instruções detalhadas. **Não pule etapas** e **não avance sem o usuário revisar** a etapa anterior, a não ser que ele peça para seguir direto.

## Antes de começar

1. Rode `{{prumo}} status` para ver quais documentos existem e quantas lacunas `[PREENCHER]` cada um tem.
2. Leia `docs/00-briefing.md`. Se estiver vazio, peça ao usuário as anotações do cliente (e-mails, áudios transcritos, mensagens) e preencha o briefing primeiro, sem inventar nada.
3. Se `projeto.prumo.json` tiver `"existente": true`, o código já existia: rode antes a skill `mapear-projeto-existente` (os documentos descrevem o que existe) e use o fluxo abaixo só para o trabalho novo.
4. Leia `projeto.prumo.json` para saber quais documentos fazem parte deste perfil. Pule as etapas cujos documentos não existem.

## Etapas

| # | Etapa | Skill | Documentos |
|---|---|---|---|
| 1 | Visão e requisitos | `levantar-requisitos` | 01-visao.md, 02-requisitos.md |
| 2 | Casos de uso | `especificar-casos-de-uso` | 03-casos-de-uso.md |
| 3 | Interface (se houver) | `especificar-interface` | 05-interface.md |
| 4 | Modelagem UML | `modelar-uml` | 04-uml/*.md |
| 5 | Banco de dados | `modelar-banco` | 06-banco-de-dados.md |
| 6 | Arquitetura | `planejar-arquitetura` | 07-arquitetura.md, docs/adr/ |
| 7 | Backlog e estimativas | `gerar-backlog` | 08-backlog.md |
| 8 | Plano de testes | `planejar-testes` | 09-plano-de-testes.md |
| 9 | Proposta comercial | `proposta-comercial` | 10-proposta-comercial.md, orcamento.md |

## Ao final de cada etapa

1. Rode `{{prumo}} validar` e corrija os erros (IDs indefinidos, Mermaid inválido).
2. Mostre ao usuário um resumo curto: o que foi criado, lacunas que ficaram e as perguntas para o cliente que surgiram (registradas na seção 9 do briefing).
3. Pergunte se pode seguir para a próxima etapa.

## Ao final do fluxo

- Rode `{{prumo}} rastreabilidade` e `{{prumo}} orcamento`.
- Sugira ao usuário quais documentos enviar ao cliente para aprovação. Depois da aprovação, **o usuário** roda `prumo aprovar <arquivo>`; você não aprova documentos.
