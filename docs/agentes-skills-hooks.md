# Agentes, skills e hooks

Cada projeto criado recebe um kit para agentes de IA. O `AGENTS.md` é a fonte única de instruções; o `CLAUDE.md` importa esse arquivo (`@AGENTS.md`) e acrescenta o que é específico do Claude Code.

## Estrutura instalada

```text
AGENTS.md                 regras do projeto (especificação primeiro, IDs, tokens, segurança, convenções da stack)
CLAUDE.md                 @AGENTS.md + específicos do Claude Code
.mcp.json                 servidor MCP do Figma (perfis com interface)
.claude/settings.json     hooks e bloqueios de leitura de pastas pesadas
.claude/skills/*/SKILL.md procedimentos (formato aberto Agent Skills)
.claude/agents/*.md       subagentes
.claude/hooks/*.py        hooks (Python, só biblioteca padrão)
```

## Skills

| Skill | Quando |
|---|---|
| `mapear-projeto-existente` | Engenharia reversa: descreve em `docs/` o sistema que já existe, citando o arquivo de origem (depois de `prumo mapear`) |
| `especificar-projeto` | Conduz a especificação completa, etapa por etapa, com pausa para revisão |
| `levantar-requisitos` | Briefing → visão e requisitos (RF, RNF, RN), perguntas ao cliente |
| `especificar-casos-de-uso` | Atores, diagrama e especificação dos casos de uso |
| `modelar-uml` | Classes, sequência, estados, atividades, componentes, implantação (Mermaid) |
| `modelar-banco` | ER, dicionário de dados, índices, DDL, LGPD, migrações |
| `planejar-arquitetura` | Stack, estrutura, módulos, integrações, segurança, operação, ADRs |
| `gerar-backlog` | Épicos, histórias com critérios Dado/Quando/Então, estimativas, marcos |
| `planejar-testes` | Estratégia, casos de teste, homologação |
| `proposta-comercial` | Proposta para o cliente a partir do escopo, backlog e orçamento |
| `implementar-historia` | Implementa uma HU seguindo a trilha, testes primeiro |
| `revisar-conformidade` | Código × especificação, item por item (não altera nada) |
| `atualizar-documentacao` | Atualiza os documentos afetados por uma mudança significativa |
| `revisar-seguranca` | OWASP Top 10, `prumo seguranca`, auditoria de dependências, achados SEG |
| `controle-de-mudancas` | Pedido de mudança com análise de impacto |
| `implementar-tela-figma` | Tela a partir do Figma via MCP; inventário TL (perfis com interface) |
| `diagramas-figjam` | Publica diagramas Mermaid no FigJam (perfis com interface) |

No Claude Code, cada skill vira um comando (`/implementar-historia HU-003`) e também é carregada automaticamente quando o pedido combina com a descrição. Outros agentes leem o `SKILL.md` indicado na tabela do `AGENTS.md`.

## Subagentes

| Subagente | Ferramentas | Papel |
|---|---|---|
| `analista-requisitos` | leitura, escrita, Bash | Documentos de negócio; só escreve em `docs/` |
| `arquiteto` | leitura, escrita, Bash, web | UML, banco, arquitetura, ADRs |
| `revisor-conformidade` | leitura, Bash | Revisão sem editar arquivos |
| `testador` | leitura, escrita, Bash | Testes a partir dos CTs e critérios de aceite |

Todos usam `model: inherit` (o mesmo modelo da sessão), para não perder qualidade. Ajuste o campo `model` se quiser um modelo mais barato em alguma função.

## Hooks

| Evento | Hook | O que faz |
|---|---|---|
| SessionStart | `contexto_sessao.py` | Injeta um resumo compacto: documentos com lacunas, aprovados, lembrete das regras |
| UserPromptSubmit | `registrar_atividade.py prompt` | Registra o horário em `.prumo/atividade.log` (para `prumo horas`) |
| PreToolUse (Bash/PowerShell) | `guarda_comandos.py` | Bloqueia `rm -rf` amplo, `git push --force`, `git reset --hard`, `DROP`/`TRUNCATE`, resets de banco, `curl \| sh`, leitura de `.env`, publicação de pacotes |
| PreToolUse (Read/Edit/Write) | `guarda_arquivos.py` | Bloqueia leitura/edição de segredos, edição de documentos aprovados e de arquivos gerados, e mudanças na lista de aprovados |
| PostToolUse (Edit/Write) | `pos_edicao.py` | Registra a alteração, formata o arquivo e roda o lint (erros voltam ao Claude) |
| Stop | `registrar_atividade.py stop` | Registra o fim da resposta |
| Stop | `revisao_pos_mudanca.py` | Em mudança significativa, exige atualizar a documentação e revisar a segurança |
| Stop | `ao_parar.py` | Se ligado, roda os testes e devolve as falhas ao Claude |

Os hooks retornam código 2 para bloquear (a mensagem em stderr vai para o Claude) e não entram em loop: os de parada respeitam `stop_hook_active`.

### Personalizar

Em `projeto.prumo.json` → `hooks`:

```json
"hooks": {
  "registrar_horas": true,
  "testes_ao_parar": false,
  "comandos_permitidos": ["git reset --hard origin/main"],
  "revisao_pos_mudanca": true,
  "limite_arquivos": 3,
  "limite_linhas": 80,
  "caminhos_sensiveis": ["(^|/)billing/"]
}
```

`comandos_permitidos` aceita expressões regulares de comandos que o `guarda_comandos` deve liberar.

## Outros agentes

`prumo agentes exportar` gera, a partir do `AGENTS.md`: `GEMINI.md` (Gemini CLI), `.github/copilot-instructions.md` (GitHub Copilot) e `.cursor/rules/prumo.mdc` (Cursor). O Codex e várias outras ferramentas leem o `AGENTS.md` diretamente. Hooks são exclusivos do Claude Code; por isso o `AGENTS.md` repete, como regra, a obrigação de atualizar a documentação e revisar a segurança após mudanças significativas.

## Atualizar o kit de um projeto existente

Depois de atualizar o Prumo: `prumo agentes atualizar` recopia skills, subagentes e hooks. O `settings.json` só é sobrescrito com `--incluir-settings` (para não perder ajustes seus).
