# Home Assistant QNAP Reverse Sync Script
# Synchronisiert Konfigurationsdateien von QNAP nach lokal
#
# Parameter:
#   -QnapIP: IP-Adresse der QNAP (default: 192.168.1.170)
#   -QnapUser: SSH Benutzername (default: fgAdmin)
#   -QnapPath: Pfad zum Home Assistant Verzeichnis auf QNAP (default: /share/dev-fg/home-assistant)
#   -LocalDashboard: Name des lokalen Dashboards in .storage/ (default: lovelace.lovelace)
#   -QnapDashboard: Name des QNAP Dashboards in .storage/ (default: lovelace.dashboard_bov)
#
# Beispiel:
#   .\sync-from-qnap.ps1

param(
    [Parameter(Mandatory=$false)]
    [string]$QnapIP = "192.168.1.170",
    
    [Parameter(Mandatory=$false)]
    [string]$QnapUser = "fgAdmin",
    
    [Parameter(Mandatory=$false)]
    [string]$QnapPath = "/share/dev-fg/home-assistant",
    
    [Parameter(Mandatory=$false)]
    [string]$LocalDashboard = "lovelace.lovelace",
    
    [Parameter(Mandatory=$false)]
    [string]$QnapDashboard = "lovelace.dashboard_bov"
)

$DockerCmd = "/share/CE_CACHEDEV1_DATA/.qpkg/container-station/bin/docker"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "QNAP -> Local Synchronization" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 1. Backup lokal erstellen
Write-Host "[1/6] Creating local backup..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "config_backup_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item config/configuration.yaml "$backupDir/" -ErrorAction SilentlyContinue
Copy-Item config/templates.yaml "$backupDir/" -ErrorAction SilentlyContinue
Copy-Item "config/.storage/$LocalDashboard" "$backupDir/" -ErrorAction SilentlyContinue
Copy-Item config/.storage/core.config_entries "$backupDir/" -ErrorAction SilentlyContinue
Write-Host "  Backup created: $backupDir" -ForegroundColor Green

# 2. templates.yaml synchronisieren
Write-Host "[2/6] Syncing templates.yaml..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "$DockerCmd exec homeassistant cat /config/templates.yaml" | Set-Content -Path config/templates.yaml -Encoding UTF8NoBOM

# 3. configuration.yaml synchronisieren
Write-Host "[3/6] Syncing configuration.yaml..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "$DockerCmd exec homeassistant cat /config/configuration.yaml" | Set-Content -Path config/configuration.yaml -Encoding UTF8NoBOM

# 4. Dashboard synchronisieren
Write-Host "[4/6] Syncing dashboard ($QnapDashboard -> $LocalDashboard)..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "$DockerCmd exec homeassistant cat /config/.storage/$QnapDashboard" | Set-Content -Path "config/.storage/$LocalDashboard" -Encoding UTF8NoBOM

# 5. Config Entries synchronisieren
Write-Host "[5/5] Syncing config entries..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "$DockerCmd exec homeassistant cat /config/.storage/core.config_entries" | Set-Content -Path config/.storage/core.config_entries -Encoding UTF8NoBOM

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "Synchronization completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Local backup created in: $backupDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "To test locally:" -ForegroundColor Cyan
Write-Host "  docker compose restart homeassistant" -ForegroundColor White
Write-Host "  Access at: http://localhost:8123" -ForegroundColor White
