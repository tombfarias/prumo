---
name: diagramas-figjam
description: Publica os diagramas Mermaid da especificação (UML, casos de uso, ER, navegação) como diagramas no FigJam usando o servidor MCP do Figma, para revisar e comentar com o cliente. Use quando pedirem para levar diagramas ao Figma/FigJam ou apresentar a modelagem ao cliente visualmente.
---

# Diagramas no FigJam

## Pré-requisitos

Servidor MCP do Figma conectado (`/mcp` → figma → autenticar). A ferramenta de geração de diagramas do servidor (`generate_diagram`) cria um diagrama no FigJam a partir de código Mermaid.

## Procedimento

1. Rode `{{prumo}} validar` para garantir que os blocos Mermaid estão corretos e `{{prumo}} diagramas` para extraí-los em `docs/diagramas/*.mmd`.
2. Pergunte ao usuário quais diagramas publicar (sugestão: casos de uso, classes, ER e sequências dos UCs principais).
3. Para cada diagrama escolhido, chame a ferramenta de geração de diagramas do Figma com o conteúdo do `.mmd` e um título no formato `{{projeto}} — <documento> — <diagrama>`.
4. Registre os links retornados no documento de origem, logo abaixo do bloco Mermaid: `> FigJam: <link> (publicado em dd/mm/aaaa)`.
5. Se o diagrama for de um documento aprovado, não edite o documento: entregue os links ao usuário.

## Observações

- O Mermaid continua sendo a fonte da verdade; o FigJam é uma cópia para revisão. Ao mudar a especificação, publique de novo.
- Comentários do cliente no FigJam que mudem escopo seguem a skill `controle-de-mudancas`.
