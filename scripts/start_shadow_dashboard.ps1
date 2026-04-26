[CmdletBinding()]
param(
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

function Test-PortInUse {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Port
    )

    $listeners = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
    return $listeners.Port -contains $Port
}

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = Split-Path -Parent $scriptDir
$buildScript = Join-Path $scriptDir "build_shadow_dashboard.py"
$dashboardDir = Join-Path $repoRoot "dashboard"
$dataPath = Join-Path $dashboardDir "data\\dashboard-data.json"
$port = 4173
$url = "http://localhost:$port"

if (-not (Test-Path -LiteralPath $buildScript)) {
    throw "Build script not found: $buildScript"
}

if (-not (Test-Path -LiteralPath $dashboardDir)) {
    throw "Dashboard directory not found: $dashboardDir"
}

if (Test-PortInUse -Port $port) {
    throw "Port $port is already in use. Stop the existing server or free the port, then rerun this script."
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    throw "Python was not found on PATH. Install Python or make sure `python` is available, then rerun this script."
}

Write-Host "Rebuilding dashboard data..."
& $pythonCommand.Source $buildScript

if (-not (Test-Path -LiteralPath $dataPath)) {
    throw "Dashboard data file not found after rebuild: $dataPath"
}

$payload = Get-Content -LiteralPath $dataPath -Raw | ConvertFrom-Json
$version = [uri]::EscapeDataString(($payload.generated_at ?? (Get-Date -Format "yyyyMMddHHmmss")))
$dashboardUrl = "$url/?v=$version"

Write-Host "Starting local server on $url ..."
$serverProcess = Start-Process `
    -FilePath $pythonCommand.Source `
    -ArgumentList @("-m", "http.server", "$port", "--directory", $dashboardDir) `
    -WorkingDirectory $repoRoot `
    -PassThru

Start-Sleep -Seconds 1

if ($serverProcess.HasExited) {
    throw "Dashboard server exited immediately. Check Python output and rerun the script."
}

if (-not $NoOpen) {
    Start-Process $dashboardUrl
}

Write-Host ""
Write-Host "Dashboard is running at $dashboardUrl"
Write-Host "Server PID: $($serverProcess.Id)"
Write-Host "Stop it with: Stop-Process -Id $($serverProcess.Id)"
