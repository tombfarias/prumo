# Economia de tokens

Todo projeto do Prumo é configurado para gastar o mínimo de tokens sem sacrificar a qualidade. A regra que vem antes de todas: **se faltar contexto para decidir bem, o agente lê o que for preciso**.

## O que já vem configurado

| Medida | Onde | Efeito |
|---|---|---|
| **Contexto compacto por ID** | `prumo contexto HU-003` | Em vez de ler 5 ou 6 documentos inteiros para implementar uma história, o agente recebe só os blocos ligados a ela |
| **Trilha injetada no prompt** | `prumo claude implementar/revisar/documentar` | O Prumo extrai a trilha antes de chamar o Claude; o agente não precisa procurar |
| **Bloqueio de leitura de pastas pesadas** | `.claude/settings.json` → `permissions.deny` | `node_modules`, `dist`, `build`, `.next`, `coverage`, `.venv`, lockfiles, `*.min.js` e `*.map` não são lidos |
| **Resumo de sessão compacto** | hook `contexto_sessao` | Uma linha por categoria, só documentos com lacunas, em vez de despejar o estado inteiro |
| **Saídas de ferramentas truncadas** | hooks de lint e testes | Só as últimas 40 a 60 linhas de erro voltam ao Claude |
| **Regras no AGENTS.md** | seção "Economia de tokens" | Não reler arquivos, ler por trechos, editar pontualmente, delegar varreduras longas a subagentes, respostas finais curtas |
| **Subagentes** | `.claude/agents/` | Revisões e análises longas rodam em contexto separado e devolvem só a conclusão |
| **Uma sessão por etapa** | `prumo claude especificar` | Cada etapa começa limpa e lê do disco o que precisa, sem arrastar o histórico das anteriores |
| **Skills sob demanda** | `.claude/skills/` | O corpo de uma skill só entra no contexto quando ela é usada |
| **Convenções enxutas** | `templates/perfis/convencoes/` | O texto que entra no AGENTS.md (lido em toda sessão) é curto e objetivo |

## Boas práticas para você

- Peça tarefas com alvo claro: "implementar HU-007" gasta muito menos do que "continue o projeto".
- Use `--continuar` só quando a tarefa depende da conversa anterior; senão, uma sessão nova sai mais barata.
- Acompanhe o custo de cada execução em `prumo claude historico` (ou na aba Claude da interface).
- Use `--max-turnos` em tarefas exploratórias para limitar o gasto.
- Se for usar um modelo mais barato em alguma tarefa simples, use `--modelo`; mantenha o modelo principal nas etapas de especificação e implementação, que pedem raciocínio.
