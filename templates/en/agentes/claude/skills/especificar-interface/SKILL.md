---
name: especificar-interface
description: Specifies the interface (05-interface.md) from the requirements and use cases, with a TL-xxx screen inventory, Mermaid navigation map, content and components of each screen, states, and accessibility and responsiveness guidelines. Use when asked for screens, pages, wireframes, site map, navigation flow or design system.
---

# Specify the interface

## Inputs

`docs/02-requisitos.md` (RF, RNF), `docs/03-casos-de-uso.md` (if it exists) and the client's request in `docs/00-briefing.md` (pages, visual references, brand).

## Procedure

1. **Screen inventory** (section 2 table, between the `prumo:figma` markers): one row per screen or page, with ID `TL-001`, `TL-002`... in the first column. In sites, each page and each landing page is a screen; system screens group what the user sees together (list and filters on the same screen). In the "Use cases" column, cite the UCs (or, without use cases, the RFs) the screen serves. Without Figma, use `—` in "Figma page", "Link" and "Image".
   - If the inventory already came from Figma (`prumo figma telas`, with links filled in), keep the rows and complete only the "Use cases" column.
   - If `docs/03-casos-de-uso.md` exists, update the "Screens" row of each use case with the TLs that serve it (or `—`).
2. **Navigation map** (section 3): replace the template example with a `flowchart` with the real screens (`tl1["TL-001 Home"]`), the links between them and, when there are any, the external entry points (ad, WhatsApp link, e-mail).
3. **Detail of each screen** (section 4): one `### Screen TL-00N — Name` subsection per screen (the ID is already defined in the inventory; that is why the title starts with "Screen"). Include goal, blocks in the order they appear, actions and destination, data shown, states (empty, loading, error, success) and the RF/RNF/UC served.
4. **Design system** (section 1): fill in only what the client provided (brand, colors, fonts, references) or what the profile already defines. The rest goes in as a marked proposal ("Proposal: ...") or as a question in section 9 of the briefing. Component library only if it makes sense for the stack.
5. **Guidelines** (section 5): accessibility with a verifiable criterion (WCAG AA contrast, visible focus, `prefers-reduced-motion` when there is animation), responsiveness (priority devices) and who provides texts and images.

## Quality

- The interface serves the requirements; do not create screens or functions the client did not ask for. If an obvious screen is missing (submission confirmation, error page), include it as Could and cite the related RF.
- Every RF the user sees on screen appears in at least one screen.
- Describe content and behavior, not pixels: the visual layout comes from Figma or the designer.

## Output

`{{prumo}} validar` with no errors and a summary: screens created, RFs without a screen and questions about content and visual identity.
