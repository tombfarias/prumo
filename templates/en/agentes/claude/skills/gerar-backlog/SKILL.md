---
name: gerar-backlog
description: Breaks the use cases into epics and user stories (08-backlog.md) with Given/When/Then acceptance criteria, hour estimates, priority and delivery milestones; then generates the budget. Use when asked for backlog, stories, estimates, sprint planning or schedule.
---

# Generate the backlog

## Inputs

Use cases, requirements, architecture and, if any, screens (05-interface.md).

## Procedure

1. **Epics** (`EP-01`...): one per functional area or delivery milestone.
2. **Stories** (`### HU-00N — Title`): each story delivers verifiable value and fits in up to 2 days of work (≤ 16h). Split the larger ones.
   - Trace line: `**Epic:** EP-0N · **Use cases:** UC-00N · **Requirements:** RF-00N`.
   - "As a / I want / so that" format.
   - Acceptance criteria in Given/When/Then, covering the main flow and the exceptions of the use case.
   - `**Estimate:** 6h` (format read by `prumo orcamento`), MoSCoW priority and status `to do`.
   - In epic titles or other tables, do not start the line with the already defined ID (use "Epic EP-01 — ..."): each ID is defined once.
3. **Base scope and optional items.** The story priority follows the requirement's: Must and Should form the base scope; **Could items are optional** and `prumo orcamento` sums them separately, outside the total. Won't does not enter the budget. List the optional items in their own section, with the hours of each, for the client to choose.
4. **Technical stories** only those needed to deliver the scope (setup, deploy, data migration when there is one). CI/CD, monitoring, privacy routines and the like in proportion to the size: in small projects, a simple or optional item. They cite the RNFs served.
5. **Estimates:** add test and review time to each story. Record the estimate assumptions when uncertainty is high and flag the riskiest stories. Do not write your own contingency percentage: contingency comes from the configuration and appears in `docs/orcamento.md`.
6. **Milestones** (`M1`, `M2`...): group epics into deliveries the client can validate, with a suggested payment percentage.
7. Run `{{prumo}} orcamento` to generate `docs/orcamento.md` and `{{prumo}} rastreabilidade` to see use cases without a story.

## Output

Summary: number of stories per epic and per priority, hours of the base scope and of the optional items, and stories without an estimate.
