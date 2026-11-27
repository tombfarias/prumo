---
name: diagramas-figjam
description: Publishes the specification's Mermaid diagrams (UML, use cases, ER, navigation) as FigJam diagrams using the Figma MCP server, to review and comment on with the client. Use when asked to take diagrams to Figma/FigJam or to present the modeling to the client visually.
---

# Diagrams in FigJam

## Prerequisites

Figma MCP server connected (`/mcp` → figma → authenticate). The server's diagram tool (`generate_diagram`) creates a FigJam diagram from Mermaid code.

## Procedure

1. Run `{{prumo}} validar` to make sure the Mermaid blocks are correct and `{{prumo}} diagramas` to extract them to `docs/diagramas/*.mmd`.
2. Ask the user which diagrams to publish (suggestion: use cases, classes, ER and the sequences of the main UCs).
3. For each chosen diagram, call the Figma diagram tool with the content of the `.mmd` and a title in the format `{{projeto}} — <document> — <diagram>`.
4. Record the returned links in the source document, right below the Mermaid block: `> FigJam: <link> (published on yyyy-mm-dd)`.
5. If the diagram belongs to an approved document, do not edit the document: give the links to the user.

## Notes

- Mermaid stays the source of truth; FigJam is a copy for review. When the specification changes, publish again.
- Client comments in FigJam that change scope follow the `controle-de-mudancas` skill.
