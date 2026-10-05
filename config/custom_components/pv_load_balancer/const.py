"""Constants for the PV Load Balancer integration."""

DOMAIN = "pv_load_balancer"

# Configuration keys - Sensors
CONF_PV_EXPORT_POWER_SENSOR = "pv_export_power_sensor"
CONF_PV_BATTERY_LEVEL_SENSOR = "pv_battery_level_sensor"
CONF_PV_BATTERY_POWER_SENSOR = "pv_battery_power_sensor"
CONF_WALLBOX_CHARGING_POWER_SENSOR = "wallbox_charging_power_sensor"
CONF_WALLBOX_STATUS_SENSOR = "wallbox_status_sensor"

# Configuration keys - Wallbox Control Entities
CONF_WALLBOX_PHASES_SELECT = (
    "wallbox_phases_select"  # select entity for 1/3 phase switching
)
CONF_WALLBOX_MAX_CURRENT_NUMBER = (
    "wallbox_max_current_number"  # number entity for max current (A)
)
CONF_WALLBOX_SOCKET = "wallbox_socket"  # socket number (for logging only)

# Configuration keys - Load Balancing Controls
CONF_LOAD_BALANCING_ACTIVE = "load_balancing_active_sensor"
CONF_LOAD_BALANCING_MINIMAL = "load_balancing_minimal_sensor"

# Defaults
DEFAULT_SOCKET = 2
DEFAULT_UPDATE_INTERVAL = 60  # seconds

# Wallbox limits
WALLBOX_AMP_MAX = 32.0
WALLBOX_AMP_MIN = 6.1
WALLBOX_AMP_STOP = 5.0
WALLBOX_BATTERY_LOAD_MIN_LOWER = 50.0
WALLBOX_BATTERY_LOAD_MIN_UPPER = 95.0

# Power calculation
VOLTAGE = 230.0
STEPS_WATT = 200.0

# Wallbox status codes that indicate active charging/connection
WALLBOX_STATE_CODES_ACTIVE = ["C2", "D2", "B1", "B2", "C1", "D1", "E"]
