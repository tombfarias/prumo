---
name: usar-prumo
description: Opera o Prumo, o sistema do usuário para projetos freelance (especificação com IDs rastreáveis, UML em Mermaid, kit de skills/hooks para o Claude Code, Figma, orçamento, segurança). Use quando o usuário pedir para criar ou especificar um projeto de cliente, gerar documentos de especificação, orçar, ou mencionar o Prumo.
---

# Usar o Prumo

O Prumo cria projetos com `docs/` (especificação), `AGENTS.md`/`CLAUDE.md`, skills, subagentes e hooks do Claude Code,
e mantém tudo rastreável por IDs. Repositório: https://github.com/tombfarias/prumo · instalação local típica: `D:\SistemaCodigo`.

## Como chamar

- CLI: `prumo <comando>` (prumo.exe, `prumo.bat` ou `python prumo.py`). Todo comando aceita `--projeto <pasta>` e `--json`.
- PowerShell (módulo `powershell/Prumo.psm1`): `prumo`, `Send-Claude "pedido"`, `Invoke-PrumoTarefa implementar HU-003`,
  `Get-PrumoStatus`, `Start-PrumoGui`.
- Interface: `prumo gui` ou duplo clique em `prumo-app.exe`.

## Fluxo de um projeto freelance

1. `prumo novo <pasta> --perfil <id> --nome "..." --cliente "..." [--figma <url>]`
   Perfis: `api-rest`, `web-fullstack`, `sistema-gestao`, `site-institucional`, `automacao-bot`, `app-mobile`, `minimo`.
2. Registrar o material do cliente em `docs/00-briefing.md` (palavras do cliente, perguntas em aberto).
3. Especificar: no Claude Code, `/especificar-projeto`; ou `prumo claude especificar` (etapas: requisitos, casos-de-uso,
   uml, banco, arquitetura, backlog, testes, proposta, com validação entre elas).
4. Conferir: `prumo status`, `prumo validar`, `prumo rastreabilidade`, `prumo orcamento`.
5. Cliente aprova → `prumo aprovar docs/01-visao.md ...` (agentes ficam proibidos de editar; mudanças via `prumo mudanca "título"`).
6. Implementar: `/implementar-historia HU-001` ou `prumo claude implementar HU-001`; depois `/revisar-conformidade`.
7. Após mudanças significativas, os hooks exigem `atualizar-documentacao` e `revisar-seguranca` (`prumo seguranca`).
8. Gestão: `prumo horas` (tempo registrado pelos hooks), `prumo orcamento`, `docs/10-proposta-comercial.md`, `docs/11-entrega.md`.

## Convenções que você deve respeitar ao escrever documentos

- IDs: RF, RNF, RN (02-requisitos), UC (03), TL (05), EP/HU (08), CT (09), SEG (12), ADR (docs/adr), CM (docs/mudancas).
- Cada ID é definido uma vez: no título (`### UC-001 — Nome`) ou na 1ª coluna de uma tabela. Dentro do bloco, cite os IDs atendidos.
- Lacunas ficam como `[PREENCHER: dica]`; nunca invente requisitos — dúvidas vão para a seção 9 do briefing.
- Diagramas em Mermaid válidos (flowchart, sequenceDiagram, classDiagram, stateDiagram-v2, erDiagram).
- Estimativas no backlog no formato `**Estimativa:** 6h`.
- Economia de tokens: `prumo contexto HU-003` carrega só a trilha de um item.

## Quando você não tem acesso ao computador do usuário

Escreva o conteúdo dos documentos seguindo os modelos e as convenções acima (para ele colar em `docs/`) e diga
quais comandos do Prumo rodar em seguida. Se houver acesso ao computador (shell do dispositivo), rode os comandos
diretamente na pasta do projeto.
