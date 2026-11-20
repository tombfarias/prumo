# Teste do módulo Prumo.psm1 (rodado no CI em PowerShell 7 e Windows PowerShell 5.1).
$ErrorActionPreference = 'Stop'
git config --global user.name "CI"
git config --global user.email "ci@example.com"
Import-Module (Join-Path $PSScriptRoot '..\powershell\Prumo.psm1') -Force -DisableNameChecking

prumo --versao
$demo = Join-Path ([System.IO.Path]::GetTempPath()) ("prumo-ps-" + [guid]::NewGuid().ToString('N'))
prumo novo $demo --perfil minimo --nome "Demonstração" --cliente "Cliente Ação" --sem-git
if ($LASTEXITCODE -ne 0) { throw 'prumo novo falhou' }
Push-Location $demo
try {
    $s = Get-PrumoStatus
    if ($s.projeto -ne 'Demonstração') { throw "status: acentos ou JSON incorretos: $($s.projeto)" }

    $r = Send-Claude 'Olá, "teste" com aspas e acentuação' -Simular -Json
    if (-not $r.prompt.Contains('"teste" com aspas e acentuação')) { throw "prompt incorreto: $($r.prompt)" }

    $t = Invoke-PrumoTarefa requisitos -Texto 'foco em LGPD' -Simular -Json
    if (-not $t.prompt.Contains('levantar-requisitos')) { throw 'tarefa incorreta' }
    if (-not $t.prompt.Contains('foco em LGPD')) { throw 'instruções extras perdidas' }

    $h = @(Get-PrumoHistorico)
    Write-Host "PowerShell $($PSVersionTable.PSVersion): ok ($($h.Count) execuções no histórico)"
}
finally {
    Pop-Location
    Remove-Item -Recurse -Force -LiteralPath $demo
}
