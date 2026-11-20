---
name: implementar-tela-figma
description: Implementa uma tela ou componente a partir do design no Figma usando o servidor MCP do Figma (contexto de design, captura, variáveis), mantendo o inventário de telas TL-xxx de 05-interface.md ligado aos casos de uso. Use quando houver link do Figma, quando pedirem para implementar uma tela/layout ou para sincronizar as telas do Figma com a documentação.
---

# Implementar tela a partir do Figma

## Pré-requisitos

- Servidor MCP do Figma conectado (`.mcp.json` já traz o remoto `https://mcp.figma.com/mcp`). Se as ferramentas do Figma não estiverem disponíveis, peça ao usuário para rodar `/mcp`, escolher **figma** e autenticar.
- Inventário de telas em `docs/05-interface.md`. Para preenchê-lo a partir do arquivo do Figma, o usuário roda `{{prumo}} figma telas <url-do-arquivo>` (precisa de `FIGMA_TOKEN`).

## A. Manter o inventário (etapa de especificação)

1. Para cada tela do inventário, preencha a coluna "Casos de uso" com os UC-xxx que ela atende (essa coluna é preservada nas sincronizações).
2. Nos casos de uso, cite as telas na linha "Telas".
3. Telas sem caso de uso ou casos de uso sem tela → pergunte ao usuário.

## B. Implementar uma tela

Argumento: `TL-00N` ou a URL de um frame do Figma.

1. Ache a tela no inventário e a URL do frame (com `node-id`). Leia os casos de uso ligados a ela.
2. Use as ferramentas do servidor MCP do Figma, nesta ordem:
   - contexto de design do frame (`get_design_context`), pedindo a saída na stack do projeto (ex.: React + Tailwind);
   - captura da tela (`get_screenshot`) para conferência visual;
   - variáveis e estilos (`get_variable_defs`) para mapear cores, tipografia e espaçamentos aos tokens do projeto.
3. **Adapte, não copie:** o código vindo do Figma é referência. Reaproveite os componentes existentes do projeto, use os tokens do design system e a estrutura definida em `AGENTS.md`. Nada de valores soltos (`#3A7BFF`, `13px`) se existir token equivalente.
4. Implemente os estados que o design costuma omitir: vazio, carregando, erro, sucesso; responsividade nos breakpoints de 05-interface.md; acessibilidade (rótulos, foco, contraste).
5. Ligue a tela ao comportamento dos casos de uso (validações, mensagens de erro dos fluxos de exceção).
6. Cite `// TL-00N · UC-00N` no componente da página.
7. Compare o resultado com a captura do Figma e liste as diferenças intencionais.

## Saída

Tela implementada, diferenças em relação ao design (e por quê) e pendências de conteúdo (textos e imagens finais do cliente).
