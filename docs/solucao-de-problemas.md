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
| `agentes atualizar` diz que manteve arquivos | Você (ou um clone novo, sem `.prumo/kit.json`) tem versões diferentes das do Prumo | Compare com `.prumo/kit-novo/`, junte o que quiser, ou rode `prumo agentes atualizar --forcar` (guarda cópia em `.prumo/backup/`) |
| "parece conter CPF/chave..." ao editar | Hook impede dados reais e segredos em arquivos | Use dados fictícios; segredos no `.env`. Falso positivo: `hooks.bloquear_dados_sensiveis: false` |
| Lint/testes "não está instalado" | O comando de `comandos` usa uma ferramenta ausente na máquina | Instale a ferramenta ou esvazie o comando em `projeto.prumo.json` |
| Criação do projeto interrompida | Erro ou Ctrl+C no meio de `prumo novo` | A pasta nova é desfeita automaticamente; rode o comando de novo |
| `Figma respondeu 403` | Token inválido ou sem acesso ao arquivo | Gere outro token com leitura de arquivos; confirme que sua conta abre o arquivo |
| Ferramentas do Figma indisponíveis no Claude | Servidor MCP não aprovado/autenticado | No Claude Code: `/mcp` → figma → Authenticate |
| Interface mostra "Sessão expirada" | O servidor local encerrou (janela fechada por mais de um minuto) | Abra de novo com `prumo gui` |
| Interface abre no navegador comum | Edge/Chrome não encontrados | Funciona igual; instale o Edge para ter a janela de aplicativo |
| PowerShell: "a execução de scripts foi desabilitada" | Política de execução | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Acentos estranhos no PowerShell | Codificação do console | Use as funções do módulo (ele configura UTF-8) ou `chcp 65001` |
| `prumo horas` sem dados | Hooks não registraram atividade | Confira `hooks.registrar_horas` e se os hooks rodam (veja acima) |
| Antivírus bloqueia o `prumo.exe` | Falso positivo comum em executáveis do PyInstaller | Gere localmente com `build.ps1` ou use `python prumo.py` |
