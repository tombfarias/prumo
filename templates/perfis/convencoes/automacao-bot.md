## Convenções do perfil: automação, integração ou bot

### Estrutura sugerida (Python)

```text
src/<pacote>/
  tarefas/               # uma tarefa/job por arquivo
  integracoes/           # clientes de APIs externas (um por sistema)
  armazenamento/         # persistência de estado e histórico de execuções
  config.py              # leitura de variáveis de ambiente
  principal.py           # ponto de entrada / agendador
tests/
```

Início rápido: `python -m venv .venv`, `pip install httpx pydantic-settings apscheduler pytest ruff` (+ `playwright` e `playwright install` se precisar de navegador).

### Padrões

- **Idempotência:** rodar a mesma tarefa duas vezes não pode duplicar efeitos; use chaves de deduplicação.
- **Falhas:** timeout em toda chamada externa, retry com backoff exponencial, e alerta (e-mail/Telegram) quando falhar de vez.
- **Limites:** respeite rate limits, termos de uso e `robots.txt` dos sites; raspagem só com autorização do cliente e do dono dos dados.
- **Logs estruturados** com ID de execução; nunca registre tokens nem dados pessoais completos.
- **Estado:** registre cada execução (início, fim, status, itens processados) para auditoria e reprocessamento.
- **Configuração** só por variáveis de ambiente; `.env.example` documenta cada chave.

### Testes

- Integrações testadas com respostas gravadas (fixtures) ou servidor falso; nada de chamar produção nos testes.
- Comandos sugeridos: formatar `ruff format {arquivo}`, lint `ruff check {arquivo}`, testar `pytest -q`.
