# Executável

O Prumo é distribuído em dois executáveis para Windows, gerados com o PyInstaller:

| Arquivo | Para quê |
|---|---|
| `prumo.exe` | Linha de comando. Também é usado pela interface (para rodar os comandos) e, em máquinas sem Python, pelos hooks |
| `prumo-app.exe` | Abre a interface gráfica sem janela de console (duplo clique) |

Os dois embutem os templates, a interface e o Python. Devem ficar na mesma pasta; `config\` é criada ao lado.

## Baixar

Cada tag de versão (`v*`) gera uma *Release* no GitHub com os dois arquivos. Execuções na branch `main` deixam os executáveis como artefato `prumo-windows` da execução do workflow:

```powershell
gh run list --workflow ci --limit 5
gh run download <id> --name prumo-windows --dir D:\SistemaCodigo
```

## Gerar na sua máquina

```powershell
cd D:\SistemaCodigo
powershell -ExecutionPolicy Bypass -File .\build.ps1          # gera em dist\ e copia para a raiz
powershell -ExecutionPolicy Bypass -File .\build.ps1 -SoDist  # só gera em dist\
```

Linux/macOS: `./build.sh` (gera `dist/prumo`).

## O que o GitHub Actions faz (`.github/workflows/ci.yml`)

1. **testes**: suíte completa no Linux, Windows e macOS.
2. **powershell**: testa o módulo `Prumo.psm1` no PowerShell 7 e no Windows PowerShell 5.1 (acentos, aspas, JSON).
3. **executavel**: gera os `.exe`, cria um projeto com o `prumo.exe`, valida, gera a rastreabilidade e confere os hooks (`prumo.exe hook guarda_comandos` bloqueando `rm -rf /`).
4. Em tags `v*`, publica a Release.

Para lançar uma versão: atualize `VERSAO` em `prumo_cli/util.py`, faça commit e `git tag v0.2.0 && git push origin v0.2.0`.

## Observações

- O Windows SmartScreen pode avisar na primeira execução de um executável não assinado: "Mais informações" → "Executar assim mesmo".
- Alguns antivírus desconfiam de executáveis do PyInstaller. Se acontecer, gere o seu com o `build.ps1` ou use o Python.
- O `.exe` extrai os recursos para uma pasta temporária a cada execução; por isso o primeiro comando pode levar um ou dois segundos.
