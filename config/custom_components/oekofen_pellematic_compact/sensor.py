"""The Ökofen Pellematic Compact integration."""

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfMass,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    CIRC1_SENSOR_TYPES,
    CONF_CIRCULATOR,
    CONF_NUM_OF_HEATING_CIRCUIT,
    CONF_NUM_OF_HOT_WATER,
    CONF_NUM_OF_PELLEMATIC_HEATER,
    CONF_SMART_PV,
    CONF_SOLAR_CIRCUIT,
    CONF_STIRLING,
    DOMAIN,
    HK_BINARY_SENSOR_TYPES,
    HK_SENSOR_TYPES,
    PE_SENSOR_TYPES,
    POWER_SENSOR_TYPES,
    PU1_BINARY_SENSOR_TYPES,
    PU1_SENSOR_TYPES,
    SE1_SENSOR_TYPES,
    SK1_BINARY_SENSOR_TYPES,
    SK1_SENSOR_TYPES,
    STIRLING_SENSOR_TYPES,
    SYSTEM_BINARY_SENSOR_TYPES,
    SYSTEM_SENSOR_TYPES,
    WW_BINARY_SENSOR_TYPES,
    WW_SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """Set up entry."""
    hub_name = entry.data[CONF_NAME]
    hub = hass.data[DOMAIN][hub_name]["hub"]

    # Get configuration with defaults for legacy entries
    num_heating_circuit = entry.data[CONF_NUM_OF_HEATING_CIRCUIT]
    solar_circuit = entry.data[CONF_SOLAR_CIRCUIT]
    stirling = entry.data.get(CONF_STIRLING, False)
    smart_pv = entry.data.get(CONF_SMART_PV, False)
    cirulator = entry.data.get(CONF_CIRCULATOR, False)
    num_hot_water = entry.data.get(CONF_NUM_OF_HOT_WATER, 1)
    num_pellematic_heater = entry.data.get(CONF_NUM_OF_PELLEMATIC_HEATER, 1)

    _LOGGER.debug("Setup entry %s %s", hub_name, hub)

    device_info = {
        "identifiers": {(DOMAIN, hub_name)},
        "name": hub_name,
        "manufacturer": ATTR_MANUFACTURER,
        "model": ATTR_MODEL,
    }

    entities: list[PellematicSensor | PellematicBinarySensor] = []

    # Add system sensors
    _add_sensors(entities, hub_name, hub, device_info, "system", SYSTEM_SENSOR_TYPES)
    _add_binary_sensors(
        entities, hub_name, hub, device_info, "system", SYSTEM_BINARY_SENSOR_TYPES
    )

    # Add heating circuit sensors
    for heating_cir_count in range(num_heating_circuit):
        circuit_num = heating_cir_count + 1
        prefix = f"hk{circuit_num}"
        _add_sensors(
            entities, hub_name, hub, device_info, prefix, HK_SENSOR_TYPES, circuit_num
        )
        _add_binary_sensors(
            entities,
            hub_name,
            hub,
            device_info,
            prefix,
            HK_BINARY_SENSOR_TYPES,
            circuit_num,
        )

    # Add stirling sensors if configured
    if stirling:
        _add_sensors(
            entities, hub_name, hub, device_info, "stirling", STIRLING_SENSOR_TYPES
        )

    # Add smart PV sensors if configured
    if smart_pv:
        _add_sensors(entities, hub_name, hub, device_info, "power", POWER_SENSOR_TYPES)

    # Add circulator sensors if configured
    if cirulator:
        _add_sensors(entities, hub_name, hub, device_info, "circ1", CIRC1_SENSOR_TYPES)

    # Add solar circuit sensors if configured
    if solar_circuit:
        _add_sensors(entities, hub_name, hub, device_info, "sk1", SK1_SENSOR_TYPES)
        _add_binary_sensors(
            entities, hub_name, hub, device_info, "sk1", SK1_BINARY_SENSOR_TYPES
        )
        _add_sensors(entities, hub_name, hub, device_info, "se1", SE1_SENSOR_TYPES)

    # Add pellematic heater sensors
    for pe_count in range(num_pellematic_heater):
        heater_num = pe_count + 1
        _add_sensors(
            entities,
            hub_name,
            hub,
            device_info,
            f"pe{heater_num}",
            PE_SENSOR_TYPES,
            heater_num,
        )

    # Add pump sensors
    _add_sensors(entities, hub_name, hub, device_info, "pu1", PU1_SENSOR_TYPES)
    _add_binary_sensors(
        entities, hub_name, hub, device_info, "pu1", PU1_BINARY_SENSOR_TYPES
    )

    # Add hot water sensors
    for hot_water_count in range(num_hot_water):
        water_num = hot_water_count + 1
        _add_sensors(
            entities,
            hub_name,
            hub,
            device_info,
            f"ww{water_num}",
            WW_SENSOR_TYPES,
            water_num,
        )
        _add_binary_sensors(
            entities,
            hub_name,
            hub,
            device_info,
            f"ww{water_num}",
            WW_BINARY_SENSOR_TYPES,
            water_num,
        )

    # Add error sensors
    for error_count in range(1, 6):
        sensor = PellematicSensor(
            hub_name,
            hub,
            device_info,
            "error",
            f"Error {error_count}",
            f"error_{error_count}",
            None,
            "mdi:alert-circle",
        )
        entities.append(sensor)

    _LOGGER.debug("Entities added: %i", len(entities))
    async_add_entities(entities)
    return True


def _add_sensors(
    entities: list,
    hub_name: str,
    hub: Any,
    device_info: dict,
    prefix: str,
    sensor_types: dict,
    number: int | None = None,
) -> None:
    """Add sensors to entities list."""
    for name, key, unit, icon in sensor_types.values():
        formatted_name = name.format(f" {number}") if number else name
        sensor = PellematicSensor(
            hub_name, hub, device_info, prefix, formatted_name, key, unit, icon
        )
        entities.append(sensor)


def _add_binary_sensors(
    entities: list,
    hub_name: str,
    hub: Any,
    device_info: dict,
    prefix: str,
    sensor_types: dict,
    number: int | None = None,
) -> None:
    """Add binary sensors to entities list."""
    for name, key, unit, icon in sensor_types.values():
        formatted_name = name.format(f" {number}") if number else name
        sensor = PellematicBinarySensor(
            hub_name, hub, device_info, prefix, formatted_name, key, unit, icon
        )
        entities.append(sensor)


class PellematicBinarySensor(BinarySensorEntity):
    """Representation of a binary sensor entity."""

    _attr_should_poll = False

    def __init__(
        self,
        platform_name: str,
        hub: Any,
        device_info: dict,
        prefix: str,
        name: str,
        key: str,
        unit: str | None,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        self._platform_name = platform_name
        self._hub = hub
        self._prefix = prefix
        self._key = key
        self._attr_name = f"{self._platform_name} {name}"
        self._attr_unique_id = (
            f"{self._platform_name.lower()}_{self._prefix}_{self._key}"
        )
        self._unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = device_info  # type: ignore
        self._attr_device_class = BinarySensorDeviceClass.POWER
        if icon == "mdi:usb-flash-drive":
            self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

        _LOGGER.debug(
            "Adding PellematicBinarySensor: %s, %s, %s, %s",
            self._attr_name,
            self._attr_unique_id,
            self._unit_of_measurement,
            self._attr_device_class,
        )

    @property
    def is_on(self) -> bool | None:
        """Return the state of the sensor."""
        try:
            return self._hub.data[self._prefix][self._key]["val"]
        except (KeyError, TypeError):
            try:
                return self._hub.data[self._prefix][self._key]
            except (KeyError, TypeError):
                return None

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self._hub.async_add_pellematic_sensor(self._api_data_updated)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks."""
        self._hub.async_remove_pellematic_sensor(self._api_data_updated)

    @callback
    def _api_data_updated(self) -> None:
        """Handle updated data from the hub."""
        self.async_write_ha_state()


class PellematicSensor(SensorEntity):
    """Representation of a Pellematic sensor."""

    _attr_should_poll = False

    def __init__(
        self,
        platform_name: str,
        hub: Any,
        device_info: dict,
        prefix: str,
        name: str,
        key: str,
        unit: str | None,
        icon: str,
    ) -> None:
        """Initialize the sensor."""
        self._platform_name = platform_name
        self._hub = hub
        self._prefix = prefix
        self._key = key
        self._attr_name = f"{self._platform_name} {name}"
        self._attr_unique_id = (
            f"{self._platform_name.lower()}_{self._prefix}_{self._key}"
        )
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_info = device_info  # type: ignore

        # Set device class and state class based on unit
        self._configure_device_class(unit)

        _LOGGER.debug(
            "Adding PellematicSensor: %s, %s, %s",
            self._attr_name,
            self._attr_unique_id,
            self._attr_native_unit_of_measurement,
        )

    def _configure_device_class(self, unit: str | None) -> None:
        """Configure device class and state class based on unit."""
        if unit in (UnitOfPower.KILO_WATT, UnitOfPower.WATT):
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_device_class = SensorDeviceClass.POWER
        elif unit in (UnitOfEnergy.WATT_HOUR, UnitOfEnergy.KILO_WATT_HOUR):
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_device_class = SensorDeviceClass.ENERGY
        elif unit == UnitOfTemperature.CELSIUS:
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == UnitOfMass.KILOGRAMS:
            self._attr_device_class = SensorDeviceClass.WEIGHT
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == PERCENTAGE:
            self._attr_device_class = SensorDeviceClass.POWER_FACTOR
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == UnitOfTime.HOURS:
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif unit in (
            UnitOfTime.MINUTES,
            UnitOfTime.SECONDS,
            UnitOfTime.MILLISECONDS,
        ):
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        try:
            current_value = self._hub.data[self._prefix][self._key]
            return self._convert_value(current_value)
        except (KeyError, TypeError, ValueError):
            return None

    def _convert_value(self, value: Any) -> float | int | str:
        """Convert raw value based on device class and unit."""
        if getattr(self, "_attr_device_class", None) == SensorDeviceClass.TEMPERATURE:
            return int(value) / 10
        if self._attr_native_unit_of_measurement == UnitOfEnergy.KILO_WATT_HOUR:
            # SE1 needs / 10 but POWER needs / 10000
            divisor = 10 if self._prefix == "se1" else 10000
            return int(value) / divisor
        return value

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self._hub.async_add_pellematic_sensor(self._api_data_updated)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks."""
        self._hub.async_remove_pellematic_sensor(self._api_data_updated)

    @callback
    def _api_data_updated(self) -> None:
        """Handle updated data from the hub."""
        self.async_write_ha_state()
