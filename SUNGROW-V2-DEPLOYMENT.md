# Sungrow V2 Deployment auf QNAP

## Was wurde geändert?

1. **Sungrow Integration V2** (mkaiser 2026-04-27)
   - 150+ neue Sensoren
   - EMS-Steuerung (Battery SoC, Export Limit)
   - Meter-Sensoren für SH10RT-V112 deaktiviert (Register 5740-5745)

2. **Template-Sensoren** in `templates.yaml`:
   - `sensor.export_power` - Positive Werte wenn Export
   - `sensor.import_power` - Positive Werte wenn Import
   - Basis: `sensor.export_power_raw` (Register 13009/13010)

3. **Dashboard** aktualisiert mit allen V2-Sensoren

## Deployment-Optionen

### Option 1: Normales Deployment (wenn QNAP bereits V2 hat)

```powershell
.\deploy-to-qnap.ps1 -QnapIP 192.168.1.170
```

**Deploy folgende Dateien:**
- Custom Components (pv_load_balancer, oekofen_pellematic_compact, alfen_modbus)
- config/configuration.yaml
- config/templates.yaml
- config/integrations/modbus_sungrow.yaml
- config/.storage/lovelace.dashboard_bov (Dashboard)

### Option 2: Deployment mit Entity Registry Cleanup (empfohlen beim ersten V2-Update!)

```powershell
.\deploy-to-qnap.ps1 -QnapIP 192.168.1.170 -CleanupEntityRegistry
```

**Zusätzlich wird ausgeführt:**
- Löscht alte V1-Sensoren aus Entity Registry:
  - `sensor.export_power_raw` (alte unique_id: `sg_export_power_raw`)
  - `sensor.export_power_raw_60s_avg` (sunny_balance_loader)
  - Alte Template-Sensoren aus Modbus-YAML

**Verhindert:**
- Sensor-Umbenennungen (`sensor.export_power_raw_2` statt `sensor.export_power_raw`)
- Template-Fehler wegen duplicate unique_ids

## Warum ist Cleanup wichtig?

**Ohne Cleanup:**
```
sensor.export_power_raw       → alte V1 Entity (sg_export_power_raw)
sensor.export_power_raw_2     → neue V2 Entity (sg_battery_export_power_raw)  ❌ FALSCH
```

**Mit Cleanup:**
```
sensor.export_power_raw       → neue V2 Entity (sg_battery_export_power_raw)  ✅ KORREKT
```

Die Template-Sensoren `sensor.export_power` und `sensor.import_power` erwarten:
```yaml
availability: "{{ states('sensor.export_power_raw') | is_number }}"
```

Wenn der Sensor `sensor.export_power_raw_2` heißt → Templates funktionieren nicht!

## Nach dem Deployment prüfen

1. **Sensoren vorhanden:**
   ```
   Entwicklerwerkzeuge → Zustände
   - sensor.export_power_raw  ✓
   - sensor.export_power      ✓
   - sensor.import_power      ✓
   - sensor.load_power        ✓
   ```

2. **Keine Modbus-Fehler:**
   ```powershell
   ssh fgAdmin@192.168.1.170 'cd /share/dev-fg/home-assistant && docker compose logs -f homeassistant | grep ERROR'
   ```
   
   Nur erwartete Fehler (harmlos):
   - Version 2/3/4 firmware strings (Register 2596, 2612, 2628)

3. **pv_load_balancer funktioniert:**
   ```
   Entwicklerwerkzeuge → Zustände
   - sensor.pv_load_balancer_export_power  → zeigt 60s Durchschnitt
   ```

## Rollback (falls nötig)

Falls nach Deployment Probleme auftreten:

1. **Backup wiederherstellen:**
   ```bash
   ssh fgAdmin@192.168.1.170
   cd /share/dev-fg/home-assistant/config
   tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz
   cd /share/dev-fg/home-assistant
   docker compose restart homeassistant
   ```

2. **Entity Registry Backup:**
   ```bash
   # Cleanup-Skript erstellt automatisch:
   /config/.storage/core.entity_registry.backup-YYYYMMDD-HHMMSS
   ```

## Lokale Tests vor QNAP-Deployment

```powershell
# Container lokal starten (Sungrow nicht erreichbar → einige Modbus-Fehler normal)
docker compose up -d

# Template-Sensoren prüfen
docker logs homeassistant-dev 2>&1 | Select-String -Pattern "ERROR.*template"

# Entity Registry prüfen
Get-Content config\.storage\core.entity_registry -Raw | ConvertFrom-Json | 
  Select-Object -ExpandProperty data | Select-Object -ExpandProperty entities | 
  Where-Object { $_.entity_id -match 'export_power|import_power' } | 
  Select-Object entity_id,unique_id,platform | Format-Table -AutoSize
```

## Wichtige Hinweise

⚠️ **Nachts/kein PV:** Register 13010 (Export power raw) gibt `0x7FFFFFFF` (NaN) zurück → Modbus ERROR ist normal!

⚠️ **SH10RT-V112 vs SH10RS:** Meter-Sensoren (5740-5745) sind nur für SH10RS → bei SH10RT deaktiviert!

✅ **pv_load_balancer:** Nutzt bereits 60s-Durchschnitte → kein Code-Update nötig!

✅ **Dashboard:** Alle nicht-unterstützten Sensoren entfernt, nur funktionierende V2-Sensoren!
