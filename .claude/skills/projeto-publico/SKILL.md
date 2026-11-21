---
name: projeto-publico
description: Regras para trabalhar no repositório público do Prumo sem expor dados pessoais do autor nem da máquina dele (nome, e-mail, caminhos locais, nome do computador, tokens, dados de clientes). Use antes de commitar, fazer push, abrir PR, issue ou release, ao escrever documentação, exemplos ou testes, e quando o guarda de privacidade bloquear algo.
---

# Repositório público: nada pessoal vai para o GitHub

O repositório do Prumo é público (licença MIT). Tudo o que entra em arquivo, mensagem de commit, PR, issue, release
ou descrição do repositório fica visível e indexado, mesmo que seja apagado depois.

## O que nunca publicar

- Dados do autor: nome completo, e-mail pessoal, telefone, CPF/CNPJ, endereço, dados bancários ou PIX.
- Dados da máquina: nome de usuário do sistema, pasta pessoal (`C:\Users\<nome>`, `/home/<nome>`), nome do computador,
  a pasta onde o Prumo está clonado, caminhos de projetos de clientes, saídas de terminal com esses dados.
- Dados de clientes e projetos (nomes, valores, briefings): ficam no projeto de cada cliente, nunca aqui.
- Segredos e estado local: tokens (GitHub, Anthropic, Figma, AWS…), chaves, `.env`, `config/freelancer.json`,
  `config/projetos.json`, `.prumo/`, `CLAUDE.local.md`, `.claude/settings.local.json` e executáveis gerados na máquina
  (o PyInstaller grava caminhos locais neles; os `.exe` públicos saem só pelo CI, nas Releases).

## Como escrever exemplos

- Caminhos: `C:\Prumo`, `D:\Projetos\loja-da-ana`, `~/prumo`; nunca a pasta real.
- E-mails: `voce@exemplo.com` ou domínios reservados (`example.com`, `exemplo.com.br`, `.test`).
- Pessoas e empresas fictícias (Ana Doces, Loja da Ana). CPF de exemplo: `123.456.789-09`.
- Nos testes, monte dados sensíveis fictícios em tempo de execução (por exemplo `"ghp" + "_" + ...`) para o guarda
  não disparar no próprio arquivo de teste.
- Antes de colar logs em docs, issues ou PRs, troque usuário e caminhos por exemplos.

## Configuração de cada clone

```bash
python .githooks/privacidade.py instalar
git config user.name "<login-do-github>"
git config user.email "<id>+<login-do-github>@users.noreply.github.com"
python .githooks/privacidade.py tudo --historico
```

- O nome do commit precisa ser o login do GitHub: o `user.name` vira termo pessoal, e só o login (dono do `origin`
  ou o do e-mail noreply) é liberado.
- O e-mail noreply aparece em GitHub → Settings → Emails; lá, ative também "Keep my email addresses private" e
  "Block command line pushes that expose my email".
- Crie `~/.prumo/privado.txt` (no Windows, `%USERPROFILE%\.prumo\privado.txt`; fora do repositório) com o que a
  máquina não revela sozinha: nome completo, telefone, CPF, endereço, nomes de clientes. Um termo por linha; `#` comenta.
- `instalar` grava os hooks em `.git/hooks` (vale para todos os worktrees). Num checkout sem
  `.githooks/privacidade.py` eles bloqueiam o commit e o push: traga o guarda para o branch antes.

## O guarda automático (`.githooks/privacidade.py`)

| Onde | O que verifica |
|---|---|
| `pre-commit` (git) | nome e conteúdo completo dos arquivos preparados e a identidade (autor/committer) do commit |
| `commit-msg` (git) | a mensagem do commit, inclusive linhas que começam com `#` |
| `pre-push` (git) | cada commit, tag e objeto que o remoto de destino ainda não tem: autor, committer, mensagem, nomes e conteúdo dos arquivos alterados |
| Hook do Claude (`.claude/settings.json`) | bloqueia `--no-verify` (até abreviado ou só citado no comando), `git commit -n`, `-c core.hooksPath`/`alias.`, variáveis que desligam o guarda, mudanças em `core.hooksPath` e em `.git/hooks`, `gh api` que grava no repositório e `gh` dentro de `bash -c`; exige os hooks instalados; varre o que `gh pr/issue/release/gist/repo/api` vai publicar (argumentos, heredocs, `--body-file`, `-F campo=@arquivo`, `$(cat arquivo)`, anexos de release) e recusa texto vindo da entrada padrão ou de variáveis |
| CI | `privacidade.py tudo --historico` com as regras genéricas |

O conteúdo é lido em UTF-8, UTF-16 (padrão do `>` no Windows PowerShell 5.1), CP1252 e, em binários, o texto
legível e o de dentro de ZIP (docx/xlsx), PDF e PNG; escapes (`\u`, `%XX`, `&...;`) são desfeitos, e termos de
várias palavras são achados com hífen, sublinhado, sem espaço ou quebrados entre linhas.
Se o git falhar, o guarda bloqueia em vez de liberar.

O que ele procura:
- termos desta máquina, descobertos na hora (nada pessoal fica gravado no repositório): usuário do sistema, pasta
  pessoal, nome do computador, pasta do clone, e-mails e nome do git, `config/freelancer.json` e as pastas de
  `config/projetos.json`;
- os termos de `~/.prumo/privado.txt`;
- regras genéricas: e-mails reais, pastas de usuário, tokens e chaves, URL com senha, CPF/CNPJ válidos e arquivos
  proibidos.

Auditoria manual: `python .githooks/privacidade.py tudo` (arquivos versionados e novos) e
`python .githooks/privacidade.py tudo --historico` (também todos os commits e tags).

## Quando o guarda bloquear

1. Corrija o conteúdo (troque por um exemplo genérico) e repita. Nunca use `--no-verify`, `-n`, `-c core.hooksPath`,
   `PRUMO_PRIVACIDADE_AMBIENTE=0` nem mexa em `core.hooksPath` ou em `.git/hooks`.
2. Falso positivo de regra genérica de conteúdo (um e-mail de exemplo com domínio real, por exemplo): acrescente
   `privacidade:ignorar` na linha e explique no commit. Termos pessoais, arquivos proibidos e identidade não aceitam
   exceção; se um termo de `~/.prumo/privado.txt` é genérico demais, ajuste o arquivo.
3. Para citar `--no-verify` num texto (docs, skill), grave o arquivo com a ferramenta de arquivos, não num comando
   que também commita.
4. Dado em commit local que ainda não subiu: corrija com `git commit --amend` (último commit) ou rebase local.

## Se algo já foi publicado

Pare e avise o usuário. Segredo publicado: revogue e gere outro imediatamente, porque reescrever o histórico não apaga
as cópias já feitas. Dado pessoal no histórico: apresente as opções (remover no próximo commit; reescrever o histórico
com `git filter-repo` e force push; pedir ao suporte do GitHub a limpeza de caches) e só reescreva o histórico ou faça
force push com autorização explícita do usuário.
