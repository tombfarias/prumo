# Guia rápido

Do zero a um projeto especificado. Os exemplos usam PowerShell; no Linux/macOS troque `prumo` por `./prumo` ou `python3 prumo.py`.

## 1. Crie o projeto

```powershell
prumo perfis                                   # veja os perfis disponíveis
prumo novo D:\Projetos\loja-da-ana --perfil web-fullstack --nome "Loja da Ana" --cliente "Ana Doces" `
     --figma "https://www.figma.com/design/XXXX/Loja"
```

Ou pela interface: **Novo projeto**, preencha nome, cliente, pasta e perfil.

O Prumo cria a pasta com `docs/` (todos os documentos do perfil, já com o nome do projeto e lacunas `[PREENCHER]`), `AGENTS.md`, `CLAUDE.md`, `.claude/` (skills, subagentes, hooks), `.mcp.json` (Figma), `.gitignore`, `.env.example`, as pastas de código e um repositório git com o commit inicial.

## 2. Registre o briefing

Cole em `docs/00-briefing.md` tudo o que o cliente disse: e-mails, mensagens, transcrições. Não organize demais. Se preferir, peça ao Claude:

```powershell
cd D:\Projetos\loja-da-ana
Send-Claude (Get-Content .\anotacoes-reuniao.txt -Raw)   # "registre isto no briefing" vai junto no texto
```

## 3. Especifique

Com o Claude Code aberto na pasta, rode `/especificar-projeto`. Ele conduz as etapas e pausa entre elas para você revisar.

Pelo terminal, sem abrir o editor:

```powershell
prumo claude especificar              # pergunta antes de cada etapa
prumo claude especificar --sem-pausa  # vai direto
prumo claude requisitos               # só uma etapa
```

Entre as etapas, o Prumo roda `validar`; se houver erro (ID indefinido, Mermaid inválido), pede a correção ao Claude. Depois do backlog, gera o orçamento.

## 4. Confira

```powershell
prumo status            # documentos, lacunas, IDs
prumo validar           # erros e avisos
prumo rastreabilidade   # docs/rastreabilidade.md
prumo orcamento --valor-hora 120
```

As perguntas que dependem do cliente ficam na seção 9 do briefing. Responda com ele e rode a etapa de novo, ou peça ajustes com `Send-Claude`.

## 5. Aprove com o cliente

Envie visão, requisitos, casos de uso, telas e proposta. Aprovados:

```powershell
prumo aprovar docs/01-visao.md docs/02-requisitos.md docs/03-casos-de-uso.md
```

Os agentes passam a ser proibidos de editá-los. Pedidos novos viram `prumo mudanca "título"`.

## 6. Implemente

```powershell
prumo claude implementar HU-001 --permitir "Bash(npm test:*)"
prumo claude revisar HU-001
```

Ou, no Claude Code: `/implementar-historia HU-001` e `/revisar-conformidade HU-001`. Quando a mudança é significativa, o hook do Prumo só deixa o Claude encerrar depois de atualizar a documentação afetada e revisar a segurança.

Próximo: [fluxo de trabalho freelance completo](fluxo-de-trabalho.md).
