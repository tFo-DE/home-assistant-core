# Home Assistant DEV/PROD Workflow (QNAP)

Dieses Repository ist die DEV-Umgebung, PROD bleibt auf `Q:\home-assistant`.

## Zielbild

- **DEV (Git, branch `main`)**: `C:\PythonCode\home-assistant`
- **PROD (laufende Instanz auf QNAP)**: `Q:\home-assistant`
- Änderungen werden in DEV entwickelt/testet und anschließend nach PROD deployt.

## Wichtige Skripte

- Deploy nach QNAP: `.\deploy-to-qnap.ps1`
- Sync von QNAP nach lokal: `.\sync-from-qnap.ps1`
- DEV/PROD-Vergleich: `.\compare-prod-dev.ps1`
- Lokalen DEV-Container starten: `.\start-local-container.ps1`

## Empfohlener Ablauf

1. **Aktuellen PROD-Stand holen**
   ```powershell
   .\sync-from-qnap.ps1
   ```

2. **Unterschiede DEV vs PROD prüfen**
   ```powershell
   .\compare-prod-dev.ps1
   ```
   Standardmäßig werden volatile Verzeichnisse ausgeschlossen (`.storage`, `__pycache__`, `deps`, `backups`, `tts`, `www`, `.cache`).

3. **Lokal testen**
   ```powershell
   .\start-local-container.ps1 -PullImage
   ```
   Optional:
   ```powershell
   .\start-local-container.ps1 -FollowLogs
   ```

4. **Deploy nach QNAP**
   ```powershell
   .\deploy-to-qnap.ps1
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

- Das Verzeichnis `config` ist in `.gitignore` enthalten und wird nicht versioniert.
- Secrets bleiben in lokalen/produktiven Konfigurationsdateien und werden nicht nach Git committed.
