# Guia de escrita

Regras para tudo o que o Prumo gera: modelos de documento, skills, subagentes, AGENTS.md e CLAUDE.md. Os documentos são lidos pelo Claude a cada tarefa e pelo cliente na aprovação; texto curto e exato economiza tokens e evita interpretação.

## Regras

| Regra | Faça | Evite |
|---|---|---|
| Um fato, um lugar | Defina o termo no glossário (`02-requisitos.md`) e o ID no documento dono; cite o ID nos demais | Copiar a descrição de um RF para o caso de uso, a história e o teste |
| Estrutura antes de prosa | Tabela para itens com os mesmos campos; lista para passos | Parágrafos que enumeram itens |
| Tamanho | Parágrafos de até 3 frases (70 palavras); frases de até 40 palavras | Frases com vários "e", ";" e parênteses |
| Verificável | "Responde em até 2 s com 100 usuários" | "Rápido", "intuitivo", "moderno", "robusto" |
| Sem enchimento | Vá direto ao fato | "É importante ressaltar que", "a fim de" (use "para"), "no que diz respeito a" |
| Instrução | Imperativo, uma ação por item: "Rode `prumo validar`." | "Seria interessante que o agente rodasse..." |
| Não se aplica | "Não se aplica: sem login no sistema." em uma linha | Apagar a seção ou deixá-la vazia |

O briefing (`00-briefing.md`) é exceção parcial: registra as palavras do cliente, então termos vagos ficam ali, e a especificação os converte em critério ou pergunta.

## Onde as regras atuam

- **AGENTS.md** de cada projeto: seção "Escrita dos documentos" (versão curta destas regras, lida em toda sessão).
- **Prompt de `prumo claude especificar`**: regra "Concisão" em `REGRAS_ESPECIFICACAO` (`prumo_cli/claude.py`).
- **`prumo validar`**: avisos `estilo:` gerados por `prumo_cli/estilo.py`. São sugestões, nunca erros, nem com `--estrito`. Até 8 por documento.
- **Testes**: todo arquivo `.md` de um projeto recém-criado (de qualquer perfil) passa sem avisos de estilo. Modelo, skill ou convenção nova precisa passar também.

## O que `estilo.py` verifica

| Verificação | Limite |
|---|---|
| Expressões de enchimento | lista `ENCHIMENTO` |
| Termos vagos (fora do briefing) | lista `VAGOS`; termos entre aspas são exemplos e não contam |
| Frase longa | mais de 40 palavras (`MAX_PALAVRAS_FRASE`) |
| Parágrafo longo | mais de 70 palavras de prosa (`MAX_PALAVRAS_PARAGRAFO`) |
| Linha repetida | linha igual de 40+ caracteres e 8+ palavras no mesmo documento (metadados com " · " não contam) |

Comentários HTML, blocos de código, trechos em crase e lacunas `[PREENCHER]` são ignorados.
