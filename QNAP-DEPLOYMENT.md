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

### 1. SSH in QNAP einloggen
```bash
ssh admin@<QNAP-IP>
```

### 2. Repository aktualisieren
```bash
# Zum Repository navigieren
cd /share/Container/home-assistant-core  # ← Pfad anpassen!

# Aktuellen Branch prüfen
git branch

# Falls nicht auf v2:
git checkout v2

# Repository pullen
git pull origin v2
```

### 3. Backup erstellen (WICHTIG!)
```bash
# Home Assistant Backup über UI erstellen (Einstellungen → System → Backups)
# ODER via CLI:
cd /share/Container/home-assistant-core/config
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz . --exclude='*.db-*' --exclude='*.log*'
```

### 4. Container aktualisieren
```bash
# Container stoppen
docker-compose down

# Neues Image bauen (dauert ~10-15 Min)
docker-compose build homeassistant

# Container starten
docker-compose up -d homeassistant

# Logs verfolgen
docker-compose logs -f homeassistant
```

### 5. Deployment verifizieren
```bash
# Container Status prüfen
docker ps | grep homeassistant

# Logs auf Fehler prüfen (Linux)
docker-compose logs homeassistant | grep -i error

# Home Assistant Version prüfen
docker exec homeassistant-dev ha core info
```

### 6. UI Testing
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
