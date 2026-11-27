# Referência de comandos

Forma geral: `prumo [--projeto PASTA] [--json] <comando> [opções]`.

- `--projeto PASTA`: pasta do projeto. Sem ela, o Prumo procura `projeto.prumo.json` na pasta atual e nas de cima.
- `--json`: saída em JSON (para scripts, PowerShell e a interface). Pode vir antes ou depois do comando.
- Código de saída: `0` ok, `1` problemas encontrados (validação/segurança/tarefa com erro), `2` erro de uso.
- `prumo <comando> -h` mostra a ajuda de cada comando.

## Projetos

### `prumo perfis`
Lista os perfis (templates de projeto) com descrição e stack sugerida.

### `prumo projetos [--remover PASTA]`
Projetos abertos recentemente (alimenta a barra lateral da interface). `--remover` tira um projeto da lista sem apagar nada.

### `prumo config [--definir CHAVE=VALOR ...]`
Mostra ou altera seus dados (`freelancer.*`, gravados em `config/freelancer.json`) e as configurações do projeto
(`projeto.*`, gravadas em `projeto.prumo.json`). É o que a tela **Configurações** e o botão **Meus dados** da interface usam.

```powershell
prumo config --definir freelancer.valor_hora=150 --definir freelancer.nome="Seu Nome"
prumo config --projeto D:\Projetos\loja --definir projeto.comandos.testar="npm test" --definir projeto.hooks.testes_ao_parar=sim
```

Chaves aceitas: `freelancer.nome`, `email`, `valor_hora`, `moeda`, `contingencia_percentual`; `projeto.projeto`, `cliente`, `stack`,
`comandos.formatar|lint|testar`, `hooks.registrar_horas|testes_ao_parar|revisao_pos_mudanca|limite_arquivos|limite_linhas|comandos_permitidos`,
`orcamento.valor_hora|contingencia_percentual`, `claude.modelo|max_turnos` e `pastas_codigo`. Listas aceitam JSON (`["src","lib"]`)
e valor vazio volta ao padrão.

### `prumo novo PASTA`
Cria um projeto completo.

| Opção | Descrição |
|---|---|
| `--perfil, -p` | `api-rest`, `web-fullstack` (padrão), `sistema-gestao`, `site-institucional`, `wordpress`, `automacao-bot`, `app-mobile`, `minimo` |
| `--nome`, `--cliente`, `--autor` | Metadados usados nos documentos (autor padrão: `config/freelancer.json` ou `git config user.name`) |
| `--stack` | Substitui a stack sugerida do perfil |
| `--figma URL` | Ativa a integração com o Figma e registra o arquivo |
| `--com-figma` / `--sem-figma` | Força ligar/desligar o Figma independentemente do perfil |
| `--sem-git` | Não cria o repositório git |
| `--python CMD` | Comando do Python nos hooks (padrão: detectado: `python`, `python3` ou `py`) |
| `--hooks-absolutos` | Caminho absoluto nos hooks em vez de `$CLAUDE_PROJECT_DIR` |
| `--hooks-via python\|prumo` | Rodar hooks pelo Python ou pelo `prumo.exe` |
| `--forcar` | Usa uma pasta que já tem arquivos |

### `prumo status`
Documentos com lacunas e estado (em andamento, completo, aprovado, aprovado ALTERADO), contagem de IDs e o próximo documento a completar.

### `prumo doc [ID] [--listar]`
Sem ID ou com `--listar`: catálogo de documentos e quais o projeto tem. Com ID (ex.: `03-casos-de-uso`, `04-uml/estados`): adiciona o documento ao projeto.

### `prumo formulario [salvar ARQUIVO | validar]`
Formulário de especificação em `especificacao.prumo.json` (veja [Formulário de especificação](formulario-de-especificacao.md)).
Sem ação: preenchimento por passo e quantidade de itens; com `--json`, também o formulário, os catálogos de
`templates/catalogos/` e as opções fixas (é o que a interface usa). `salvar ARQUIVO`: normaliza, atribui os IDs que
faltam (RF, RN, UC, TL, marcos) sem colidir com os documentos e grava; só erro de estrutura impede a gravação.
`validar`: referências soltas, IDs repetidos, campos obrigatórios e valores fora dos catálogos (sai com código 1 se houver erro).

## Qualidade da especificação

### `prumo validar [--estrito] [--mmdc]`
Erros: documento aprovado alterado ou ausente, Mermaid inválido, ID citado e não definido, ID definido duas vezes. Avisos: lacunas `[PREENCHER]`, marcadores `{{...}}` não substituídos, cobertura incompleta (requisito sem caso de uso ou história, caso de uso sem história, história sem teste, tela sem caso de uso) e avisos `estilo:` (enchimento, termos vagos, frases ou parágrafos longos, linhas repetidas; veja o [guia de escrita](guia-de-escrita.md)).
`--estrito` transforma avisos em erros (exceto os de estilo) (útil antes de enviar ao cliente). `--mmdc` valida cada diagrama com o mermaid-cli.

### `prumo rastreabilidade`
Gera `docs/rastreabilidade.md`: requisitos → casos de uso → histórias → testes → código, regras de negócio, casos de uso com telas e histórias, e a lista de problemas. Veja [Rastreabilidade](rastreabilidade.md).

### `prumo contexto ID [ID...] [--profundidade N]`
Imprime só os blocos ligados aos IDs (por exemplo, a história, seus casos de uso, requisitos, regras, telas e testes) e os arquivos de código que os citam. Feito para alimentar agentes gastando poucos tokens.

### `prumo diagramas`
Extrai todos os blocos Mermaid para `docs/diagramas/<documento>-<n>.mmd` (para o mermaid-cli, o FigJam ou outras ferramentas).

### `prumo seguranca [ARQUIVOS...] [--falhar-em GRAVIDADE]`
Varredura estática: chaves privadas, tokens conhecidos, segredos literais, SQL concatenado, `eval`/`exec`, shell com entrada externa, TLS desligado, CORS aberto, debug ligado, HTML sem escape, hash fraco, aleatório inseguro, `http://` externo, JWT sem verificação. Os segredos aparecem mascarados. Silencie uma linha revisada com o comentário `prumo:ignorar`. `--falhar-em Alta` sai com código 1 se houver achado Alta ou Crítica (bom para CI).

## Aprovação e registros

| Comando | Descrição |
|---|---|
| `prumo aprovar ARQ... [--forcar]` | Marca como aprovado pelo cliente (data + hash). Recusa documentos com lacunas, salvo `--forcar` |
| `prumo desaprovar ARQ...` | Libera para edição (depois de uma mudança aprovada) |
| `prumo adr "título"` | Cria `docs/adr/ADR-00N-titulo.md` |
| `prumo mudanca "título"` | Cria `docs/mudancas/CM-00N-titulo.md` |

## Gestão

### `prumo orcamento [--valor-hora N] [--contingencia P]`
Soma as estimativas das histórias (`**Estimativa:** 6h` ou `1,5d`, 1 dia = 8h), agrupa por épico, aplica a contingência e o valor da hora (opção → `projeto.prumo.json` → `config/freelancer.json`) e gera `docs/orcamento.md`.

### `prumo horas [--de AAAA-MM-DD] [--ate AAAA-MM-DD] [--pausa MIN]`
Horas por dia a partir de `.prumo/atividade.log`, que os hooks gravam a cada pedido e a cada fim de resposta do Claude Code. Um novo pedido depois de mais de `--pausa` minutos (padrão 30) abre outra sessão.

## Agentes

| Comando | Descrição |
|---|---|
| `prumo agentes listar` | Lista skills, subagentes, hooks, `CLAUDE.md`, `AGENTS.md` e `settings.json` do projeto, com descrição, eventos de cada hook e estado: igual ao kit, personalizado, próprio do projeto ou ausente |
| `prumo agentes exportar [--alvos gemini,copilot,cursor]` | Gera `GEMINI.md`, `.github/copilot-instructions.md` e `.cursor/rules/prumo.mdc` a partir do `AGENTS.md` |
| `prumo agentes atualizar [--incluir-settings]` | Recopia skills, subagentes e hooks da versão atual do Prumo para o projeto (o `settings.json` só com a opção) |

## Claude Code

### `prumo claude TAREFA [ALVO] [opções]`

| Tarefa | O que faz | Alvo |
|---|---|---|
| `especificar` | Todas as etapas de especificação do perfil, com validação entre elas | — |
| `requisitos`, `casos-de-uso`, `uml`, `banco`, `arquitetura`, `backlog`, `testes`, `proposta` | Uma etapa | — |
| `implementar` | Implementa uma história (trilha injetada no prompt) | `HU-003` |
| `revisar` | Revisão de conformidade (só leitura) | `HU-003` ou nada |
| `documentar` | Atualiza a documentação após mudanças | opcional |
| `seguranca` | Revisão de segurança | opcional |
| `mudanca` | Pedido de mudança com análise de impacto | use `--texto` |
| `tela` | Implementa uma tela a partir do Figma | `TL-002` ou URL |
| `figjam` | Publica diagramas no FigJam | — |
| `livre` | Pedido livre | o próprio texto ou `--texto` |
| `historico` | Lista execuções anteriores | — |

| Opção | Descrição |
|---|---|
| `--texto, -t` / `--texto-arquivo` | Pedido ou instruções extras (o arquivo é lido em UTF-8) |
| `--continuar, -c` / `--sessao ID` | Continua a última sessão / uma sessão específica |
| `--modelo`, `--max-turnos` | Repassados ao Claude Code |
| `--permitir FERRAMENTA` | Libera uma ferramenta extra, ex.: `"Bash(npm test:*)"` (repetível) |
| `--modo` | Modo de permissão (`acceptEdits` padrão; `default` na revisão) |
| `--simular` | Mostra o comando e o prompt sem executar |
| `--de`, `--ate`, `--sem-pausa` | Na especificação: intervalo de etapas e sem perguntas entre elas |
| `--sessoes grupos\|unica\|etapa` | Na especificação: 3 sessões (análise, solução, planejamento; padrão), uma sessão só ou uma por etapa. Também em `projeto.prumo.json` → `claude.sessoes_especificacao` |

Detalhes em [PowerShell e Claude](powershell-e-claude.md).

## Figma

| Comando | Descrição |
|---|---|
| `prumo figma telas [URL] [--token T] [--imagens] [--escala N]` | Sincroniza o inventário de telas (TL) em `docs/05-interface.md` |
| `prumo figma ativar [URL]` | Liga a integração num projeto criado sem Figma (`.mcp.json`, skills, documento 05) |

## Interface e utilitários

| Comando | Descrição |
|---|---|
| `prumo gui [--porta N] [--sem-janela]` | Abre a interface; `--sem-janela` só inicia o servidor e mostra o endereço |
| `prumo hook NOME [ARGS]` | Executa um hook do projeto com o Python embutido (uso interno do `prumo.exe`) |
| `prumo versao` / `prumo --versao` | Versão e pasta do Prumo |
