## Profile conventions: automation, integration or bot

### Suggested structure (Python)

```text
src/<package>/
  tasks/                 # one task/job per file
  integrations/          # external API clients (one per system)
  storage/               # state persistence and run history
  config.py              # reading environment variables
  main.py                # entry point / scheduler
tests/
```

Quick start: `python -m venv .venv`, `pip install httpx pydantic-settings apscheduler pytest ruff` (+ `playwright` and `playwright install` if you need a browser).

### Patterns

- **Idempotency:** running the same task twice must not duplicate effects; use deduplication keys.
- **Failures:** timeout on every external call, retry with exponential backoff, and an alert (e-mail/Telegram) when it fails for good.
- **Limits:** respect the sites' rate limits, terms of use and `robots.txt`; scraping only with authorization from the client and the data owner.
- **Structured logs** with a run ID; never log tokens or full personal data.
- **State:** record each run (start, end, status, items processed) for auditing and reprocessing.
- **Configuration** only through environment variables; `.env.example` documents each key.

### Tests

- Integrations tested with recorded responses (fixtures) or a fake server; never call production in tests.
- Suggested commands: format `ruff format {arquivo}`, lint `ruff check {arquivo}`, test `pytest -q`.
