# Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| `Nenhum projeto do Prumo encontrado aqui` | Você não está dentro da pasta do projeto | `cd` para a pasta ou use `--projeto <pasta>` |
| `Claude Code não encontrado no PATH` | Claude Code não instalado ou fora do PATH | Instale, rode `claude` uma vez, ou defina `PRUMO_CLAUDE` |
| Tarefa do Claude termina sem fazer nada | Ferramenta necessária não liberada no modo não interativo | Veja o log em `.prumo/claude/`; libere com `--permitir` ou `claude.ferramentas_extras` |
| Hooks não rodam / "file not found" no Claude Code | Python não está no PATH do shell que o Claude Code usa, ou `$CLAUDE_PROJECT_DIR` não expandiu | Confira `python --version` no terminal; recrie o settings com `--hooks-absolutos` (`prumo agentes atualizar --incluir-settings` após ajustar `hooks_absolutos: true`) ou use `hooks_via: "prumo"` |
| O Claude não consegue encerrar e pede documentação/segurança | Mudança significativa detectada (é o comportamento esperado) | Deixe o Claude concluir as skills; ajuste `limite_arquivos`/`limite_linhas` se estiver sensível demais |
| "Acesso bloqueado a '.env'" | Hook protegendo segredos | Documente as variáveis em `.env.example` e preencha o `.env` você mesmo |
| "foi aprovado pelo cliente... somente leitura" | Documento aprovado | Siga o controle de mudanças; `prumo desaprovar` só após o aceite do cliente |
| `prumo validar` acusa "alterado depois de aprovado" | O arquivo mudou após `prumo aprovar` | Se a mudança é legítima e aceita: `prumo aprovar <arquivo>` de novo; senão, reverta pelo git |
| "Mermaid: tipo de diagrama desconhecido" | Primeira linha do bloco errada | Comece com `flowchart LR`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2` ou `erDiagram`; valide com `--mmdc` |
| `Figma respondeu 403` | Token inválido ou sem acesso ao arquivo | Gere outro token com leitura de arquivos; confirme que sua conta abre o arquivo |
| Ferramentas do Figma indisponíveis no Claude | Servidor MCP não aprovado/autenticado | No Claude Code: `/mcp` → figma → Authenticate |
| Interface mostra "Sessão expirada" | O servidor local encerrou (janela fechada por mais de um minuto) | Abra de novo com `prumo gui` |
| Interface abre no navegador comum | Edge/Chrome não encontrados | Funciona igual; instale o Edge para ter a janela de aplicativo |
| PowerShell: "a execução de scripts foi desabilitada" | Política de execução | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Acentos estranhos no PowerShell | Codificação do console | Use as funções do módulo (ele configura UTF-8) ou `chcp 65001` |
| `prumo horas` sem dados | Hooks não registraram atividade | Confira `hooks.registrar_horas` e se os hooks rodam (veja acima) |
| Antivírus bloqueia o `prumo.exe` | Falso positivo comum em executáveis do PyInstaller | Gere localmente com `build.ps1` ou use `python prumo.py` |
