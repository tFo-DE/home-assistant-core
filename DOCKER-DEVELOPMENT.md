# Home Assistant Docker Development Setup

## 🐳 Quick Start

### 1. Docker Container bauen und starten
```powershell
# Image bauen
docker compose build homeassistant

# Container starten
docker compose up -d homeassistant

# Logs verfolgen
docker compose logs -f homeassistant
```

### 2. Debuggen mit VS Code

**In config/configuration.yaml:**
```yaml
# Debugpy für Remote Debugging aktivieren
debugpy:
  start: true
  wait: false
  port: 5678
```

**In VS Code:**
1. Container starten: `docker-compose up -d`
2. Warte bis HA gestartet ist (~30 Sekunden)
3. In VS Code: `F5` → "Home Assistant: Attach Docker"
4. Setze Breakpoints in deinem Custom Component Code
5. Trigger die Funktion in HA (z.B. über UI oder Automatisierung)

### 3. Custom Components testen

Die Custom Components in `config/custom_components/` werden automatisch geladen:
- `oekofen_pellematic_compact` - Ökofen Heizung Integration (✅ aktualisiert für HA 2026.x)
- `pv_load_balancer` - PV-Überschussladung für Wallbox (✅ neu erstellt)
- `alfen_modbus` - Alfen Eve Double Wallbox (✅ von GitHub installiert)
- ~~`sunny_balance_loader`~~ - Deprecated, ersetzt durch `pv_load_balancer`

**Nach Code-Änderungen:**
```powershell
# Container neu starten
docker compose restart homeassistant

# Oder nur HA Core neu laden (schneller)
docker exec homeassistant-dev ha core restart
```

### 4. Tests ausführen

**Im Container:**
```powershell
# Shell im Container öffnen
docker exec -it homeassistant-dev /bin/bash

# Tests für eine Integration ausführen
uv run pytest tests/components/oekofen_pellematic_compact/ -v

# Mit Coverage
uv run pytest tests/components/oekofen_pellematic_compact/ --cov=homeassistant.components.oekofen_pellematic_compact --cov-report term-missing
```

**Über VS Code Tasks:**
- `Ctrl+Shift+P` → "Tasks: Run Task"
- Wähle "Docker: Run Tests in Container"

## 📋 Nützliche Commands

```powershell
# Container Status
docker compose ps

# Logs ansehen
docker compose logs -f homeassistant

# Logs auf Fehler prüfen (Windows PowerShell)
docker compose logs homeassistant | Select-String -Pattern "error" -CaseSensitive:$false

# In Container einloggen
docker exec -it homeassistant-dev /bin/bash

# Container stoppen
docker compose down

# Container und Volumes löschen (Clean Start)
docker compose down -v
```

## 🔧 VS Code Tasks

Verfügbare Tasks (zugänglich über `Ctrl+Shift+P` → "Tasks: Run Task"):

- **Docker: Build Dev Image** - Baut das Development Image neu
- **Docker: Start HA Container** - Startet den Container
- **Docker: Stop HA Container** - Stoppt den Container
- **Docker: Restart HA Container** - Neustart des Containers
- **Docker: View Logs** - Zeigt Container Logs
- **Docker: Shell into Container** - Öffnet eine Shell im Container
- **Docker: Run Tests in Container** - Führt Tests aus
- **Docker: Compile Translations** - Kompiliert Übersetzungen

## 🐛 Debugging Setup

### Remote Debugging aktivieren

1. **In `config/configuration.yaml`:**
```yaml
debugpy:
  start: true
  wait: false
  port: 5678
```

2. **Container neu starten:**
```powershell
docker compose restart homeassistant
```

3. **In VS Code debuggen:**
   - Drücke `F5`
   - Wähle "Home Assistant: Attach Docker"
   - Breakpoints werden jetzt getroffen

### Custom Component Debug Workflow

1. Setze Breakpoint in deinem Custom Component (z.B. `config/custom_components/oekofen_pellematic_compact/sensor.py`)
2. Starte Debugging (`F5` → "Home Assistant: Attach Docker")
3. Triggere die Funktion in Home Assistant (z.B. Integration setup, Sensor update)
4. VS Code stoppt am Breakpoint

## 🚀 Deployment zu QNAP

Nach erfolgreichem Testing im lokalen Container:

1. **Code committen:**
```powershell
git add .
git commit -m "Update custom components for HA 2026.x"
git push
```

2. **Auf QNAP:**
```bash
# Repository aktualisieren
cd /path/to/home-assistant-core
git pull origin v2

# Container neu bauen
docker-compose build homeassistant
docker-compose up -d homeassistant
```

## 📝 Troubleshooting

### Container startet nicht
```powershell
# Logs prüfen
docker compose logs homeassistant

# Fehler filtern (PowerShell)
docker compose logs homeassistant | Select-String "error|ERROR|Error"

# Container Status
docker ps -a

# Clean restart
docker compose down -v
docker compose up --build
```

### Debugger verbindet nicht
1. Prüfe ob Port 5678 offen ist: `netstat -an | findstr 5678`
2. Stelle sicher dass `debugpy` in configuration.yaml aktiviert ist
3. Warte ~30 Sekunden nach Container-Start bevor du anhängst

### Custom Component wird nicht geladen
1. Prüfe manifest.json auf Syntax-Fehler
2. Logs prüfen: `docker compose logs homeassistant | Select-String "custom_components"`
3. Container neu starten: `docker compose restart homeassistant`

## 🔗 Weiterführende Links

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Integration Quality Scale](https://developers.home-assistant.io/docs/integration_quality_scale_index/)
- [debugpy Integration](https://www.home-assistant.io/integrations/debugpy/)
