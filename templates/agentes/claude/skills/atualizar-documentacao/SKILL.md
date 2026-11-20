---
name: atualizar-documentacao
description: Atualiza os documentos de especificação afetados depois de uma mudança significativa no código (banco, rotas, telas, dependências, infraestrutura, testes, configuração), mantendo docs e código coerentes. Use quando o hook do Prumo pedir, ao concluir uma história ou quando pedirem para sincronizar a documentação com o código.
---

# Atualizar a documentação após uma mudança

A especificação só é a fonte da verdade se acompanhar o código. Esta skill fecha o ciclo depois de cada mudança significativa.

## 1. Levantar o que mudou

- Use a lista de arquivos que o hook informou ou, sem ela, `git status` e `git diff` (inclua arquivos novos).
- Para cada arquivo, descubra a que itens da especificação ele pertence: IDs citados no código (`// RN-002`, `// TL-003`) e a história em andamento. Use `{{prumo}} contexto <ID>` para ver só os trechos ligados a cada item, em vez de abrir os documentos inteiros.

## 2. Decidir quais documentos atualizar

| Mudança no código | Documentos a revisar |
|---|---|
| Migrações, schema, models, entidades | `06-banco-de-dados.md` (ER, dicionário, índices, LGPD), `04-uml/classes.md` |
| Rotas, endpoints, controladores, telas, componentes de página | `03-casos-de-uso.md` (fluxos), `04-uml/sequencia.md`, `05-interface.md` |
| Regra de negócio nova ou alterada | `02-requisitos.md` (RN), casos de uso que a aplicam |
| Dependência nova, serviço externo, mudança de estrutura | `07-arquitetura.md` (+ ADR com `{{prumo}} adr`), `04-uml/componentes.md` |
| Docker, CI/CD, hospedagem | `04-uml/implantacao.md`, `07-arquitetura.md`, `11-entrega.md` |
| Variável de ambiente nova | `.env.example`, `07-arquitetura.md` (segredos), `11-entrega.md`, `README.md` |
| Testes novos ou alterados | `09-plano-de-testes.md` (CT-xxx com o caminho do teste) |
| História concluída ou em revisão | `08-backlog.md` (status) |
| Comando de instalação, execução ou convenção nova | `README.md`, `AGENTS.md` |

Só considere os documentos que existem no projeto (`projeto.prumo.json` → `documentos`).

## 3. Atualizar

- Edite só o necessário, mantendo o formato e os IDs existentes. Itens novos recebem o próximo ID livre da sequência.
- **Documento aprovado** (`projeto.prumo.json` → `aprovados`) não pode ser editado (o hook bloqueia). Se a mudança altera o que foi aprovado, isso é mudança de escopo: siga a skill `controle-de-mudancas` e avise o usuário.
- Se o código diverge da especificação sem motivo registrado, **não ajuste o documento para "bater"**: aponte a divergência ao usuário. Ele decide se o código ou a especificação está errado.
- Diagramas Mermaid alterados precisam continuar válidos.

## 4. Conferir

1. `{{prumo}} validar` sem erros.
2. `{{prumo}} rastreabilidade` regenerada.
3. Resuma ao usuário: documentos atualizados (com o motivo), divergências encontradas e o que depende de aprovação do cliente.
