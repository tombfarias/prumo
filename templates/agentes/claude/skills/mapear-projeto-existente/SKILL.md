---
name: mapear-projeto-existente
description: Faz a engenharia reversa de um projeto que já tem código e descreve em docs/ o sistema como ele é hoje (requisitos, casos de uso, UML, banco, arquitetura, telas), citando o arquivo de origem de cada item, sem alterar o código. Use quando o Prumo foi instalado num projeto existente, quando pedirem para mapear, documentar ou entender um sistema que já existe, ou ao assumir o projeto de outra pessoa.
---

# Mapear um projeto existente

`{{projeto}}` já tinha código quando o Prumo foi instalado. Seu trabalho é **descrever o que existe**, não o que deveria existir. O código é a fonte dos fatos; o cliente é a fonte das intenções.

## Antes de começar

1. Leia `docs/00-mapa-do-codigo.md` (stack, comandos, estrutura e arquivos-chave detectados). Não refaça essa varredura.
2. Confira `projeto.prumo.json` → `comandos`. Se algum estiver errado para esta máquina, corrija lá e diga ao usuário.
3. Leia o README e a documentação que o projeto já tinha. **Não apague nem reescreva** arquivos do cliente: o Prumo só acrescentou blocos entre `<!-- prumo:inicio -->` e `<!-- prumo:fim -->`.
4. **Não altere código** nesta tarefa. Para varrer muitos arquivos, delegue a subagentes (`analista-requisitos`, `arquiteto`) que devolvem só a conclusão.

## Procedimento (pule o que o perfil não tem)

| # | O que ler no código | Onde escrever |
|---|---|---|
| 1 | README, issues/anotações do cliente, o que o usuário contar | `docs/00-briefing.md` (contexto, integrações existentes; o que não se sabe vira pergunta P-xx) |
| 2 | Rotas, controllers, handlers, telas, comandos, jobs | `docs/02-requisitos.md`: um RF por comportamento observável |
| 3 | Validações, cálculos, permissões, limites no código | `docs/02-requisitos.md`: RN, com o exemplo tirado do código |
| 4 | Config de segurança, cache, logs, timeouts, CI | RNF com o valor atual (ex.: "sessão expira em 30 min") |
| 5 | Papéis de usuário, fluxos ponta a ponta | `docs/03-casos-de-uso.md` |
| 6 | Telas, páginas e componentes | `docs/05-interface.md` (inventário TL) |
| 7 | Models, entidades, migrações, schema | `docs/06-banco-de-dados.md` e `docs/04-uml/classes.md` |
| 8 | Fluxos com várias camadas, estados de entidades | `docs/04-uml/sequencia.md`, `estados.md`, `atividades.md` |
| 9 | Pastas, módulos, integrações externas, Docker/CI, hospedagem | `docs/07-arquitetura.md`, `04-uml/componentes.md`, `04-uml/implantacao.md`; decisões já tomadas viram ADRs com status "Aceita" |
| 10 | Testes existentes | `docs/09-plano-de-testes.md` (CT ligados aos RF que já cobrem) |
| 11 | O que o cliente pediu agora (se houver) | `docs/08-backlog.md`: só o trabalho novo vira HU; o existente não |

## Regras

- **Origem de cada item:** na coluna Origem dos requisitos use `Código: caminho/arquivo` (ex.: `Código: src/routes/pedidos.ts`). Nos demais documentos, cite o arquivo entre crases ao lado do item.
- **Inferido não é confirmado:** comportamento que parece bug, código morto ou regra sem motivo claro vira pergunta ao cliente (P-xx) e entra como "Premissa", não como requisito firme.
- **Fidelidade à stack real:** a arquitetura descreve a stack que está no código, não a sugerida pelo perfil. Se o projeto usa uma convenção (nomes, pastas, estilo), registre-a em `docs/07-arquitetura.md` para as próximas implementações seguirem.
- **Dívidas e riscos:** problemas encontrados (dependência desatualizada, falta de teste, falha de segurança) vão para os riscos da visão ou para `docs/12-seguranca.md` (achados SEG), nunca corrigidos em silêncio.
- **Rastreabilidade:** onde o código for tocado no futuro, os comentários com IDs (`// HU-003 · RN-002`) ligam código e documentos. Não saia inserindo IDs no código agora.
- Proporcional ao sistema: um projeto pequeno gera documentos curtos. Seção que não se aplica: "Não se aplica" e o motivo.

## Saída

Rode `{{prumo}} validar` e `{{prumo}} rastreabilidade`. Responda em poucas linhas: quantos RF/RN/UC/tabelas foram mapeados, as perguntas abertas ao cliente, riscos encontrados e o próximo passo (normalmente revisar com o usuário e aprovar com `{{prumo}} aprovar`).
