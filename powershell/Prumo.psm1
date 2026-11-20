<#
.SYNOPSIS
  Módulo do Prumo para PowerShell: comandos do Prumo e envio de tarefas ao Claude Code.

.DESCRIPTION
  Importe com:  Import-Module "<pasta do Prumo>\powershell\Prumo.psm1"
  (ou rode instalar.ps1 para importar automaticamente em toda sessão).

  Funções:
    prumo / Invoke-Prumo        Qualquer comando do Prumo (ex.: prumo status, prumo validar)
    Send-Claude                 Envia um pedido livre ao Claude Code no projeto atual
    Invoke-PrumoTarefa          Executa uma tarefa do fluxo (requisitos, implementar HU-003, revisar...)
    Get-PrumoStatus             Status do projeto como objeto do PowerShell
    Get-PrumoHistorico          Execuções anteriores do Claude como objetos
    Start-PrumoGui              Abre a interface gráfica
#>

$script:RaizKit = Split-Path -Parent $PSScriptRoot
$script:Tarefas = @('especificar', 'requisitos', 'casos-de-uso', 'uml', 'banco', 'arquitetura', 'backlog', 'testes',
                    'proposta', 'implementar', 'revisar', 'documentar', 'seguranca', 'mudanca', 'tela', 'figjam', 'livre')

function Get-PrumoComando {
    <# Retorna o executável e os argumentos iniciais para chamar o Prumo (prumo.exe ou Python + prumo.py). #>
    $exe = Join-Path $script:RaizKit 'prumo.exe'
    if (Test-Path -LiteralPath $exe) { return @($exe) }
    $py = Join-Path $script:RaizKit 'prumo.py'
    foreach ($nome in 'python', 'py', 'python3') {
        $cmd = Get-Command $nome -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return @($cmd.Source, $py) }
    }
    throw "Prumo: não encontrei prumo.exe nem o Python. Instale o Python 3.9+ ou gere o executável (build.ps1)."
}

function Invoke-PrumoBruto {
    param([string[]]$Argumentos, [switch]$CapturarJson)
    $base = @(Get-PrumoComando)
    $exe = $base[0]
    $todos = @()
    if ($base.Count -gt 1) { $todos += $base[1..($base.Count - 1)] }
    $todos += $Argumentos
    $codificacaoAnterior = [Console]::OutputEncoding
    $env:PYTHONIOENCODING = 'utf-8'
    try {
        [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
        if ($CapturarJson) {
            $saida = & $exe @todos
            $texto = ($saida | Out-String).Trim()
            if (-not $texto) { return $null }
            return $texto | ConvertFrom-Json
        }
        & $exe @todos
    }
    finally {
        [Console]::OutputEncoding = $codificacaoAnterior
    }
}

function Invoke-Prumo {
    <#
    .SYNOPSIS  Executa qualquer comando do Prumo.
    .EXAMPLE   prumo novo D:\Projetos\loja --perfil web-fullstack --nome "Loja" --cliente "Ana"
    .EXAMPLE   prumo validar
    #>
    Invoke-PrumoBruto -Argumentos $args
}
Set-Alias -Name prumo -Value Invoke-Prumo

function ConvertTo-ArquivoTemporario([string]$Texto) {
    # O pedido vai por arquivo UTF-8: evita problemas de aspas e acentos na passagem de argumentos (PowerShell 5.1 e 7).
    $tmp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "prumo-" + [guid]::NewGuid().ToString('N') + ".txt")
    [System.IO.File]::WriteAllText($tmp, $Texto, [System.Text.UTF8Encoding]::new($false))
    return $tmp
}

function Invoke-PrumoTarefa {
    <#
    .SYNOPSIS  Executa uma tarefa do Prumo no Claude Code (modo não interativo).
    .PARAMETER Tarefa      Etapa ou ação: especificar, requisitos, casos-de-uso, uml, banco, arquitetura, backlog,
                           testes, proposta, implementar, revisar, documentar, seguranca, mudanca, tela, figjam, livre.
    .PARAMETER Alvo        ID alvo (HU-003, TL-002...) quando a tarefa pede.
    .PARAMETER Texto       Instruções adicionais (ou o pedido, na tarefa livre/mudança).
    .PARAMETER Projeto     Pasta do projeto (padrão: a atual).
    .PARAMETER Continuar   Continua a última sessão do Claude neste projeto.
    .PARAMETER Permitir    Ferramentas extras liberadas (ex.: 'Bash(npm test:*)').
    .PARAMETER Simular     Mostra o comando e o prompt sem executar.
    .PARAMETER Json        Devolve o resultado como objeto (o progresso continua no console).
    .EXAMPLE   Invoke-PrumoTarefa implementar HU-003
    .EXAMPLE   Invoke-PrumoTarefa especificar -SemPausa
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, Position = 0)]
        [ValidateSet('especificar', 'requisitos', 'casos-de-uso', 'uml', 'banco', 'arquitetura', 'backlog', 'testes',
                     'proposta', 'implementar', 'revisar', 'documentar', 'seguranca', 'mudanca', 'tela', 'figjam', 'livre')]
        [string]$Tarefa,
        [Parameter(Position = 1)][string]$Alvo,
        [string]$Texto,
        [string]$Projeto = (Get-Location).Path,
        [switch]$Continuar,
        [string]$Sessao,
        [string]$Modelo,
        [int]$MaxTurnos,
        [string[]]$Permitir,
        [ValidateSet('default', 'acceptEdits', 'plan', 'bypassPermissions')][string]$Modo,
        [switch]$SemPausa,
        [switch]$Simular,
        [switch]$Json
    )
    $argumentos = @('--projeto', $Projeto)
    if ($Json) { $argumentos += '--json' }
    $argumentos += @('claude', $Tarefa)
    if ($Alvo) { $argumentos += $Alvo }
    $tmp = $null
    if ($Texto) { $tmp = ConvertTo-ArquivoTemporario $Texto; $argumentos += @('--texto-arquivo', $tmp) }
    if ($Continuar) { $argumentos += '--continuar' }
    if ($Sessao) { $argumentos += @('--sessao', $Sessao) }
    if ($Modelo) { $argumentos += @('--modelo', $Modelo) }
    if ($MaxTurnos) { $argumentos += @('--max-turnos', "$MaxTurnos") }
    foreach ($p in $Permitir) { $argumentos += @('--permitir', $p) }
    if ($Modo) { $argumentos += @('--modo', $Modo) }
    if ($SemPausa) { $argumentos += '--sem-pausa' }
    if ($Simular) { $argumentos += '--simular' }
    try {
        Invoke-PrumoBruto -Argumentos $argumentos -CapturarJson:$Json
    }
    finally {
        if ($tmp) { Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue }
    }
}

function Send-Claude {
    <#
    .SYNOPSIS  Envia um pedido livre ao Claude Code no projeto do Prumo.
    .EXAMPLE   Send-Claude "Crie o componente de listagem de pedidos seguindo a TL-004"
    .EXAMPLE   Get-Content pedido.txt -Raw | Send-Claude -Continuar
    .EXAMPLE   $r = Send-Claude "Liste as rotas sem testes" -Json; $r.resumo
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory, Position = 0, ValueFromPipeline)][string]$Pedido,
        [string]$Projeto = (Get-Location).Path,
        [switch]$Continuar,
        [string]$Modelo,
        [string[]]$Permitir,
        [switch]$SomenteLeitura,
        [switch]$Simular,
        [switch]$Json
    )
    begin { $partes = New-Object System.Collections.Generic.List[string] }
    process { $partes.Add($Pedido) }
    end {
        $parametros = @{ Tarefa = 'livre'; Texto = ($partes -join "`n"); Projeto = $Projeto; Continuar = $Continuar;
                         Simular = $Simular; Json = $Json }
        if ($Modelo) { $parametros.Modelo = $Modelo }
        if ($Permitir) { $parametros.Permitir = $Permitir }
        if ($SomenteLeitura) { $parametros.Modo = 'plan' }
        Invoke-PrumoTarefa @parametros
    }
}

function Get-PrumoStatus {
    <# .SYNOPSIS Status do projeto (documentos, lacunas, IDs) como objeto. #>
    param([string]$Projeto = (Get-Location).Path)
    Invoke-PrumoBruto -Argumentos @('--projeto', $Projeto, '--json', 'status') -CapturarJson
}

function Get-PrumoHistorico {
    <# .SYNOPSIS Execuções anteriores do Claude neste projeto. #>
    param([string]$Projeto = (Get-Location).Path, [int]$Limite = 20)
    Invoke-PrumoBruto -Argumentos @('--projeto', $Projeto, '--json', 'claude', 'historico', '--limite', "$Limite") -CapturarJson
}

function Start-PrumoGui {
    <# .SYNOPSIS Abre a interface gráfica do Prumo (opcionalmente já no projeto informado). #>
    param([string]$Projeto)
    $argumentos = @()
    if ($Projeto) { $argumentos += @('--projeto', $Projeto) }
    $argumentos += 'gui'
    $base = @(Get-PrumoComando)
    $resto = @()
    if ($base.Count -gt 1) { $resto += $base[1..($base.Count - 1)] }
    Start-Process -FilePath $base[0] -ArgumentList (($resto + $argumentos) | ForEach-Object { '"' + $_ + '"' }) -WindowStyle Hidden
}

Export-ModuleMember -Function Invoke-Prumo, Invoke-PrumoTarefa, Send-Claude, Get-PrumoStatus, Get-PrumoHistorico, Start-PrumoGui -Alias prumo
