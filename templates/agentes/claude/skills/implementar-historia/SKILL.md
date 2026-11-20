---
name: implementar-historia
description: Implementa uma história de usuário (HU-xxx) seguindo a trilha de especificação (UC, RF, RN, telas, modelo de dados), com testes primeiro, IDs no código e commit rastreável. Use quando pedirem para implementar, codificar ou desenvolver uma história, funcionalidade ou caso de uso.
---

# Implementar uma história

Argumento esperado: o ID da história (ex.: `HU-003`). Se não vier, pergunte qual, listando as histórias `a fazer` de maior prioridade.

## 1. Carregar a trilha

1. Rode `{{prumo}} contexto HU-00N`: ele traz, sem o resto dos documentos, a história, os UCs, RF/RNF/RN, telas, testes e épico ligados a ela.
2. Se precisar de mais, leia só as seções relevantes de `06-banco-de-dados.md`, `07-arquitetura.md` e dos ADRs (busque pelos nomes das entidades/módulos).
4. Verifique a **Definição de Preparado**: se houver `[PREENCHER]` ou contradição na trilha, **pare** e pergunte ao usuário antes de codificar.

## 2. Planejar

Liste ao usuário, em poucas linhas: arquivos a criar/alterar, migrações, testes (com os CT-xxx correspondentes) e riscos. Em histórias grandes, espere o ok.

## 3. Testes primeiro

Escreva os testes a partir dos critérios de aceite e dos CTs de `09-plano-de-testes.md`, com o ID no teste (`// CT-004` ou `# CT-004`). Confirme que falham pelo motivo certo.

## 4. Implementar

- Siga as convenções de `AGENTS.md` e a estrutura da arquitetura.
- Cite a regra onde ela é implementada (`// RN-002`).
- Telas: se a tela tiver link do Figma, use a skill `implementar-tela-figma`.
- Migrações pelo ORM, coerentes com o modelo de dados. Se o modelo precisar mudar, pare e avise (o documento pode estar aprovado).

## 5. Fechar

1. Rode os testes, o lint e `{{prumo}} validar`.
2. Siga `atualizar-documentacao` (documentos afetados pela implementação) e `revisar-seguranca` (arquivos alterados). O hook do Prumo exige isso quando a mudança é significativa.
3. Atualize o status da história no backlog para `em revisão` (se o documento estiver aprovado, informe o usuário em vez de editar).
4. Rode `{{prumo}} rastreabilidade`.
5. Sugira a mensagem de commit: `feat(HU-003): <resumo>` com os UCs no corpo. Só faça commit se o usuário pedir.
6. Recomende rodar `/revisar-conformidade HU-003` (ou o subagente `revisor-conformidade`).
