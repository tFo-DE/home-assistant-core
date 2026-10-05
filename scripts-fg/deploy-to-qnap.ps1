# filepath: deploy-to-qnap.ps1
# Home Assistant QNAP Deployment Script
# Kopiert alle Custom Components und Konfigurationsdateien auf die QNAP
#
# Parameter:
#   -QnapIP: IP-Adresse der QNAP (default: 192.168.1.170)
#   -QnapUser: SSH Benutzername (default: fgAdmin)
#   -QnapPath: Pfad zum Home Assistant Verzeichnis auf QNAP (default: /share/dev-fg/home-assistant)
#   -LocalDashboard: Name des lokalen Dashboards in .storage/ (default: lovelace.lovelace)
#   -QnapDashboard: Name des QNAP Dashboards in .storage/ (default: lovelace.dashboard_bov)
#   -CleanupEntityRegistry: Bereinigt alte V1-Sensoren aus der Entity Registry vor dem Deployment
#
# Beispiel:
#   deploy-to-qnap.ps1
#   deploy-to-qnap.ps1 -QnapIP 192.168.1.170 -LocalDashboard lovelace.lovelace -QnapDashboard lovelace.dashboard_bov
#   deploy-to-qnap.ps1 -CleanupEntityRegistry  # Empfohlen beim ersten V2-Deployment!

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
    [string]$QnapDashboard = "lovelace.dashboard_bov",
    
    [Parameter(Mandatory=$false)]
    [switch]$CleanupEntityRegistry
)

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Home Assistant QNAP Deployment" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$totalSteps = if ($CleanupEntityRegistry) { 11 } else { 9 }

# 1. Container stoppen
Write-Host "[1/$totalSteps] Stopping Home Assistant container..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "cd $QnapPath && /share/CE_CACHEDEV1_DATA/.qpkg/container-station/bin/docker compose stop homeassistant"

# 1b. Entity Registry Cleanup (optional)
if ($CleanupEntityRegistry) {
    Write-Host "[2/$totalSteps] Uploading cleanup script..." -ForegroundColor Yellow
    scp -O cleanup-sungrow-v1-entities.sh "$QnapUser@${QnapIP}:$QnapPath/"
    
    Write-Host "[3/$totalSteps] Running entity registry cleanup..." -ForegroundColor Yellow
    ssh "$QnapUser@$QnapIP" "cd $QnapPath && chmod +x cleanup-sungrow-v1-entities.sh && ./cleanup-sungrow-v1-entities.sh"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Entity registry cleaned successfully" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Cleanup script had warnings (check output above)" -ForegroundColor Yellow
    }
    $stepOffset = 3
} else {
    $stepOffset = 1
}

# 2. Backup erstellen auf QNAP
Write-Host "[$($stepOffset + 1)/$totalSteps] Creating backup on QNAP..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "cd $QnapPath/config && tar -czf backup_`$(date +%Y%m%d_%H%M%S).tar.gz .storage/core.config_entries .storage/$QnapDashboard configuration.yaml templates.yaml --exclude='*.db*' --exclude='*.log*' 2>/dev/null || echo 'Backup completed'"

# 2b. Cleanup __pycache__ directories
Write-Host "[$($stepOffset + 2)/$totalSteps] Cleaning up __pycache__ directories..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "find $QnapPath/config/custom_components -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true"

# 3. Custom Components übertragen
Write-Host "[$($stepOffset + 3)/$totalSteps] Deploying pv_load_balancer..." -ForegroundColor Yellow
scp -O -r config/custom_components/pv_load_balancer "$QnapUser@${QnapIP}:$QnapPath/config/custom_components/"

Write-Host "[$($stepOffset + 4)/$totalSteps] Deploying oekofen_pellematic_compact..." -ForegroundColor Yellow
scp -O -r config/custom_components/oekofen_pellematic_compact "$QnapUser@${QnapIP}:$QnapPath/config/custom_components/"

Write-Host "[$($stepOffset + 5)/$totalSteps] Deploying alfen_modbus..." -ForegroundColor Yellow
scp -O -r config/custom_components/alfen_modbus "$QnapUser@${QnapIP}:$QnapPath/config/custom_components/"

# 4. Konfigurationsdateien übertragen
Write-Host "[$($stepOffset + 6)/$totalSteps] Deploying configuration files..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "rm -f $QnapPath/config/configuration.yaml $QnapPath/config/templates.yaml 2>/dev/null || true"
ssh "$QnapUser@$QnapIP" "mkdir -p $QnapPath/config/integrations 2>/dev/null || true"
scp -O config/configuration.yaml "$QnapUser@${QnapIP}:$QnapPath/config/"
scp -O config/templates.yaml "$QnapUser@${QnapIP}:$QnapPath/config/"
scp -O config/integrations/modbus_sungrow.yaml "$QnapUser@${QnapIP}:$QnapPath/config/integrations/"

Write-Host "[$($stepOffset + 7)/$totalSteps] Deploying dashboard..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "rm -f $QnapPath/config/.storage/$QnapDashboard 2>/dev/null || true"
scp -O "config/.storage/$LocalDashboard" "$QnapUser@${QnapIP}:$QnapPath/config/.storage/$QnapDashboard"

Write-Host "[$($stepOffset + 8)/$totalSteps] Deploying config entries..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "rm -f $QnapPath/config/.storage/core.config_entries 2>/dev/null || true"
scp -O core.config_entries "$QnapUser@${QnapIP}:$QnapPath/config/.storage/"

# 5. Container starten (Volume-Mounts übernehmen automatisch neue Dateien)
Write-Host "[$($stepOffset + 9)/$totalSteps] Starting Home Assistant container..." -ForegroundColor Yellow
ssh "$QnapUser@$QnapIP" "cd $QnapPath && /share/CE_CACHEDEV1_DATA/.qpkg/container-station/bin/docker compose start homeassistant"

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Check logs with:" -ForegroundColor Cyan
Write-Host "ssh $QnapUser@$QnapIP 'cd $QnapPath && docker compose logs -f homeassistant'" -ForegroundColor White
Write-Host ""
Write-Host "Access Home Assistant at: http://${QnapIP}:8123" -ForegroundColor Cyan