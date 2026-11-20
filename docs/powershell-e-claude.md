# PowerShell e Claude

O Prumo envia tarefas ao Claude Code em modo não interativo (`claude -p`), pelo terminal, pelo PowerShell ou pela interface.

## Como funciona

1. O Prumo monta o prompt da tarefa: qual skill seguir (`.claude/skills/<skill>/SKILL.md`), o alvo, suas instruções e, para histórias, a trilha da especificação já extraída (`prumo contexto`).
2. Chama `claude -p --output-format stream-json --verbose --permission-mode <modo> --allowedTools <lista>` na pasta do projeto, enviando o prompt pela **entrada padrão** (sem problemas de aspas ou acentos).
3. Mostra o progresso ao vivo: mensagens do Claude e cada ferramenta usada (`→ Edit docs/02-requisitos.md`).
4. Grava `.prumo/claude/<data>_<tarefa>.md` (comando, prompt, resumo), `historico.jsonl` e `ultima_sessao.txt`.

Os hooks do projeto continuam valendo nesse modo: bloqueios, formatação, lint e a revisão obrigatória após mudanças significativas.

## Ferramentas liberadas por tarefa

| Tarefa | Ferramentas | Modo |
|---|---|---|
| Etapas de especificação | Read, Glob, Grep, Write, Edit (+ WebSearch/WebFetch na arquitetura) | acceptEdits |
| `implementar`, `documentar`, `seguranca` | Leitura e escrita + `git status/diff/log/show` + o comando `testar` do projeto | acceptEdits |
| `revisar` | Só leitura + git + `testar` | default |
| `tela`, `figjam` | Leitura e escrita + ferramentas do servidor MCP `figma` | acceptEdits |
| `livre` | Leitura e escrita | acceptEdits |

Ferramentas não liberadas são negadas automaticamente (não há ninguém para aprovar). Libere mais com `--permitir "Bash(npm run build:*)"` ou, de forma permanente, em `projeto.prumo.json` → `claude.ferramentas_extras`.

## Pela linha de comando

```powershell
prumo claude especificar --sem-pausa
prumo claude implementar HU-004 --permitir "Bash(npm test:*)"
prumo claude revisar HU-004
prumo claude mudanca --texto "O cliente quer pagamento por boleto"
prumo claude livre "Explique como o módulo de pedidos calcula o frete"
prumo claude livre --continuar "Agora gere testes para esse cálculo"
prumo claude historico
prumo claude implementar HU-004 --simular       # mostra o comando e o prompt
```

## Pelo módulo do PowerShell

Instalação em [Instalação](instalacao.md#powershell). Funções:

| Função | Uso |
|---|---|
| `prumo ...` | Qualquer comando do Prumo |
| `Send-Claude "pedido"` | Pedido livre. Aceita pipeline: `Get-Content pedido.txt -Raw \| Send-Claude` |
| `Invoke-PrumoTarefa <tarefa> [alvo]` | Qualquer tarefa, com autocompletar (`-Texto`, `-Continuar`, `-Permitir`, `-Modelo`, `-MaxTurnos`, `-Modo`, `-SemPausa`, `-Simular`, `-Json`) |
| `Get-PrumoStatus` | Status como objeto |
| `Get-PrumoHistorico` | Execuções do Claude como objetos |
| `Start-PrumoGui` | Abre a interface |

Exemplos:

```powershell
# Pedido livre no projeto atual
Send-Claude "Crie o componente de listagem de pedidos seguindo a TL-004"

# Resultado como objeto
$r = Invoke-PrumoTarefa revisar HU-004 -Json
$r.resumo
"{0:N4} US$ em {1}s" -f $r.custo_usd, $r.duracao_s

# Rodar a especificação de vários projetos em sequência
Get-ChildItem D:\Projetos -Directory | Where-Object { Test-Path "$($_.FullName)\projeto.prumo.json" } |
  ForEach-Object { Invoke-PrumoTarefa especificar -Projeto $_.FullName -SemPausa }

# Lacunas por documento
(Get-PrumoStatus).documentos | Where-Object lacunas -gt 0 | Sort-Object lacunas -Descending
```

O módulo grava o pedido num arquivo temporário UTF-8 e repassa com `--texto-arquivo`; assim aspas, quebras de linha e acentos chegam intactos no Windows PowerShell 5.1 e no PowerShell 7.

## Primeira vez com o Figma no modo não interativo

O servidor MCP do Figma (`.mcp.json`) precisa ser aprovado e autenticado uma vez de forma interativa: abra `claude` na pasta, rode `/mcp`, escolha **figma** e autentique. Depois, as tarefas `tela` e `figjam` funcionam pelo Prumo.
