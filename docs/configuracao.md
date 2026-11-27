# Configuração

## `config/freelancer.json` (seus dados)

Fica na pasta do Prumo, fora do git. Copie de `config/freelancer.exemplo.json`.

```json
{
  "nome": "Seu Nome",
  "email": "voce@exemplo.com",
  "valor_hora": 120,
  "moeda": "BRL",
  "contingencia_percentual": 20,
  "idioma_interface": "auto",
  "idioma_projetos": "pt-BR"
}
```

`nome` vira o autor dos documentos; `valor_hora`, `moeda` e `contingencia_percentual` são o padrão do `prumo orcamento`.
`idioma_interface` e `idioma_projetos`: veja [Idioma](#idioma).

Na mesma pasta, o Prumo mantém `projetos.json` (projetos recentes) e `.janela/` (perfil da janela da interface).

## `projeto.prumo.json` (cada projeto)

| Campo | Descrição |
|---|---|
| `projeto`, `slug`, `cliente`, `autor`, `perfil`, `stack`, `criado_em` | Metadados |
| `idioma` | Idioma dos documentos e do kit do Claude: `pt-BR` (padrão) ou `en` (veja [Idioma](#idioma)) |
| `documentos` | Documentos do projeto (atualizado por `prumo doc`) |
| `aprovados` | Documentos aprovados: `{"docs/01-visao.md": {"data": "...", "sha256": "..."}}`. Altere só com `prumo aprovar`/`desaprovar` |
| `comandos.formatar` / `comandos.lint` | Rodados pelo hook após cada edição; `{arquivo}` é substituído pelo arquivo editado |
| `comandos.testar` | Usado por `ao_parar` (se ligado) e liberado nas tarefas `implementar`, `revisar` e `seguranca` |
| `comandos_sugeridos` | Sugestão do perfil; copie para `comandos` quando a stack estiver instalada |
| `hooks.registrar_horas` | Grava a atividade para `prumo horas` (padrão `true`) |
| `hooks.testes_ao_parar` | Roda `comandos.testar` antes de o Claude encerrar (padrão `false`) |
| `hooks.comandos_permitidos` | Expressões regulares de comandos que o `guarda_comandos` deve liberar |
| `hooks.revisao_pos_mudanca` | Exige documentação e segurança após mudança significativa (padrão `true`) |
| `hooks.limite_arquivos` / `hooks.limite_linhas` | Limites da mudança significativa (padrão 3 e 80) |
| `hooks.extensoes_lint` | Extensões extras em que o lint roda, além das de código (ex.: `[".sql"]` no perfil `banco-de-dados`) |
| `hooks.caminhos_sensiveis` | Padrões extras (regex) que tornam qualquer mudança significativa |
| `hooks.bloquear_dados_sensiveis` | `false` desliga o bloqueio de segredos (chaves, tokens) em qualquer arquivo e de CPF/cartão válidos em `docs/` (padrão: ligado; valores de teste conhecidos passam) |
| `pastas_codigo` | Pastas varridas pela rastreabilidade e pela segurança |
| `figma.ativo`, `figma.arquivo`, `figma.telas` | Integração com o Figma; `telas` mapeia nó do Figma → `TL-xxx` |
| `orcamento.valor_hora`, `orcamento.contingencia_percentual` | Sobrescrevem o `freelancer.json` neste projeto |
| `claude.modelo`, `claude.max_turnos` | Padrões para `prumo claude` |
| `claude.ferramentas_extras` | Ferramentas sempre liberadas no modo não interativo (ex.: `"Bash(npm run build:*)"`) |
| `python`, `hooks_via`, `hooks_absolutos` | Como os hooks são chamados (veja abaixo) |

Exemplo de `comandos` para Node.js:

```json
"comandos": {
  "formatar": "npx prettier --write {arquivo}",
  "lint": "npx eslint {arquivo}",
  "testar": "npm test"
}
```

## Como os hooks são chamados

| Situação | Comando gerado em `.claude/settings.json` |
|---|---|
| Padrão | `python "$CLAUDE_PROJECT_DIR/.claude/hooks/<hook>.py"` (portátil: funciona em qualquer máquina com Python) |
| `--hooks-absolutos` | `python "D:/Projetos/x/.claude/hooks/<hook>.py"` |
| `hooks_via: "prumo"` (padrão do `.exe` em máquinas sem Python) | `"C:/Prumo/prumo.exe" hook <hook>` |

Para mudar depois: ajuste os campos em `projeto.prumo.json` e rode `prumo agentes atualizar --incluir-settings`.

## Idioma

São dois idiomas independentes:

| | Onde se define | Valores |
|---|---|---|
| **Interface e CLI** (telas, mensagens, `--help`) | `PRUMO_IDIOMA`, senão `idioma_interface` em `freelancer.json` (Meus dados), senão o idioma do sistema | `auto` (sistema: português → `pt-BR`, outro → `en`), `pt-BR`, `en` |
| **Projeto** (documentos, `AGENTS.md`, `CLAUDE.md`, skills, subagentes, convenções e mensagens dos hooks) | `--idioma` em `prumo novo`/`prumo mapear`, senão `idioma_projetos`; fica gravado em `projeto.prumo.json` → `idioma` | `pt-BR`, `en` |

Num projeto em inglês:

- os modelos vêm de `templates/en/` (mesmos caminhos de `templates/`); quem não tem versão em inglês usa a portuguesa;
- as lacunas são `[FILL: dica]` (o Prumo conta `[PREENCHER]` e `[FILL]`);
- IDs, comandos (`prumo validar`), nomes de arquivos (`docs/02-requisitos.md`) e chaves de configuração continuam iguais;
- `prumo validar` usa as regras de estilo em inglês ([guia de escrita](guia-de-escrita.md));
- `prumo gerar` traduz os rótulos do que escreve; textos do formulário e dos catálogos (RNFs, ameaças, perguntas da entrevista) entram como estão, em português até os catálogos ganharem versão em inglês.

Trocar o idioma de um projeto já criado: mude `idioma` em `projeto.prumo.json` e rode `prumo agentes atualizar`. Isso troca skills e subagentes; `AGENTS.md`, `CLAUDE.md` e os documentos já escritos ficam como estão. Novos documentos (`prumo doc`, `adr`, `mudanca`) já saem no idioma novo.

## Variáveis de ambiente

| Variável | Uso |
|---|---|
| `PRUMO_IDIOMA` | Idioma da interface e da CLI (`pt-BR` ou `en`); vale mais que `idioma_interface` |
| `FIGMA_TOKEN` | Token pessoal do Figma para `prumo figma telas` |
| `PRUMO_CLAUDE` | Caminho do executável do Claude Code, se não estiver no PATH |
| `CLAUDE_PROJECT_DIR` | Definida pelo Claude Code ao rodar os hooks |
