"""Sensor platform for PV Load Balancer."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PVLoadBalancerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PV Load Balancer sensors from a config entry."""
    coordinator: PVLoadBalancerCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            PVExportPower60sAvgSensor(coordinator, entry),
            BatteryPower60sAvgSensor(coordinator, entry),
            ChargingCurrentProposalSensor(coordinator, entry),
            ChargingPowerProposalSensor(coordinator, entry),
            ChargingPhasesProposalSensor(coordinator, entry),
            PVAvailablePowerSensor(coordinator, entry),
        ]
    )


class PVLoadBalancerSensorBase(
    CoordinatorEntity[PVLoadBalancerCoordinator], SensorEntity
):
    """Base class for PV Load Balancer sensors."""

    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: PVLoadBalancerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "PV Load Balancer",
            "manufacturer": "Custom",
            "model": "PV Load Balancer",
        }


class PVExportPower60sAvgSensor(PVLoadBalancerSensorBase):
    """Sensor for 60s average of PV export power."""

    _attr_name = "PV Export Power 60s Avg"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PVLoadBalancerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pv_export_power_60s_avg"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("pv_export_power_60s_avg")
        return None


class BatteryPower60sAvgSensor(PVLoadBalancerSensorBase):
    """Sensor for 60s average of battery power."""

    _attr_name = "Battery Power 60s Avg"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PVLoadBalancerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_battery_power_60s_avg"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("battery_power_60s_avg")
        return None


class ChargingCurrentProposalSensor(PVLoadBalancerSensorBase):
    """Sensor for proposed charging current."""

    _attr_name = "Charging Current Proposal"
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PVLoadBalancerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_charging_current_proposal"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("new_charging_current")
        return None


class ChargingPowerProposalSensor(PVLoadBalancerSensorBase):
    """Sensor for proposed charging power."""

    _attr_name = "Charging Power Proposal"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PVLoadBalancerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_charging_power_proposal"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("new_charging_power")
        return None


class ChargingPhasesProposalSensor(PVLoadBalancerSensorBase):
    """Sensor for proposed charging phases."""

    _attr_name = "Charging Phases Proposal"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PVLoadBalancerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_charging_phases_proposal"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("new_charging_phases")
        return None


class PVAvailablePowerSensor(PVLoadBalancerSensorBase):
    """Sensor for available PV power (export + battery)."""

    _attr_name = "PV Available Power"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: PVLoadBalancerCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_pv_available_power"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get("pv_available_power")
        return None
