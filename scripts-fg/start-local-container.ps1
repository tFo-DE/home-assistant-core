[CmdletBinding()]
param(
    [string]$ComposeFile = "compose-qnap.yml",
    [string]$EnvFile = ".env.fg-dev",
    [string]$Service = "homeassistant",
    [switch]$PullImage,
    [switch]$Recreate,
    [switch]$FollowLogs
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $RepoRoot
$ComposePath = Join-Path $RepoRoot $ComposeFile
$EnvPath = Join-Path $RepoRoot $EnvFile

if (-not (Test-Path $ComposePath)) {
    throw "Compose file not found: $ComposePath"
}

if (-not (Test-Path $EnvPath)) {
    throw "Env file not found: $EnvPath"
}

if (-not (Test-Path (Join-Path $RepoRoot "config"))) {
    throw "Local config directory missing: $(Join-Path $RepoRoot 'config')"
}

function Get-SecretValue([string]$Path, [string]$Key) {
    $line = Get-Content -LiteralPath $Path | Where-Object {
        $_ -match "^\s*$Key\s*:\s*"
    } | Select-Object -First 1
    if (-not $line) {
        return $null
    }
    $parts = $line -split ":", 2
    if ($parts.Count -lt 2) {
        return $null
    }
    return $parts[1].Trim().Trim("'").Trim('"')
}

function Get-EnvValue([string]$Path, [string]$Key, [string]$Default) {
    $line = Get-Content -LiteralPath $Path | Where-Object {
        $_ -match "^\s*$Key\s*="
    } | Select-Object -First 1
    if (-not $line) {
        return $Default
    }
    $parts = $line -split "=", 2
    if ($parts.Count -lt 2 -or [string]::IsNullOrWhiteSpace($parts[1])) {
        return $Default
    }
    return $parts[1].Trim()
}

$httpPort = Get-EnvValue -Path $EnvPath -Key "HA_HTTP_PORT" -Default "8123"
$secretsPath = Join-Path $RepoRoot "config\secrets.yaml"
if (-not (Test-Path $secretsPath)) {
    throw "Secrets file not found: $secretsPath"
}

$dbUrl = Get-SecretValue -Path $secretsPath -Key "ha_db_url"
if ([string]::IsNullOrWhiteSpace($dbUrl)) {
    throw "No 'ha_db_url' entry found in $secretsPath"
}

try {
    $dbUri = [System.Uri]$dbUrl
}
catch {
    throw "Could not parse ha_db_url in $secretsPath"
}

if ($dbUri.Scheme -notin @("postgresql", "postgres")) {
    throw "ha_db_url must use postgres/postgresql for local DEV postgres setup. Current scheme: $($dbUri.Scheme)"
}

$dbUserInfo = $dbUri.UserInfo
$dbUser = ""
$dbPassword = ""
if (-not [string]::IsNullOrWhiteSpace($dbUserInfo)) {
    $parts = $dbUserInfo -split ":", 2
    $dbUser = [System.Uri]::UnescapeDataString($parts[0])
    if ($parts.Count -gt 1) {
        $dbPassword = [System.Uri]::UnescapeDataString($parts[1])
    }
}
if ([string]::IsNullOrWhiteSpace($dbUser)) {
    $dbUser = "homeassistant"
}
if ([string]::IsNullOrWhiteSpace($dbPassword)) {
    $dbPassword = "homeassistant"
}

$dbName = $dbUri.AbsolutePath.TrimStart("/")
if ([string]::IsNullOrWhiteSpace($dbName)) {
    $dbName = "homeassistant"
}

$dbPort = if ($dbUri.Port -gt 0) { "$($dbUri.Port)" } else { "5432" }
$dbHostAlias = if ([string]::IsNullOrWhiteSpace($dbUri.Host)) { "tfo-postgresql" } else { $dbUri.Host }
if ($dbHostAlias -ne "tfo-postgresql") {
    throw "ha_db_url host must be 'tfo-postgresql' for this local DEV compose setup. Current host: $dbHostAlias"
}

$env:DEV_DB_USER = $dbUser
$env:DEV_DB_PASSWORD = $dbPassword
$env:DEV_DB_NAME = $dbName
$env:DEV_DB_PORT = $dbPort

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Home Assistant local DEV container" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Repo:    $RepoRoot"
Write-Host "Compose: $ComposePath"
Write-Host "Env:     $EnvPath"
Write-Host "Service: $Service"
Write-Host "DB host: tfo-postgresql (local container), DB: $dbName, User: $dbUser, Port: $dbPort"
Write-Host ""

if ($PullImage) {
    Write-Host "[1/4] Pulling image..." -ForegroundColor Yellow
    docker compose --env-file $EnvPath -f $ComposePath pull $Service
}
else {
    Write-Host "[1/4] Pull skipped (use -PullImage to enable)." -ForegroundColor DarkYellow
}

$upArgs = @("compose", "--env-file", $EnvPath, "-f", $ComposePath, "up", "-d")
if ($Recreate) {
    $upArgs += "--force-recreate"
}
$upArgs += $Service

Write-Host "[2/4] Starting container..." -ForegroundColor Yellow
docker @upArgs

Write-Host "[3/4] Container status..." -ForegroundColor Yellow
docker compose --env-file $EnvPath -f $ComposePath ps

Write-Host "[4/4] Waiting for HTTP endpoint on http://localhost:$httpPort ..." -ForegroundColor Yellow
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$httpPort" -Method Get -UseBasicParsing -TimeoutSec 2
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
    Write-Warning "Endpoint did not become reachable in time. Check logs with: docker compose --env-file $EnvPath -f $ComposePath logs $Service"
}

if ($FollowLogs) {
    docker compose --env-file $EnvPath -f $ComposePath logs -f $Service
}
