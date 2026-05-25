# Custom Components - Status & Migration Guide

## ✅ Status Übersicht (Stand: 24. Mai 2026)

| Integration | Status | Aktion |
|------------|--------|--------|
| `oekofen_pellematic_compact` | ✅ **Fertig** | Modernisiert für HA 2026.x |
| `pv_load_balancer` | ✅ **Fertig** | Neu erstellt, ersetzt sunny_balance_loader |
| `alfen_modbus` | ✅ **Fertig** | Von GitHub installiert (ThaStealth/alfen_modbus) |
| ~~`sunny_balance_loader`~~ | ❌ **Deaktiviert** | Deprecated, durch pv_load_balancer ersetzt |

---

## pv_load_balancer (NEU) - Modern Replacement

### Übersicht
Moderne Config Flow Integration für PV-Überschussladung der Alfen Wallbox.

**Funktionen:**
- ✅ Config Flow UI Setup (keine YAML Konfiguration nötig)
- ✅ DataUpdateCoordinator Pattern (60s Update-Intervall)
- ✅ Nutzung von Alfen Modbus Service Calls statt direktem Modbus
- ✅ 60-Sekunden-Durchschnitts-Sensoren
- ✅ Graduated Load Balancing (200W/400W/600W Schritte)
- ✅ Automatische 1/3-Phasen-Umschaltung
- ✅ Batterie SOC Integration

**Struktur:**
```
config/custom_components/pv_load_balancer/
├── __init__.py          # Entry setup & coordinator registration
├── coordinator.py       # DataUpdateCoordinator mit Load Balancing Logik
├── sensor.py           # 6 Sensor Entitäten
├── config_flow.py      # UI Configuration Flow
├── manifest.json       # Integration metadata
├── const.py           # Constants
├── strings.json       # UI Strings (DE/EN)
└── translations/
    └── en.json        # Kompilierte Übersetzungen
```

**Sensoren:**
1. `sensor.pv_export_power_60s_avg` - 60s Durchschnitt PV Export Power
2. `sensor.battery_power_60s_avg` - 60s Durchschnitt Batterie Power
3. `sensor.charging_current_proposal` - Vorgeschlagener Ladestrom
4. `sensor.charging_power_proposal` - Vorgeschlagene Ladeleistung
5. `sensor.charging_phases_proposal` - Vorgeschlagene Phasenanzahl
6. `sensor.pv_available_power` - Verfügbare PV-Leistung

**Service Calls statt direktem Modbus:**
```python
# Strom setzen
await self.hass.services.async_call(
    "number",
    "set_value",
    {
        "entity_id": "number.alf_ace0195477_alfen_max_current_limit_s2",
        "value": current_value,
    },
)

# Phasen umschalten
await self.hass.services.async_call(
    "select",
    "select_option",
    {
        "entity_id": "select.alf_ace0195477_alfen_usable_phases2",
        "option": "1 Phase" if phases == 1 else "3 Phases",
    },
)
```

---

## alfen_modbus (VON GITHUB)

### Installation
```bash
cd config/custom_components/
git clone https://github.com/ThaStealth/alfen_modbus.git
```

**Wichtige Features:**
- ✅ Auto-Renew Max Current (verhindert Timeout)
- ✅ 30+ Sensoren pro Socket
- ✅ Binary Sensors (Car Connected, Car Charging)
- ✅ Session Tracking (Energie, Dauer)
- ✅ Phase-Details (Strom/Spannung L1-L3)
- ✅ Number/Select Entities zur Steuerung

**Genutzte Entitäten:**
- `sensor.alf_ace0195477_alfen_s2_real_power_sum` - Aktuelle Ladeleistung
- `sensor.alf_ace0195477_alfen_s2_mode_3_state` - Ladestatus
- `number.alf_ace0195477_alfen_max_current_limit_s2` - Max Current Steuerung
- `select.alf_ace0195477_alfen_usable_phases2` - Phasen Steuerung

---

## oekofen_pellematic_compact - Durchgeführte Änderungen

### ✅ 1. __init__.py - Modernize setup/unload (ERLEDIGT)

**Änderung 1: async_setup_entry**

```python
# ✅ UMGESETZT:
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Ökofen Pellematic Component."""
    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]
    scan_interval = entry.data[CONF_SCAN_INTERVAL]

    _LOGGER.debug("Setup Pellematic Hub %s, %s", DOMAIN, name)

    hub = PellematicHub(hass, name, host, scan_interval)
    hass.data[DOMAIN][name] = {"hub": hub}

    # Modern way: forward all platforms at once
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
```

**Änderung 2: async_unload_entry**

```python
# ✅ UMGESETZT:
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Pellematic entry."""
    # Modern way: unload all platforms at once with walrus operator
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.data[CONF_NAME])
    
    return unload_ok
```

### ✅ 2. config_flow.py - Remove deprecated CONNECTION_CLASS (ERLEDIGT)

```python
# ✅ UMGESETZT:
class OekofenPellematicCompactConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Oekofen Pellematic Compact configflow."""

    VERSION = 1
    # CONNECTION_CLASS entfernt - wird aus manifest.json gelesen (iot_class)
```

---

## Dashboard Updates (ERLEDIGT)

### Alfen Eve Double Card
- ✅ Alle alten `sensor.alfen_*` Entitäten auf neue `sensor.alf_ace0195477_alfen_*` umgestellt
- ✅ Deutsche Namen für bessere Lesbarkeit hinzugefügt
- ✅ 28 zusätzliche Sensoren in neuer Section "Zusätzliche Sensoren" hinzugefügt
- ✅ Binary Sensors für Auto Connected/Charging
- ✅ Session Tracking (Energie, Dauer)
- ✅ Phase-Details (Strom L1-L3, Spannung L1-L3-N)

### Überschussladen Auto Card
- ✅ Sensoren auf neue pv_load_balancer Entity IDs aktualisiert:
  - `sensor.wallbox_alfen_eve_double_ng920_61101_pv_export_power_60s_avg`
  - `sensor.wallbox_alfen_eve_double_ng920_61101_battery_power_60s_avg`
  - `sensor.wallbox_alfen_eve_double_ng920_61101_charging_current_proposal`

---

## ~~sunny_balance_loader - DEPRECATED~~

**Status:** ❌ Deaktiviert und durch `pv_load_balancer` ersetzt

**Gründe für Deprecation:**
1. Verwendete veraltete YAML-Konfiguration
2. Direkter Modbus-Zugriff kollidiert mit alfen_modbus Integration
3. Keine Config Flow UI
4. Sync statt Async Update Pattern
5. Kein DataUpdateCoordinator Pattern

**Migration zu pv_load_balancer:** Abgeschlossen ✅

---
---

## Nächste Schritte für QNAP Deployment

### 1. Lokale Tests abschließen ✅
- [x] pv_load_balancer funktioniert korrekt
- [x] oekofen_pellematic_compact lädt ohne Fehler
- [x] alfen_modbus Integration funktioniert
- [x] Dashboard aktualisiert und getestet
- [x] Keine Fehler in Logs

### 2. Auf QNAP deployen (siehe QNAP-DEPLOYMENT.md)
- [ ] Backup erstellen
- [ ] Code auf v2 Branch pushen
- [ ] Auf QNAP: `git pull origin v2`
- [ ] Container neu bauen: `docker-compose build`
- [ ] Container starten: `docker-compose up -d`
- [ ] Logs prüfen und Funktionalität testen

### 3. Hardware-Verbindungen testen
- [ ] Sungrow SH10RT (Modbus TCP 192.168.1.155:502)
- [ ] Alfen NG920-61101 Eve Double (192.168.1.151:502)
- [ ] PV-Überschussladung aktiv testen
- [ ] Phasenumschaltung testen (1/3 Phasen)

### 4. Monitoring
- [ ] Load Balancing Logs überwachen
- [ ] Wallbox Ladeverhalten beobachten
- [ ] Batterie SOC Integration prüfen

Bei Fragen oder Problemen beim Deployment helfe ich gerne weiter!
