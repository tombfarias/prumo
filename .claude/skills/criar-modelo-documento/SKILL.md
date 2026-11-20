---
name: criar-modelo-documento
description: Adiciona um novo modelo de documento de especificação ao Prumo (ex.: LGPD/RIPD, plano de comunicação, SLA), integrado aos perfis, à rastreabilidade e às skills. Use quando pedirem um novo tipo de documento nos projetos.
---

# Criar um modelo de documento

1. Crie `templates/documentos/<NN>-<nome>.md` seguindo o padrão: título com `{{projeto}}`, orientações em comentários
   HTML (`<!-- -->`, ignorados pela validação e pela rastreabilidade) e lacunas `[PREENCHER: dica]`.
2. Se o documento define itens rastreáveis, use um prefixo de ID: os existentes estão em `PREFIXOS` (`prumo_cli/rastreio.py`).
   Para um prefixo novo, adicione-o em `PREFIXOS` e `NOMES`, na tabela de IDs de `templates/agentes/AGENTS.md` e em `ORDEM_CONTEXTO`
   (`prumo_cli/validacao.py`). Defina cada item no título (`### XX-001 — Nome`) ou na 1ª coluna de uma tabela.
3. Exemplos no modelo só podem citar IDs que o próprio modelo define ou que todo perfil tem; os órfãos viram "—" na criação,
   mas é melhor evitá-los.
4. Descreva o documento em `DESCRICOES` (`prumo_cli/projeto.py`) e inclua-o nos perfis que devem tê-lo.
5. Se uma skill deve preencher o documento, crie ou ajuste a skill em `templates/agentes/claude/skills/` e, se fizer sentido,
   uma tarefa em `TAREFAS` (`prumo_cli/claude.py`) e na lista da interface (`prumo_cli/gui/index.html`).
6. Rode os testes e documente em `docs/perfis-e-modelos.md`.
