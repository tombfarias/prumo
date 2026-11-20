---
name: gerar-executavel
description: Gera os executáveis do Prumo para Windows (prumo.exe e prumo-app.exe) com PyInstaller, localmente pelo build.ps1 ou pelo GitHub Actions a cada push na main (Release da versão). Use quando pedirem para gerar, atualizar ou publicar o executável do Prumo.
---

# Gerar o executável do Prumo

## Opção A — na máquina Windows (rápido)

1. Pré-requisito: Python 3.9+ no PATH.
2. Na pasta do Prumo, rode `powershell -ExecutionPolicy Bypass -File .\build.ps1`.
3. O script instala o PyInstaller, gera `dist\prumo.exe` (console, usado pela CLI, pelos hooks e pela interface) e
   `dist\prumo-app.exe` (abre a interface sem janela de console) e copia os dois para a raiz do Prumo.
4. Teste: `.\prumo.exe --versao` e um duplo clique em `prumo-app.exe`.

## Opção B — pelo GitHub Actions (sem precisar de Windows)

1. Para uma versão nova, atualize `VERSAO` em `prumo_cli/util.py`. Faça commit e push na `main`.
2. O workflow `ci` roda os testes (Linux, Windows e macOS), testa o módulo PowerShell (5.1 e 7), gera os executáveis,
   testa o `prumo.exe` (criar projeto, validar, hooks) e publica ou atualiza a Release `v<VERSAO>` com os dois `.exe`.
3. Download direto: `https://github.com/tombfarias/prumo/releases/latest/download/prumo.exe` (e `prumo-app.exe`).
   Também ficam como artefato `prumo-windows` da execução: `gh run download <id> -n prumo-windows`.

## Cuidados

- Os templates, a interface (`prumo_cli/gui`) e `config/freelancer.exemplo.json` entram no executável via `--add-data`;
  ao criar uma pasta de recursos nova, inclua-a no `build.ps1`, no `build.sh` e confira `RECURSOS` em `prumo_cli/util.py`.
- No executável, `RAIZ_KIT` é a pasta do `.exe` (onde ficam `config/freelancer.json` e `config/projetos.json`).
- Projetos criados pelo `.exe` em máquinas sem Python usam `hooks_via: "prumo"` (os hooks rodam como `prumo.exe hook <nome>`).
