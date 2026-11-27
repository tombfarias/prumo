---
name: implementar-tela-figma
description: Implements a screen or component from the Figma design using the Figma MCP server (design context, screenshot, variables), keeping the TL-xxx screen inventory in 05-interface.md linked to the use cases. Use when there is a Figma link, when asked to implement a screen/layout or to sync the Figma screens with the documentation.
---

# Implement a screen from Figma

## Prerequisites

- Figma MCP server connected (`.mcp.json` already includes the remote `https://mcp.figma.com/mcp`). If the Figma tools are not available, ask the user to run `/mcp`, choose **figma** and authenticate.
- Screen inventory in `docs/05-interface.md`. To fill it in from the Figma file, the user runs `{{prumo}} figma telas <file-url>` (needs `FIGMA_TOKEN`).

## A. Keep the inventory (specification step)

1. For each screen in the inventory, fill in the "Use cases" column with the UC-xxx it serves (this column is kept across syncs).
2. In the use cases, cite the screens in the "Screens" row.
3. Screens without a use case or use cases without a screen → ask the user.

## B. Implement a screen

Argument: `TL-00N` or the URL of a Figma frame.

1. Find the screen in the inventory and the frame URL (with `node-id`). Read the use cases linked to it.
2. Use the Figma MCP server tools, in this order:
   - the frame's design context (`get_design_context`), asking for output in the project's stack (e.g. React + Tailwind);
   - the screen capture (`get_screenshot`) for visual checking;
   - variables and styles (`get_variable_defs`) to map colors, typography and spacing to the project tokens.
3. **Adapt, do not copy:** the code from Figma is a reference. Reuse the project's existing components, use the design system tokens and the structure defined in `AGENTS.md`. No loose values (`#3A7BFF`, `13px`) if an equivalent token exists.
4. Implement the states the design usually omits: empty, loading, error, success; responsiveness at the breakpoints in 05-interface.md; accessibility (labels, focus, contrast).
5. Wire the screen to the behavior of the use cases (validations, error messages of the exception flows).
6. Cite `// TL-00N · UC-00N` in the page component.
7. Compare the result with the Figma capture and list the intentional differences.

## Output

Screen implemented, differences from the design (and why) and pending content (final texts and images from the client).
