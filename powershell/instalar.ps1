<#
.SYNOPSIS
  Instala o Prumo no PowerShell: importa o módulo em toda sessão e (opcionalmente) coloca a pasta no PATH.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\powershell\instalar.ps1 -AdicionarAoPath
#>
param([switch]$AdicionarAoPath)

$raiz = Split-Path -Parent $PSScriptRoot
$modulo = Join-Path $PSScriptRoot 'Prumo.psm1'
$perfil = $PROFILE.CurrentUserAllHosts
$linha = "Import-Module `"$modulo`" -DisableNameChecking"

if (-not (Test-Path -LiteralPath $perfil)) { New-Item -ItemType File -Path $perfil -Force | Out-Null }
$conteudo = Get-Content -LiteralPath $perfil -Raw -ErrorAction SilentlyContinue
if (-not $conteudo -or -not $conteudo.Contains($modulo)) {
    Add-Content -LiteralPath $perfil -Value "`n# Prumo`n$linha"
    Write-Host "Módulo adicionado ao perfil do PowerShell: $perfil"
} else {
    Write-Host "O perfil do PowerShell já importa o Prumo."
}

if ($AdicionarAoPath) {
    $atual = [Environment]::GetEnvironmentVariable('Path', 'User')
    if (-not ($atual -split ';' | Where-Object { $_ -eq $raiz })) {
        [Environment]::SetEnvironmentVariable('Path', ($atual.TrimEnd(';') + ";$raiz"), 'User')
        Write-Host "Pasta adicionada ao PATH do usuário: $raiz (abra um novo terminal)."
    }
}

if ((Get-ExecutionPolicy -Scope CurrentUser) -in 'Restricted', 'Undefined' -and (Get-ExecutionPolicy) -eq 'Restricted') {
    Write-Host "Se o PowerShell bloquear o módulo, rode: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" -ForegroundColor Yellow
}
Write-Host "Pronto. Abra um novo PowerShell e teste:  prumo --versao   |   Send-Claude 'olá' -Simular"
