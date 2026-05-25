# QNAP Deployment Checklist

## Pre-Deployment (Lokal getestet ✅)

### 1. Custom Components Status
- [x] `oekofen_pellematic_compact` - Modernisiert für HA 2026.x
- [x] `pv_load_balancer` - Neu erstellt, ersetzt sunny_balance_loader
- [x] `alfen_modbus` - Von GitHub installiert (ThaStealth/alfen_modbus)
- [x] ~~`sunny_balance_loader`~~ - Deaktiviert und deprecated
- [x] Linting geprüft: `uv run prek run --all-files`
- [x] Dashboard aktualisiert (alle Entity IDs)

### 2. Docker Build lokal getestet ✅
```powershell
# Image gebaut und getestet
docker compose build homeassistant
docker compose up -d
docker compose logs -f homeassistant
```

### 3. Funktionalität getestet ✅
- [x] Home Assistant UI erreichbar unter http://localhost:8123
- [x] `oekofen_pellematic_compact` lädt korrekt
- [x] `pv_load_balancer` Config Entry lädt
- [x] `alfen_modbus` Integration funktioniert
- [x] Sensoren erscheinen im Dashboard
- [x] Keine Fehler in Logs
- [x] Debugging funktioniert (F5 → "Home Assistant: Attach Docker")

### 4. Debug-Konfiguration für Produktion vorbereiten
```yaml
# config/configuration.yaml
# Für lokales Docker Development:
debugpy:
  start: true   # ← Auf QNAP: false oder auskommentieren
  wait: false
  port: 5678
```

**WICHTIG für QNAP:** debugpy deaktivieren oder Port ändern!

### 5. Git Commit & Push
```powershell
git add .
git commit -m "Update to HA 2026.x: Add pv_load_balancer, modernize oekofen, add alfen_modbus"
git push origin v2
```

---

## Deployment auf QNAP

> **Hinweis:** Da Git auf der QNAP nicht installiert ist, nutzen wir **SCP (Secure Copy)** zum Übertragen der Dateien.

### Methode 1: Automatisches Deployment-Script (Empfohlen) ⚡

**Von Windows PowerShell aus:**

```powershell
# Script ausführen (ersetzt <QNAP-IP> mit deiner IP)
.\deploy-to-qnap.ps1 -QnapIP <QNAP-IP>

# Beispiel:
.\deploy-to-qnap.ps1 -QnapIP 192.168.1.170

# Mit anderem User:
.\deploy-to-qnap.ps1 -QnapIP 192.168.1.170 -QnapUser admin

# Mit anderem Pfad:
.\deploy-to-qnap.ps1 -QnapIP 192.168.1.170 -QnapPath /share/Container/ha

# Mit anderen Dashboard-Namen:
.\deploy-to-qnap.ps1 -LocalDashboard lovelace.lovelace -QnapDashboard lovelace.dashboard_bov
```

**Das Script macht automatisch:**
1. ✅ Backup auf QNAP erstellen (inkl. templates.yaml)
2. ✅ Custom Components übertragen (pv_load_balancer, oekofen, alfen_modbus)
3. ✅ Konfigurationsdateien übertragen (configuration.yaml, templates.yaml)
4. ✅ Dashboard übertragen (mit flexiblen Namen)
5. ✅ Config Entries übertragen
6. ✅ Container neu starten
7. ✅ Status-Meldungen anzeigen

**Script-Parameter:**
- `-QnapIP`: IP-Adresse der QNAP (default: 192.168.1.170)
- `-QnapUser`: SSH Benutzername (default: fgAdmin)
- `-QnapPath`: Pfad zum HA Verzeichnis (default: /share/dev-fg/home-assistant)
- `-LocalDashboard`: Lokaler Dashboard-Name (default: lovelace.lovelace)
- `-QnapDashboard`: QNAP Dashboard-Name (default: lovelace.dashboard_bov)

---

### Methode 2: Reverse Sync (QNAP → Lokal) 🔄

**Wann verwenden:**
- Nach manuellen Änderungen direkt auf QNAP
- Um lokale Dev-Umgebung mit QNAP zu synchronisieren
- Zum Testen von QNAP-Konfigurationen lokal

**Von Windows PowerShell aus:**

```powershell
# Automatisches Reverse Sync Script
.\sync-from-qnap.ps1 -QnapIP 192.168.1.170

# Mit anderen Dashboard-Namen:
.\sync-from-qnap.ps1 -LocalDashboard lovelace.lovelace -QnapDashboard lovelace.dashboard_bov
```

**Das Script macht automatisch:**
1. ✅ Lokales Backup erstellen (im Verzeichnis `config_backup_TIMESTAMP/`)
2. ✅ templates.yaml von QNAP holen
3. ✅ configuration.yaml von QNAP holen
4. ✅ Dashboard von QNAP holen (z.B. dashboard_bov → lovelace.lovelace)
5. ✅ Config Entries von QNAP holen
6. ✅ Veraltete Dateien aufräumen (sunny_balance_loader, etc.)

**Nach dem Sync lokal testen:**
```powershell
# Container neu starten
docker compose restart homeassistant

# Logs prüfen
docker compose logs -f homeassistant

# UI öffnen
Start-Process "http://localhost:8123"
```

---

### Methode 3: Manuelles Deployment via SCP

**1. Backup erstellen (WICHTIG!)**

```powershell
# Von Windows aus: Backup auf QNAP erstellen
ssh fgAdmin@<QNAP-IP> "cd /share/dev-fg/home-assistant/config && tar -czf backup_`$(date +%Y%m%d_%H%M%S).tar.gz .storage/core.config_entries .storage/lovelace.dashboard_bov configuration.yaml templates.yaml"
```

**2. Custom Components übertragen (von Windows aus)**

```powershell
# pv_load_balancer
scp -O -r config/custom_components/pv_load_balancer fgAdmin@<QNAP-IP>:/share/dev-fg/home-assistant/config/custom_components/

# oekofen_pellematic_compact
scp -O -r config/custom_components/oekofen_pellematic_compact fgAdmin@<QNAP-IP>:/share/dev-fg/home-assistant/config/custom_components/

# alfen_modbus
scp -O -r config/custom_components/alfen_modbus fgAdmin@<QNAP-IP>:/share/dev-fg/home-assistant/config/custom_components/
```

**3. Konfigurationsdateien übertragen**

```powershell
# Configuration.yaml
scp -O config/configuration.yaml fgAdmin@<QNAP-IP>:/share/dev-fg/home-assistant/config/

# Templates.yaml (NEU!)
scp -O config/templates.yaml fgAdmin@<QNAP-IP>:/share/dev-fg/home-assistant/config/

# Dashboard (beachte: QNAP verwendet dashboard_bov, lokal lovelace.lovelace)
scp -O config/.storage/lovelace.lovelace fgAdmin@<QNAP-IP>:/share/dev-fg/home-assistant/config/.storage/lovelace.dashboard_bov

# Config Entries (Integration Konfiguration)
scp -O config/.storage/core.config_entries fgAdmin@<QNAP-IP>:/share/dev-fg/home-assistant/config/.storage/
```

**4. Container neu starten**

```bash
# SSH zur QNAP
ssh fgAdmin@<QNAP-IP>

# Container neu starten
cd /share/dev-fg/home-assistant
/share/CE_CACHEDEV1_DATA/.qpkg/container-station/bin/docker restart homeassistant

# Logs verfolgen
/share/CE_CACHEDEV1_DATA/.qpkg/container-station/bin/docker logs -f homeassistant
```

---

### Deployment verifizieren

```bash
# SSH zur QNAP (falls nicht mehr verbunden)
ssh fgAdmin@<QNAP-IP>

# Container Status prüfen
docker ps | grep homeassistant

# Logs auf Fehler prüfen (Linux)
docker compose logs homeassistant | grep -i error

# Home Assistant Version prüfen
docker exec homeassistant ha core info
```

### UI Testing
- [ ] Home Assistant UI erreichbar: http://<QNAP-IP>:8123
- [ ] Alle Integrationen laden korrekt
- [ ] Custom Components funktionieren:
  - [ ] Ökofen Sensoren aktualisieren sich
  - [ ] PV Load Balancer funktioniert (ersetzt Sunny Balance Loader)
  - [ ] Alfen Modbus Sensoren aktualisieren sich
- [ ] Automationen laufen
- [ ] Dashboard "Overview" zeigt alle Sensoren korrekt
- [ ] Hardware-Verbindungen:
  - [ ] Sungrow SH10RT (192.168.1.155:502)
  - [ ] Alfen Eve Double (192.168.1.151:502)

---

## Rollback-Plan (Falls Probleme auftreten)

### Option 1: Zum vorherigen Commit zurück
```bash
cd /share/Container/home-assistant-core

# Letzten funktionierenden Commit finden
git log --oneline -10

# Zurücksetzen (ersetze <commit-hash>)
git reset --hard <commit-hash>

# Container neu bauen
docker-compose down
docker-compose build homeassistant
docker-compose up -d
```

### Option 2: Altes Image wiederherstellen
```bash
# Alte Images anzeigen
docker images | grep homeassistant

# Altes Image taggen und verwenden
docker tag homeassistant-dev:<old-tag> homeassistant-dev:latest
docker-compose up -d
```

### Option 3: Backup wiederherstellen
```bash
# Home Assistant Backup über UI wiederherstellen
# Einstellungen → System → Backups → Backup auswählen → Wiederherstellen
```

---

## Monitoring nach Deployment

### Erste 24 Stunden überwachen
```bash
# Logs kontinuierlich beobachten
docker-compose logs -f homeassistant | tee -a deployment_$(date +%Y%m%d).log

# Speichernutzung prüfen
docker stats homeassistant-dev

# Restart-Count prüfen (sollte bei 0 bleiben)
docker ps -a | grep homeassistant
```

### Performance-Metriken
- [ ] CPU-Auslastung < 50% im Idle
- [ ] RAM-Nutzung stabil
- [ ] Keine Memory Leaks (RAM steigt nicht kontinuierlich)
- [ ] Response-Zeiten UI < 2 Sekunden

### Funktions-Tests
- [ ] Ökofen Sensoren aktualisieren sich alle X Sekunden
- [ ] PV Load Balancer steuert Wallbox korrekt
  - [ ] Ladestrom wird angepasst (6-16A)
  - [ ] Phasenumschaltung funktioniert (1/3 Phasen)
  - [ ] Batterie SOC wird berücksichtigt
- [ ] Alfen Modbus Sensoren zeigen korrekte Werte
- [ ] Alle Automationen funktionieren
- [ ] Mobile App verbindet sich

---

## Troubleshooting

### Container startet nicht
```bash
# Detaillierte Logs
docker-compose logs --tail=100 homeassistant

# Container interaktiv starten für Debugging
docker-compose run --rm homeassistant /bin/bash
```

### Custom Component Fehler
```bash
# Logs filtern
docker-compose logs homeassistant | grep "custom_components"

# Integration neu laden (ohne Neustart)
docker exec homeassistant-dev ha integration reload oekofen_pellematic_compact
```

### Permission-Probleme
```bash
# Ownership prüfen und korrigieren
ls -la /share/Container/home-assistant-core/config
chown -R <user>:<group> /share/Container/home-assistant-core/config
```

### Netzwerk-Probleme
```bash
# Port-Bindings prüfen
netstat -tulpn | grep 8123

# Container Network prüfen
docker network inspect bridge
```

---

## Post-Deployment Checklist

- [ ] Deployment-Zeitpunkt dokumentiert
- [ ] Git-Commit-Hash notiert
- [ ] Backup verifiziert
- [ ] Monitoring für 24h aktiv
- [ ] Alle Funktionen getestet
- [ ] Dokumentation aktualisiert
- [ ] Rollback-Plan bereit

---

## Kontakte & Ressourcen

- **Home Assistant Logs:** http://<QNAP-IP>:8123/config/logs
- **System Info:** http://<QNAP-IP>:8123/config/info
- **QNAP Container Station:** http://<QNAP-IP>:8080
- **Dokumentation:** /share/Container/home-assistant-core/DOCKER-DEVELOPMENT.md

---

## Automatisiertes Deployment (Optional)

Für zukünftige Deployments kannst du ein Script erstellen:

```bash
#!/bin/bash
# deploy.sh

set -e  # Exit on error

echo "🚀 Starting Home Assistant Deployment..."

# Backup
echo "📦 Creating backup..."
cd /share/Container/home-assistant-core/config
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz . --exclude='*.db-*' --exclude='*.log*'

# Update
echo "📥 Pulling latest changes..."
cd /share/Container/home-assistant-core
git pull origin v2

# Build & Deploy
echo "🐳 Building and deploying container..."
docker-compose down
docker-compose build homeassistant
docker-compose up -d homeassistant

# Verify
echo "✅ Verifying deployment..."
sleep 10
docker ps | grep homeassistant || (echo "❌ Container not running!" && exit 1)

echo "✨ Deployment complete!"
echo "📊 Monitor logs: docker-compose logs -f homeassistant"
```

Verwendung:
```bash
chmod +x deploy.sh
./deploy.sh
```
