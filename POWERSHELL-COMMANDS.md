# PowerShell Commands Cheat Sheet für Home Assistant Development

## Docker Commands (Windows PowerShell)

### Container Management
```powershell
# Container bauen
docker compose build homeassistant

# Container starten
docker compose up -d homeassistant

# Container stoppen
docker compose down

# Container neu starten
docker compose restart homeassistant

# Container Status
docker compose ps

# In Container einloggen
docker exec -it homeassistant-dev /bin/bash
```

### Logs & Debugging

```powershell
# Logs ansehen (live)
docker compose logs -f homeassistant

# Logs auf Fehler prüfen
docker compose logs homeassistant | Select-String -Pattern "error" -CaseSensitive:$false

# Nur ERROR Level
docker compose logs homeassistant | Select-String "ERROR"

# Mehrere Patterns
docker compose logs homeassistant | Select-String "error|ERROR|Error|warning|WARNING"

# Mit Kontext (Zeilen vor/nach Match)
docker compose logs homeassistant | Select-String "error" -Context 2,2

# Logs in Datei speichern
docker compose logs homeassistant > logs_$(Get-Date -Format "yyyyMMdd_HHmmss").txt

# Custom Components filtern
docker compose logs homeassistant | Select-String "custom_components"

# Letzte 100 Zeilen
docker compose logs --tail=100 homeassistant
```

### Container Informationen

```powershell
# Alle Container
docker ps -a

# Ressourcen-Nutzung (CPU, RAM)
docker stats homeassistant-dev

# Container Details
docker inspect homeassistant-dev

# Container IP Adresse
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' homeassistant-dev
```

## Home Assistant Commands (im Container)

```powershell
# HA Core neu laden
docker exec homeassistant-dev ha core restart

# HA Version
docker exec homeassistant-dev ha core info

# Integration neu laden
docker exec homeassistant-dev ha integration reload oekofen_pellematic_compact

# Config prüfen
docker exec homeassistant-dev ha core check
```

## Git Commands

```powershell
# Status prüfen
git status

# Branch wechseln
git checkout v2

# Änderungen hinzufügen
git add .

# Commit
git commit -m "Your message"

# Push
git push origin v2

# Pull
git pull origin v2

# Letzten Commit ansehen
git log -1

# Änderungen seit letztem Commit
git diff
```

## Nützliche PowerShell Befehle

### Dateien & Ordner

```powershell
# Datei suchen
Get-ChildItem -Path . -Recurse -Filter "manifest.json"

# Inhalt durchsuchen (wie grep)
Get-ChildItem -Recurse -Include *.py | Select-String "async_setup_entry"

# Große Dateien finden
Get-ChildItem -Recurse | Where-Object {$_.Length -gt 1MB} | Sort-Object Length -Descending

# Ordnergröße
(Get-ChildItem -Path . -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
```

### Ports & Netzwerk

```powershell
# Port prüfen (ob belegt)
Test-NetConnection -ComputerName localhost -Port 8123

# Alle offenen Ports
Get-NetTCPConnection | Where-Object {$_.State -eq "Listen"}

# Port 5678 (debugpy) prüfen
Get-NetTCPConnection -LocalPort 5678 -ErrorAction SilentlyContinue

# HTTP Request
Invoke-WebRequest -Uri http://localhost:8123 -Method Get
```

### Prozesse

```powershell
# Prozesse nach Name suchen
Get-Process | Where-Object {$_.Name -like "*docker*"}

# Prozess beenden
Stop-Process -Name "process_name" -Force

# CPU/RAM Nutzung
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
```

## Aliases (Abkürzungen)

```powershell
# Select-String
sls "pattern" file.txt

# Get-ChildItem
gci -Recurse

# Where-Object
? {$_.Name -like "*test*"}

# Select-Object
select Name, Size
```

## Häufige Workflows

### Nach Fehler suchen und Kontext sehen

```powershell
docker compose logs homeassistant | Select-String "error" -Context 5,5 | Out-File errors_with_context.txt
notepad errors_with_context.txt
```

### Custom Component Logs extrahieren

```powershell
docker compose logs homeassistant | Select-String "pv_load_balancer|oekofen|alfen_modbus" > custom_components.log
```

### Performance überwachen

```powershell
# Endlos-Loop für Monitoring
while ($true) {
    Clear-Host
    docker stats --no-stream homeassistant-dev
    Start-Sleep -Seconds 5
}
```

### Clean Restart

```powershell
docker compose down -v
docker compose build --no-cache homeassistant
docker compose up -d homeassistant
docker compose logs -f homeassistant
```

## Unterschiede zu Linux/Bash

| Linux/Bash | PowerShell | Beschreibung |
|------------|------------|--------------|
| `grep` | `Select-String` oder `sls` | Text suchen |
| `grep -i` | `Select-String -CaseSensitive:$false` | Case-insensitive |
| `cat` | `Get-Content` oder `gc` | Datei anzeigen |
| `ls -la` | `Get-ChildItem` oder `gci` | Verzeichnis auflisten |
| `ps` | `Get-Process` | Prozesse anzeigen |
| `kill` | `Stop-Process` | Prozess beenden |
| `tail -f` | `Get-Content -Wait -Tail 10` | Datei live verfolgen |
| `find` | `Get-ChildItem -Recurse` | Dateien finden |
| `which` | `Get-Command` | Befehl finden |

## Tipps & Tricks

### Tab-Completion nutzen
```powershell
# Tippe Anfang und drücke Tab für Auto-Complete
docker comp<TAB>  # → docker compose
docker compose lo<TAB>  # → docker compose logs
```

### Pipeline nutzen (wie | in Linux)
```powershell
# Mehrere Befehle verketten
docker compose logs homeassistant | 
  Select-String "error" | 
  Select-Object -First 5 |
  Out-File top5_errors.txt
```

### Ausgabe formatieren
```powershell
# Als Tabelle
Get-Process | Format-Table Name, CPU, Memory

# Als Liste
docker ps | Format-List
```

### Profile anlegen (Befehle beim Start ausführen)
```powershell
# Profile bearbeiten
notepad $PROFILE

# Beispiel Inhalt für schnellere HA Development:
function ha-logs { docker compose logs -f homeassistant }
function ha-restart { docker compose restart homeassistant }
function ha-errors { docker compose logs homeassistant | Select-String "error|ERROR" }
```

Dann kannst du einfach `ha-logs` tippen statt den kompletten Befehl! 🚀
