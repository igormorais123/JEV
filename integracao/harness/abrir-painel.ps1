$ErrorActionPreference = 'Stop'
$repoDir = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$panelUrl = 'http://127.0.0.1:8767'
$running = $false
try {
    $state = Invoke-RestMethod "$panelUrl/api/state" -TimeoutSec 2
    $running = $null -ne $state.tools
} catch {}
if (-not $running) {
    $stateDir = Join-Path $repoDir 'integracao/estado'
    New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    $pythonExe = (Get-Command python).Source
    Start-Process -FilePath $pythonExe -ArgumentList ('"' + (Join-Path $PSScriptRoot 'painel.py') + '"') -WorkingDirectory $repoDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $stateDir 'harness-server.log') -RedirectStandardError (Join-Path $stateDir 'harness-server-error.log')
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        Start-Sleep -Milliseconds 200
        try { $state = Invoke-RestMethod "$panelUrl/api/state" -TimeoutSec 1; if ($null -ne $state.tools) {$running=$true;break} } catch {}
    }
}
if (-not $running) { throw 'Não foi possível iniciar o painel. Consulte integracao/estado/harness-server-error.log.' }
Start-Process $panelUrl
