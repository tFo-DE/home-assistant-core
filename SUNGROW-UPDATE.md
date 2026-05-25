# Sungrow Integration V2 Update - Zusammenfassung

## ✅ Was wurde gemacht

### 1. Sungrow Modbus Integration aktualisiert
- **Alt:** ~20 Sensoren (modbus_sungrow_old_2024.yaml.backup)
- **Neu:** 150+ Sensoren (modbus_sungrow.yaml)
- **Version:** 2026-04-27 Release
- **Quelle:** https://github.com/mkaiser/Sungrow-SHx-Inverter-Modbus-Home-Assistant

### 2. Secrets erweitert
Neue Einträge in `config/secrets.yaml`:
- `sungrow_modbus_device_address: 1` (gleich wie slave)
- `sungrow_modbus_wait_milliseconds: 5` (5ms für LAN, 20+ für WiNet-S)

### 3. Update-Script erstellt
`update-sungrow-integration.ps1` - Für zukünftige Updates:
```powershell
.\update-sungrow-integration.ps1           # Main branch
.\update-sungrow-integration.ps1 -Branch dev  # Dev branch
```

---

## 🆕 Neue Sensoren für pv_load_balancer

Die neue Integration bietet viele Sensoren die **optional** für erweiterte Steuerung genutzt werden könnten:

### EMS Control Sensoren (lesbar & schreibbar)
| Sensor | Entity ID | Verwendung |
|--------|-----------|------------|
| Battery min SoC | `number.sungrow_battery_min_soc` | Minimaler Batterieladestand |
| Battery max SoC | `number.sungrow_battery_max_soc` | Maximaler Batterieladestand |
| Export power limit | `number.sungrow_export_power_limit` | Grid Export Limit (0-10000W) |
| Battery forced charge power | `number.sungrow_battery_forced_charge_discharge_power` | Forced Charging |
| Export power limit min | `sensor.sungrow_export_power_limit_min` | Minimales Export Limit |
| Export power limit max | `sensor.sungrow_export_power_limit_max` | Maximales Export Limit |

### Zusätzliche Monitoring Sensoren
| Sensor | Entity ID | Verwendung |
|--------|-----------|------------|
| Battery power | `sensor.sungrow_battery_power` | Aktuelle Batterieleistung (+ laden, - entladen) |
| Export power raw | `sensor.sungrow_export_power_raw` | Rohdaten Grid Export |
| Daily exported energy | `sensor.sungrow_daily_exported_energy` | Täglich exportierte Energie |
| Total exported energy | `sensor.sungrow_total_exported_energy` | Gesamt exportierte Energie |

---

## 📋 Aktuelle pv_load_balancer Konfiguration

### Sensoren die aktuell verwendet werden:
1. **Wallbox Leistung:** `sensor.alf_ace0195477_alfen_s2_real_power_sum` (Alfen Modbus)
2. **Wallbox Status:** `sensor.alf_ace0195477_alfen_s2_mode_3_state` (Alfen Modbus)
3. **Max Current:** `number.alf_ace0195477_alfen_max_current_limit_s2` (Alfen)
4. **Usable Phases:** `select.alf_ace0195477_alfen_usable_phases2` (Alfen)
5. **Sungrow Sensoren:** Verfügbar über alte Integration, jetzt mehr Details

### Steuerung:
- **Lead System:** `pv_load_balancer` (bleibt bestehen)
- **Wallbox Control:** Alfen Modbus Service Calls
- **Sungrow:** Nur Monitoring (keine Steuerung durch pv_load_balancer)

---

## 🔄 Mögliche zukünftige Verbesserungen

### Option A: Erweiterte Sungrow-Integration (optional)
Falls du später **direkte Sungrow-Steuerung** willst:

```python
# In pv_load_balancer/coordinator.py könnte man optional hinzufügen:
async def _set_export_limit(self, limit_watts: int) -> None:
    """Set Sungrow export power limit."""
    await self.hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.sungrow_export_power_limit",
            "value": limit_watts
        },
    )
```

### Option B: Bessere Battery Min SoC Koordination
Falls pv_load_balancer später auch Batterie-SoC steuern soll:

```python
async def _adjust_battery_min_soc(self, new_min_soc: int) -> None:
    """Adjust battery min SoC based on forecasts."""
    await self.hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.sungrow_battery_min_soc",
            "value": new_min_soc
        },
    )
```

**ABER:** Diese Funktionen sind **OPTIONAL** und sollten nur hinzugefügt werden wenn tatsächlich benötigt!

---

## ✅ Empfehlung: Aktuellen Zustand beibehalten

**Warum:**
1. ✅ pv_load_balancer funktioniert bereits perfekt für Wallbox-Steuerung
2. ✅ Alfen Modbus gibt alle benötigten Wallbox-Daten
3. ✅ Sungrow Sensoren sind jetzt aktueller und detaillierter für Monitoring
4. ✅ Keine Änderungen am pv_load_balancer Code nötig
5. ✅ Klare Trennung: Sungrow = Monitoring, Alfen = Steuerung

**Später erweitern wenn:**
- 🔮 Du Export Limits direkt über Sungrow setzen willst
- 🔮 Du Battery Min SoC dynamisch anpassen willst
- 🔮 Du Forced Charging basierend auf Forecasts nutzen willst

---

## 🚀 Nächste Schritte

### Sofort:
```powershell
# Container neu starten um neue Sensoren zu laden
docker compose restart homeassistant
```

### Nach Restart überprüfen:
1. ✅ Sungrow Sensoren im UI anzeigen
2. ✅ pv_load_balancer läuft weiter
3. ✅ Alfen Modbus funktioniert weiter
4. ✅ Keine Fehler in Logs

### Später (optional):
```powershell
# Zukünftige Updates einfach mit:
.\update-sungrow-integration.ps1
```

### Auf QNAP deployen:
```powershell
.\deploy-to-qnap.ps1 -QnapIP 192.168.1.170
```

---

## 📚 Dokumentation

- **Sungrow Repo:** https://github.com/mkaiser/Sungrow-SHx-Inverter-Modbus-Home-Assistant
- **Installation Guide:** https://github.com/mkaiser/Sungrow-SHx-Inverter-Modbus-Home-Assistant/blob/main/doc/installation.md
- **Changelog:** https://github.com/mkaiser/Sungrow-SHx-Inverter-Modbus-Home-Assistant/blob/main/doc/changelog.md
- **Discord Support:** https://discord.gg/ZvYBejFkm2
