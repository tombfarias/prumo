# {{projeto}} — guia para agentes de IA

> Fonte única de instruções para qualquer agente (Claude Code, Codex, Gemini CLI, Copilot, Cursor...).
> O `CLAUDE.md` importa este arquivo. Para gerar as cópias das outras ferramentas, rode `{{prumo}} agentes exportar`.
> Gerado pelo Prumo em {{data}} (perfil `{{perfil}}`). Pode e deve ser ajustado ao longo do projeto.

## Projeto

| | |
|---|---|
| Cliente | {{cliente}} |
| Perfil | {{perfil_nome}} |
| Stack | {{stack}} |
| Configuração do Prumo | `projeto.prumo.json` |

## Regra de ouro: a especificação vem primeiro

1. Os documentos em `docs/` são a fonte da verdade do que deve ser construído. Leia-os antes de propor ou alterar código.
2. Antes de implementar uma história, percorra a trilha completa: **HU → UC → RF/RNF/RN → telas (TL) → modelo de dados → ADRs**.
3. Se o código precisar divergir da especificação, **pare e aponte a divergência** ao usuário. Não ajuste a especificação em silêncio para caber no código.
4. **Documentos aprovados são somente leitura** (lista em `projeto.prumo.json` → `aprovados`). Pedidos de alteração viram um registro de mudança: `{{prumo}} mudanca "título"`.
5. **Não invente requisitos.** Dúvidas sobre o negócio viram perguntas na seção 9 de `docs/00-briefing.md`.
6. Trechos `[PREENCHER: ...]` são lacunas. Ao preencher um documento, substitua todas ou deixe explícito por que ficaram em aberto.

## Situações adversas (o que fazer sem improvisar)

- **Briefing vago ou contraditório:** não escolha um lado. Registre as duas versões como pergunta (seção 9 do briefing) e siga só com o que não depende dela.
- **Cliente muda o escopo no meio:** nada de código antes do registro `{{prumo}} mudanca "título"` com impacto em prazo e preço.
- **Stack fora do perfil:** registre a escolha num ADR (`{{prumo}} adr "título"`) e escreva as convenções em `docs/07-arquitetura.md` antes de codificar; não aplique convenções de outra stack.
- **Ferramenta ausente** (git, node, php, banco...): não instale nada global nem troque a stack por conta própria; diga ao usuário o que falta e o comando para instalar.
- **Dados reais do cliente** (CPF, cartão, senhas, tokens): nunca em `docs/`, código ou commits. Use dados fictícios; segredos só no `.env`.
- **Hook bloqueou:** leia o motivo e corrija a causa. Não contorne a guarda por outro caminho (shell, outro arquivo).

## Depois de toda mudança significativa

Mudança significativa = 3 ou mais arquivos de código, 80 ou mais linhas, ou qualquer alteração em autenticação/autorização, banco de dados (migrações, models), rotas/API, dependências, infraestrutura (Docker, CI/CD), configuração ou dados sensíveis. Ao concluir uma mudança assim, **antes de encerrar**:

1. **Atualize a documentação afetada** seguindo `.claude/skills/atualizar-documentacao/SKILL.md`.
2. **Procure falhas de segurança** seguindo `.claude/skills/revisar-seguranca/SKILL.md` (inclui `{{prumo}} seguranca`) e registre os achados em `docs/12-seguranca.md`.

No Claude Code um hook exige essas duas etapas automaticamente; nos demais agentes, siga esta regra por conta própria.

## Escrita dos documentos

- **Um fato, um lugar.** Termos do negócio são definidos uma vez no glossário de `docs/02-requisitos.md`; cada ID, no documento dono. Nos demais, cite o ID em vez de repetir o texto.
- **Estrutura antes de prosa:** tabelas e listas; parágrafos de até 3 frases; frases de até 40 palavras.
- **Verificável:** números, nomes e critérios. Termo vago ("rápido", "intuitivo", "moderno") vira métrica ou pergunta P-xx.
- **Sem enchimento:** nada de introduções que repetem o título, "é importante ressaltar", "a fim de" (use "para").
- **Instruções no imperativo**, uma ação por item. Seção que não se aplica: "Não se aplica: motivo", em uma linha.
- `{{prumo}} validar` aponta os excessos como avisos de estilo.

## Economia de tokens (sem perder qualidade)

- **Carregue só a trilha necessária:** `{{prumo}} contexto HU-003` (ou UC-xxx, RF-xxx...) imprime apenas os blocos ligados àquele item. Prefira isso a ler documentos inteiros; para achar algo pontual, use busca por ID (`Grep "UC-004" docs/`).
- **Não releia** o que já está no contexto; leia arquivos grandes por trechos.
- **Edite com precisão:** use edições pontuais em vez de reescrever arquivos inteiros.
- **Delegue explorações longas** (varrer o código, revisar muitos arquivos) a subagentes, que devolvem só a conclusão.
- **Não leia** dependências, builds, lockfiles nem arquivos minificados (`node_modules/`, `dist/`, `*.lock`, `*.min.js`).
- **Respostas finais curtas:** o que mudou, pendências e decisões. Sem repetir o conteúdo dos arquivos.
- Qualidade vem primeiro: se faltar contexto para decidir bem, leia o que for preciso.

## Documentos do projeto

{{lista_documentos}}

## Identificadores e rastreabilidade

| Prefixo | Significado | Definido em |
|---|---|---|
| `RF-001` | Requisito funcional | 02-requisitos.md |
| `RNF-001` | Requisito não funcional | 02-requisitos.md |
| `RN-001` | Regra de negócio | 02-requisitos.md |
| `UC-001` | Caso de uso | 03-casos-de-uso.md |
| `TL-001` | Tela | 05-interface.md |
| `EP-01` / `HU-001` | Épico / história de usuário | 08-backlog.md |
| `CT-001` | Caso de teste | 09-plano-de-testes.md |
| `ADR-001` | Decisão arquitetural | docs/adr/ |
| `CM-001` | Mudança de escopo | docs/mudancas/ |
| `SEG-001` | Achado de segurança | 12-seguranca.md |

- Cada ID é **definido uma única vez**: no título da seção (`### UC-001 — Nome`) ou na primeira coluna de uma tabela.
- Dentro do bloco de um item, cite os IDs que ele atende. É isso que monta a matriz `docs/rastreabilidade.md`.
- No código, cite o ID onde a regra é implementada (`// RN-002`) e nos testes o caso coberto (`// CT-005`).
- Commits no formato Conventional Commits com o ID da história: `feat(HU-003): cadastro de clientes`.

## Comandos do Prumo

| Comando | Para quê |
|---|---|
| `{{prumo}} status` | Resumo dos documentos e pendências |
| `{{prumo}} validar` | Lacunas, Mermaid inválido, IDs indefinidos ou duplicados, documentos aprovados alterados |
| `{{prumo}} rastreabilidade` | Gera `docs/rastreabilidade.md` (não edite à mão) |
| `{{prumo}} orcamento` | Soma as estimativas do backlog e gera `docs/orcamento.md` (não edite à mão) |
| `{{prumo}} diagramas` | Extrai os blocos Mermaid para `docs/diagramas/*.mmd` |
| `{{prumo}} seguranca` | Varredura estática de falhas comuns de segurança no código |
| `{{prumo}} adr "título"` | Cria um registro de decisão arquitetural |
| `{{prumo}} mudanca "título"` | Cria um pedido de mudança de escopo |
{{comandos_figma}}
## Procedimentos (skills)

Os procedimentos detalhados estão em `.claude/skills/<nome>/SKILL.md`, no formato aberto *Agent Skills*. Agentes que não carregam skills automaticamente devem **ler o arquivo correspondente antes de executar a tarefa**.

{{lista_skills}}

## Definição de pronto

- Implementação fiel aos documentos e aos critérios de aceite da história.
- Testes automatizados cobrindo os critérios de aceite; suíte passando.
- Documentação afetada atualizada (skill `atualizar-documentacao`) e revisão de segurança feita (skill `revisar-seguranca`).
- `{{prumo}} validar` sem erros e `{{prumo}} rastreabilidade` regenerada.
- Status da história atualizado em `docs/08-backlog.md`.

## Segurança

- Nunca leia, exiba ou versione `.env`, chaves privadas ou credenciais. Documente as variáveis em `.env.example`.
- Não rode comandos destrutivos (`rm -rf`, `git push --force`, `git reset --hard`, `DROP`, resets de banco) sem pedido explícito do usuário.
- Dados pessoais seguem a seção de privacidade de `docs/06-banco-de-dados.md` (LGPD).

{{convencoes}}
