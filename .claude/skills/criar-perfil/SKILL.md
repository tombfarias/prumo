---
name: criar-perfil
description: Cria um novo perfil de projeto (template comum) no Prumo, com documentos, stack sugerida, convenções, pastas e comandos sugeridos. Use quando pedirem um novo tipo de projeto/template (ex.: e-commerce, extensão de navegador, jogo, API GraphQL).
---

# Criar um perfil de projeto

1. Copie um perfil parecido de `templates/perfis/<id>.json` para `templates/perfis/<novo-id>.json` (id em kebab-case).
2. Ajuste os campos:
   - `nome`, `descricao` (uma frase: para que tipo de cliente/projeto serve), `stack` (com alternativa);
   - `stack_padrao`: camada → id de `templates/catalogos/stacks.json` (pré-marca o passo Técnico do formulário;
     `{}` se não houver padrão). Tecnologia que falta no catálogo: acrescente-a lá primeiro;
   - `documentos`: ids de `templates/documentos/` (sem `.md`; UML como `04-uml/classes`). Mantenha sempre
     `00-briefing`, `01-visao`, `02-requisitos`, `08-backlog` e `12-seguranca`;
   - `pastas`: pastas de código (entram em `pastas_codigo` e na varredura de rastreabilidade e segurança);
   - `figma`: `true` se o projeto tem interface;
   - `comandos_sugeridos`: `formatar`/`lint` com `{arquivo}` e `testar`;
   - `convencoes`: `<novo-id>.md`.
3. Escreva `templates/perfis/convencoes/<novo-id>.md` no padrão dos outros: estrutura de pastas, comandos de início
   (só comandos oficiais que você confirmou), padrões, segurança e testes. Esse texto entra no AGENTS.md de cada projeto:
   seja objetivo, ele custa tokens em toda sessão.
4. Rode `python -m unittest discover -s tests -v` (o teste `test_todos_os_perfis` cria um projeto com o perfil novo e valida tudo).
5. Teste à mão: `python prumo.py novo /tmp/teste --perfil <novo-id> --sem-git` e `python prumo.py --projeto /tmp/teste validar`.
6. Documente o perfil em `docs/perfis-e-modelos.md`.
