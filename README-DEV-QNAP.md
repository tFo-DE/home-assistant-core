# Home Assistant DEV/PROD Workflow (QNAP)

Dieses Repository ist die DEV-Umgebung, PROD bleibt auf `Q:\home-assistant`.

## Zielbild

- **DEV (Git, branch `main`)**: `C:\PythonCode\home-assistant`
- **PROD (laufende Instanz auf QNAP)**: `Q:\home-assistant`
- Änderungen werden in DEV entwickelt/testet und anschließend nach PROD deployt.

## Wichtige Skripte

- Sync von QNAP nach lokal: `.\scripts-fg\sync-from-qnap.ps1`
- Deploy nach QNAP: `.\scripts-fg\deploy-to-qnap.ps1`
- DEV/PROD-Vergleich: `.\scripts-fg\compare-prod-dev.ps1`
- Lokalen DEV-Container starten: `.\scripts-fg\start-local-container.ps1`

## Empfohlener Ablauf

1. **Aktuellen PROD-Stand holen**
   ```powershell
   .\scripts-fg\sync-from-qnap.ps1
   ```

2. **Unterschiede DEV vs PROD prüfen**
   ```powershell
   .\scripts-fg\compare-prod-dev.ps1
   ```
   Standardmäßig werden volatile Verzeichnisse ausgeschlossen (`.storage`, `__pycache__`, `deps`, `backups`, `tts`, `www`, `.cache`).

3. **Lokal testen**
   ```powershell
   .\scripts-fg\start-local-container.ps1 -PullImage
   ```
   Der Start nutzt `.env.fg-dev` (Default) und fährt einen lokalen PostgreSQL-18-Container für DEV hoch.
   Optional:
   ```powershell
   .\scripts-fg\start-local-container.ps1 -FollowLogs
   ```

4. **Deploy nach QNAP**
   ```powershell
   .\scripts-fg\deploy-to-qnap.ps1
   ```

5. **Nach Deploy prüfen**
   ```powershell
   ssh fgAdmin@192.168.1.170 "cd /share/dev-fg/home-assistant && /share/CE_CACHEDEV1_DATA/.qpkg/container-station/bin/docker compose logs -f homeassistant"
   ```

## Branching/Sync-Strategie

- `main` ist der zukünftige Arbeitsbranch in diesem Repo.
- Feature-Änderungen bei Bedarf in kurzen Topic-Branches entwickeln und per PR nach `main` mergen.
- `Q:\home-assistant` bleibt die Laufzeitumgebung (PROD), nicht der Ort für Entwicklung.

## Hinweise

- `config` ist teilweise versioniert: eigener Code in `config/custom_components`, `config/integrations` sowie ausgewählte YAML-Dateien (`configuration.yaml`, `automations.yaml`, `scenes.yaml`, `scripts.yaml`, `templates.yaml`).
- Secrets bleiben in lokalen/produktiven Konfigurationsdateien und werden nicht nach Git committed.
