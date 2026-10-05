[CmdletBinding()]
param(
    [string]$ComposeFile = "compose-qnap.yml",
    [string]$Service = "homeassistant",
    [switch]$PullImage,
    [switch]$Recreate,
    [switch]$FollowLogs
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $RepoRoot
$ComposePath = Join-Path $RepoRoot $ComposeFile

if (-not (Test-Path $ComposePath)) {
    throw "Compose file not found: $ComposePath"
}

if (-not (Test-Path (Join-Path $RepoRoot "config"))) {
    throw "Local config directory missing: $(Join-Path $RepoRoot 'config')"
}

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Home Assistant local DEV container" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Repo:    $RepoRoot"
Write-Host "Compose: $ComposePath"
Write-Host "Service: $Service"
Write-Host ""

if ($PullImage) {
    Write-Host "[1/4] Pulling image..." -ForegroundColor Yellow
    docker compose -f $ComposePath pull $Service
}
else {
    Write-Host "[1/4] Pull skipped (use -PullImage to enable)." -ForegroundColor DarkYellow
}

$upArgs = @("compose", "-f", $ComposePath, "up", "-d")
if ($Recreate) {
    $upArgs += "--force-recreate"
}
$upArgs += $Service

Write-Host "[2/4] Starting container..." -ForegroundColor Yellow
docker @upArgs

Write-Host "[3/4] Container status..." -ForegroundColor Yellow
docker compose -f $ComposePath ps

Write-Host "[4/4] Waiting for HTTP endpoint on http://localhost:8123 ..." -ForegroundColor Yellow
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8123" -Method Get -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
            $ready = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if ($ready) {
    Write-Host "Home Assistant endpoint is reachable." -ForegroundColor Green
}
else {
    Write-Warning "Endpoint did not become reachable in time. Check logs with: docker compose -f $ComposePath logs $Service"
}

if ($FollowLogs) {
    docker compose -f $ComposePath logs -f $Service
}
