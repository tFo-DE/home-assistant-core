# Home Assistant QNAP Deployment Script
# Prefer direct SSH/TAR deployment to the QNAP container filesystem because SMB can
# get stuck behind file locks and permission issues on custom components.

param(
    [string]$QnapIP = "192.168.1.170",
    [string]$QnapUser = "fgAdmin",
    [string]$QnapPath = "/share/dev-fg/home-assistant",
    [string]$LocalDashboard = "lovelace.lovelace",
    [string]$QnapDashboard = "lovelace.dashboard_bov",
    [switch]$CleanupEntityRegistry,
    [switch]$DryRun,
    [string]$LocalRoot = "Q:\home-assistant"
)

$ErrorActionPreference = "Stop"

if ((Test-Path "C:\PythonCode\home-assistant") -and ($LocalRoot -eq "Q:\home-assistant" -or -not (Test-Path $LocalRoot))) {
    $LocalRoot = "C:\PythonCode\home-assistant"
}
elseif (-not (Test-Path $LocalRoot)) {
    if (Test-Path "Q:\home-assistant") {
        $LocalRoot = "Q:\home-assistant"
    }
    else {
        $LocalRoot = (Get-Location).Path
    }
}

$target = "$QnapUser@$QnapIP"
$normalizedQnapPath = $QnapPath.TrimEnd('/')
$smBTarget = "\\$QnapIP\dev-fg\home-assistant"
$smBAvailable = $false

function Invoke-RemoteCommand {
    param([string]$Command)
    ssh $target $Command
}

function Convert-RemotePathToSmb {
    param([string]$RemotePath)

    $relativePath = $RemotePath.Trim()
    $relativePath = $relativePath.TrimEnd('/')

    if ($relativePath -and $relativePath.StartsWith($normalizedQnapPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        $relativePath = $relativePath.Substring($normalizedQnapPath.Length).TrimStart('/')
    }
    elseif ($relativePath -and $relativePath.StartsWith('/')) {
        $relativePath = $relativePath.TrimStart('/')
    }

    if ([string]::IsNullOrWhiteSpace($relativePath)) {
        return $smBTarget
    }

    return Join-Path $smBTarget $relativePath.Replace('/', '\')
}

function Ensure-RemotePathWritable {
    param([string]$RemotePath)

    if ($DryRun) {
        return
    }

    Invoke-RemoteCommand "mkdir -p '$RemotePath' 2>/dev/null; chmod -R a+rwX '$RemotePath' 2>/dev/null || true"
}

function Copy-ToQnap {
    param(
        [string]$LocalPath,
        [string]$RemotePath
    )

    if ($DryRun) {
        Write-Host "[DRY-RUN] would copy $LocalPath -> $RemotePath"
        return
    }

    if ($RemotePath -match '/\.storage/') {
        Write-Host "Skipping .storage copy for $LocalPath because the QNAP .storage directory is not writable by fgAdmin." -ForegroundColor Yellow
        return
    }

    $remoteTarget = "{0}:{1}" -f $target, $RemotePath.TrimEnd('/')
    $remoteDir = if ($RemotePath.EndsWith('/')) { $RemotePath.TrimEnd('/') } else { Split-Path -Parent $RemotePath }
    if ($remoteDir) {
        Ensure-RemotePathWritable -RemotePath $remoteDir
    }

    scp -O $LocalPath $remoteTarget
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: scp failed for $LocalPath -> $RemotePath (exit code $LASTEXITCODE); skipping this target." -ForegroundColor Yellow
    }
}

function Deploy-CustomComponent {
    param([string]$ComponentName)

    if ($DryRun) {
        Write-Host "[DRY-RUN] would deploy component: $ComponentName"
        return
    }

    $componentDir = "$normalizedQnapPath/config/custom_components"
    $backupName = "${ComponentName}_old_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Invoke-RemoteCommand "mkdir -p '$componentDir'; if [ -e '$componentDir/$ComponentName' ]; then mv '$componentDir/$ComponentName' '$componentDir/$backupName' 2>/dev/null || true; fi; chmod -R a+rwX '$componentDir' 2>/dev/null || true"
    tar -C "$LocalRoot\config\custom_components" --exclude='.git' --exclude='__pycache__' --exclude='*/__pycache__' -czf - $ComponentName | ssh $target "cd '$componentDir'; tar -xzf -"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: failed to deploy component $ComponentName via tar; remote directory may still be locked or unreadable." -ForegroundColor Yellow
    }
}

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Home Assistant QNAP Deployment" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
if ($smBAvailable) {
    Write-Host "Using SMB copy path: $smBTarget" -ForegroundColor Green
}
else {
    Write-Host "SMB share not available; falling back to SSH/scp" -ForegroundColor Yellow
}

if ($DryRun) {
    Write-Host "Dry-run enabled; no files will be copied or restarted." -ForegroundColor Yellow
}

$totalSteps = if ($CleanupEntityRegistry) { 11 } else { 9 }
$stepOffset = 1

try {
    Write-Host "[1/$totalSteps] Stopping Home Assistant container..." -ForegroundColor Yellow
    if (-not $DryRun) {
        Invoke-RemoteCommand "cd '$normalizedQnapPath'; /share/CE_CACHEDEV1_DATA/.qpkg/container-station/bin/docker compose stop homeassistant"
        Start-Sleep -Seconds 15
    }

    if ($CleanupEntityRegistry) {
        Write-Host "[2/$totalSteps] Uploading cleanup script..." -ForegroundColor Yellow
        Copy-ToQnap -LocalPath (Join-Path $LocalRoot "scripts-fg\cleanup-sungrow-v1-entities.sh") -RemotePath "$normalizedQnapPath/"

        Write-Host "[3/$totalSteps] Running entity registry cleanup..." -ForegroundColor Yellow
        if (-not $DryRun) {
            Invoke-RemoteCommand "cd '$normalizedQnapPath'; chmod +x cleanup-sungrow-v1-entities.sh; ./cleanup-sungrow-v1-entities.sh"
        }

        $stepOffset = 3
    }

    $backupName = "backup_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".tar.gz"
    Write-Host "[$($stepOffset + 1)/$totalSteps] Creating backup on QNAP..." -ForegroundColor Yellow
    if (-not $DryRun) {
        Invoke-RemoteCommand "cd '$normalizedQnapPath/config'; tar -czf '$backupName' .storage/core.config_entries .storage/$QnapDashboard configuration.yaml templates.yaml --exclude='*.db*' --exclude='*.log*' 2>/dev/null; echo 'Backup completed'"
    }

    Write-Host "[$($stepOffset + 2)/$totalSteps] Cleaning up __pycache__ directories..." -ForegroundColor Yellow
    if (-not $DryRun -and -not $smBAvailable) {
        Invoke-RemoteCommand "find '$normalizedQnapPath/config/custom_components' -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true"
    }

    Write-Host "[$($stepOffset + 3)/$totalSteps] Deploying pv_load_balancer..." -ForegroundColor Yellow
    Deploy-CustomComponent -ComponentName "pv_load_balancer"

    Write-Host "[$($stepOffset + 4)/$totalSteps] Deploying oekofen_pellematic_compact..." -ForegroundColor Yellow
    Deploy-CustomComponent -ComponentName "oekofen_pellematic_compact"

    Write-Host "[$($stepOffset + 5)/$totalSteps] Deploying alfen_modbus..." -ForegroundColor Yellow
    Deploy-CustomComponent -ComponentName "alfen_modbus"

    Write-Host "[$($stepOffset + 6)/$totalSteps] Deploying configuration files..." -ForegroundColor Yellow
    if (-not $DryRun -and -not $smBAvailable) {
        Invoke-RemoteCommand "rm -f '$normalizedQnapPath/config/configuration.yaml' '$normalizedQnapPath/config/templates.yaml' 2>/dev/null; true"
        Invoke-RemoteCommand "mkdir -p '$normalizedQnapPath/config/integrations' 2>/dev/null; true"
    }
    if ($smBAvailable -and -not (Test-Path (Join-Path $smBTarget 'config\integrations'))) {
        New-Item -ItemType Directory -Path (Join-Path $smBTarget 'config\integrations') -Force | Out-Null
    }
    Copy-ToQnap -LocalPath (Join-Path $LocalRoot "config\configuration.yaml") -RemotePath "$normalizedQnapPath/config/"
    Copy-ToQnap -LocalPath (Join-Path $LocalRoot "config\templates.yaml") -RemotePath "$normalizedQnapPath/config/"
    Copy-ToQnap -LocalPath (Join-Path $LocalRoot "config\integrations\modbus_sungrow.yaml") -RemotePath "$normalizedQnapPath/config/integrations/"

    Write-Host "[$($stepOffset + 7)/$totalSteps] Deploying dashboard..." -ForegroundColor Yellow
    if (-not $DryRun -and -not $smBAvailable) {
        Invoke-RemoteCommand "rm -f '$normalizedQnapPath/config/.storage/$QnapDashboard' 2>/dev/null; true"
    }
    Copy-ToQnap -LocalPath (Join-Path $LocalRoot "config\.storage\$LocalDashboard") -RemotePath "$normalizedQnapPath/config/.storage/$QnapDashboard"

    Write-Host "[$($stepOffset + 8)/$totalSteps] Deploying config entries..." -ForegroundColor Yellow
    if (-not $DryRun -and -not $smBAvailable) {
        Invoke-RemoteCommand "rm -f '$normalizedQnapPath/config/.storage/core.config_entries' 2>/dev/null; true"
    }
    Copy-ToQnap -LocalPath (Join-Path $LocalRoot "config\.storage\core.config_entries") -RemotePath "$normalizedQnapPath/config/.storage/"

    Write-Host ""
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "Deployment completed!" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host ""
}
finally {
    if (-not $DryRun) {
        Write-Host "[$($stepOffset + 9)/$totalSteps] Starting Home Assistant container..." -ForegroundColor Yellow
        Invoke-RemoteCommand "cd '$normalizedQnapPath'; /share/CE_CACHEDEV1_DATA/.qpkg/container-station/bin/docker compose start homeassistant"
    }
    else {
        Write-Host "[10/9] Starting Home Assistant container..." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Check logs with:" -ForegroundColor Cyan
Write-Host ("ssh {0} 'cd {1}; docker compose logs -f homeassistant'" -f $target, $normalizedQnapPath) -ForegroundColor White
Write-Host ""
Write-Host ("Access Home Assistant at: http://{0}:8123" -f $QnapIP) -ForegroundColor Cyan
