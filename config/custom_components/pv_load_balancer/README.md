# PV Load Balancer

Modern Home Assistant integration for intelligent EV charging based on available PV power.

## Features

- 🌞 **Solar-optimized charging**: Only charges with excess PV power
- 🔋 **Battery integration**: Uses battery power when SOC is sufficient
- ⚡ **Intelligent phase switching**: Automatically switches between 1-phase and 3-phase charging
- 📊 **60-second averaging**: Smooth power calculations to avoid frequent changes
- 🎛️ **Flexible control**: Active/minimal modes via input_boolean
- 📝 **Detailed logging**: All charging adjustments logged to Home Assistant logbook

## Requirements

- Home Assistant 2026.x or newer
- **Alfen Modbus integration** (e.g., ThaStealth/alfen_modbus) installed and configured
- PV system with export power sensor
- Battery system with power and level sensors
- Two input_boolean helpers:
  - `input_boolean.load_balancing_active`
  - `input_boolean.load_balancing_minimal`

## Installation

1. Copy the `pv_load_balancer` folder to `config/custom_components/`
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "PV Load Balancer"
5. Configure with your sensor entity IDs

## Configuration

During setup, you'll need to provide:

### Required Sensors
- **PV Export Power Sensor**: Raw export power from your PV system (W)
- **Battery Level Sensor**: Battery state of charge (%)
- **Battery Power Sensor**: Battery charging/discharging power (W, negative when discharging)
- **Wallbox Charging Power Sensor**: Current charging power (W)
- **Wallbox Status Sensor**: Wallbox connection/charging status

### Control Switches
- **Load Balancing Active**: Master switch (input_boolean)
- **Load Balancing Minimal**: Minimal charging mode (input_boolean)

### Wallbox Control Entities
- **Wallbox Phases Select**: Select entity for phase switching (e.g., `select.alf_ace0195477_alfen_usable_phases2`)
  - Must support "1 Phase" and "3 Phases" options
- **Wallbox Max Current Number**: Number entity for max current control (e.g., `number.alf_ace0195477_alfen_max_current_limit_s2`)
  - Controls charging current in Amperes

### Socket Configuration
- **Wallbox Socket**: Socket number 1 or 2 (default: 2) - used for logging only

## How It Works

### Normal Mode (Load Balancing Active)

1. Calculates 60-second average of PV export and battery power
2. Determines available power = export power + battery power (if SOC > 50%)
3. Adjusts wallbox charging current based on available power:
   - **Excess power available**: Increases charging by available power
   - **Power shortage < 200W**: Keeps current level
   - **Power shortage 200-4000W**: Decreases by 200W/cycle (slow)
   - **Power shortage 4000-6000W**: Decreases by 400W/cycle (medium)
   - **Power shortage 6000-8000W**: Decreases by 600W/cycle (fast)
   - **Power shortage > 8000W**: Stops charging immediately

### Minimal Mode (Load Balancing Minimal Active)

- Forces minimum charging current (6.1A) even if insufficient PV power
- Also activates when battery SOC > 95% and calculated current > 3A

### Phase Switching

- **3-phase charging**: When required power > 4200W (3 × 230V × 6.1A)
- **1-phase charging**: When required power ≤ 4200W
- Maximizes efficiency for partial-load conditions

## Example Configuration

### Input Booleans (configuration.yaml)

```yaml
input_boolean:
  load_balancing_active:
    name: Load Balancing Active
    icon: mdi:car-electric

  load_balancing_minimal:
    name: Load Balancing Minimal
    icon: mdi:car-emergency
```

### Modbus Configuration Example

```yaml
modbus:
  - name: alfen_eve_double
    type: tcp
    host: 192.168.1.100
    port: 502
```

## Sensors Created

After setup, the integration creates these sensors:

- `sensor.pv_export_power_60s_avg`: 60-second average of PV export power
- `sensor.battery_power_60s_avg`: 60-second average of battery power
- `sensor.charging_current_proposal`: Calculated charging current sent to wallbox
- `sensor.charging_power_proposal`: Calculated charging power
- `sensor.charging_phases_proposal`: Number of phases (1 or 3)
- `sensor.pv_available_power`: Total available power (export + battery)

## Troubleshooting

### Wallbox not responding
- Check Modbus hub name matches your configuration
- Verify socket number (1 or 2)
- Check Modbus addresses (1215 for phases, 1210 for max ampere)

### Frequent charging starts/stops
- Check 60-second averaging is working
- Increase STEPS_WATT in const.py (default: 200W)
- Verify wallbox status sensor reports correct states

### Wrong phase count
- Verify WALLBOX_AMP_MIN setting (default: 6.1A)
- Check VOLTAGE setting (default: 230V)
- Ensure wallbox supports 1-phase and 3-phase switching

## Advanced Configuration

Edit `const.py` to customize:

```python
WALLBOX_AMP_MAX = 32.0  # Maximum charging current
WALLBOX_AMP_MIN = 6.1   # Minimum charging current
WALLBOX_AMP_STOP = 5.0  # Stop charging below this
WALLBOX_BATTERY_LOAD_MIN_LOWER = 50.0  # Min battery SOC to use battery power
WALLBOX_BATTERY_LOAD_MIN_UPPER = 95.0  # Battery SOC for forced minimal charging
VOLTAGE = 230.0  # Grid voltage
STEPS_WATT = 200.0  # Power adjustment step size
```

## Migration from sunny_balance_loader

This integration replaces the old `sunny_balance_loader` with:

✅ Modern async/await architecture  
✅ Config Flow (UI-based setup)  
✅ DataUpdateCoordinator (centralized updates)  
✅ Entity-based sensors  
✅ Device registration  
✅ Better error handling  

To migrate:

1. Note your current sensor entity IDs from configuration.yaml
2. Install this integration
3. Configure with your entity IDs
4. Test in parallel (both can run simultaneously)
5. Remove old `sunny_balance_loader` when satisfied

## Support

For issues or questions, check Home Assistant logs for `pv_load_balancer` entries.

## License

This integration is provided as-is for personal use.
