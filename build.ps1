<#
.SYNOPSIS
  Gera os executáveis do Prumo para Windows com o PyInstaller:
    prumo.exe      linha de comando (também usada pelos hooks e pela interface)
    prumo-app.exe  interface gráfica, sem janela de console (duplo clique)
.EXAMPLE
  .\build.ps1             # gera em .\dist e copia para a raiz do Prumo
  .\build.ps1 -SoDist     # só gera em .\dist
#>
param([switch]$SoDist)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

python -m pip install --upgrade --quiet pyinstaller
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar o PyInstaller.' }

$sep = [System.IO.Path]::PathSeparator   # ';' no Windows
$dados = @("templates${sep}templates", "config/freelancer.exemplo.json${sep}config", "prumo_cli/gui${sep}prumo_cli/gui")
$comum = @('--noconfirm', '--clean', '--onefile', '--icon', 'assets/prumo.ico', '--hidden-import', 'tkinter', '--hidden-import', 'tkinter.filedialog')
foreach ($d in $dados) { $comum += @('--add-data', $d) }

python -m PyInstaller @comum --name prumo --console prumo.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar prumo.exe' }
python -m PyInstaller @comum --name prumo-app --windowed prumo_app.py
if ($LASTEXITCODE -ne 0) { throw 'Falha ao gerar prumo-app.exe' }

& .\dist\prumo.exe --versao
if (-not $SoDist) {
    Copy-Item .\dist\prumo.exe, .\dist\prumo-app.exe -Destination . -Force
    Write-Host "Executáveis copiados para $PSScriptRoot (prumo.exe e prumo-app.exe)."
}
