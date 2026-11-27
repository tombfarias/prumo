---
name: levantar-requisitos
description: Turns the briefing and the client's notes into the Vision Document (01-visao.md) and the Requirements Specification (02-requisitos.md), with RF/RNF/RN IDs and open questions. Use when starting the specification, when receiving new information from the client or when asked for requirements.
---

# Gather requirements

## Inputs

- `docs/00-briefing.md` (required) and any material the user pastes into the conversation.
- `especificacao.prumo.json`, if it exists: the form the user filled in on the interface. Use the same IDs for features (RF-xxx) and rules (RN-xxx), the priority, the actor and the RNFs checked; do not renumber them.
- If the user brings new material from the client, **first** record it in the briefing (section 10, meeting of the day), in the client's words.

## Procedure

1. **Vision (`docs/01-visao.md`).** Fill it in from the briefing, without completing it with assumptions. Be specific with what the client said (user profiles, numbers, deadlines). What they did not say becomes a marked assumption ("Assumption: ...") in section 7 or a question. The problem statement uses the client's words; if they did not describe the problem, leave the gap linked to a question. The "Out of scope" section is required: list what the client may assume is included and is not (mobile app, integration X, data migration, training...).
2. **Functional requirements.** One verifiable behavior per row, starting with "The system must...". Number them in sequence (RF-001, RF-002...) with no gaps. Classify with MoSCoW: Must and Should are the base scope; what the client did not ask for and you suggest goes in as Could. In the Source column, use: `Request` (it is in the briefing), `Meeting yyyy-mm-dd`, `Assumption` (to confirm, cite the P-xx question) or `Technical suggestion`.
3. **Non-functional requirements.** Consider security, privacy (LGPD/GDPR), performance, availability, compatibility, accessibility and backup, **in proportion to the project's size**: a basic bot does not need the same set as a SaaS. Each RNF needs a verifiable metric or criterion.
4. **Business rules.** Separate rules (calculations, limits, deadlines, permissions) from requirements. Give a concrete example for each RN. A rule that depends on the client's answer stays as an assumption, citing the question.
5. **Glossary.** Every business term that appears more than once.
6. **Questions.** Every gap that depends on the client becomes a row in the section 9 table of the briefing: ID `P-01`, objective question (preferably with options), whether it blocks the proposal and what it impacts (RF, RN, estimate). Mark as blocking only those that change scope or price. Do not fill gaps with silent assumptions: either an explicit assumption, or `[FILL: ...]` with the matching question.

## Quality

- Ambiguous requirement ("fast", "easy", "modern") → rewrite it with a measurable criterion or turn it into a question.
- Requirements that are technical solutions ("use React") → are not RFs. If the client imposed the technology, it goes to the vision's constraints; if it is your or the profile's suggestion, it goes to the assumptions.
- Check that each vision capability (section 5.1) has at least one RF and that each explicit item of the client's request appears in some RF, RNF or constraint.
- Proportional to the request: a two-sentence request produces a short specification and many questions, not dozens of invented requirements.

## Output

Run `{{prumo}} validar` and present: number of RF/RNF/RN per priority, the list of questions for the client and the risks identified.
