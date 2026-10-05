"""DataUpdateCoordinator for PV Load Balancer."""

from datetime import timedelta
import logging
import struct
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_LOAD_BALANCING_ACTIVE,
    CONF_LOAD_BALANCING_MINIMAL,
    CONF_PV_BATTERY_LEVEL_SENSOR,
    CONF_PV_BATTERY_POWER_SENSOR,
    CONF_PV_EXPORT_POWER_SENSOR,
    CONF_WALLBOX_CHARGING_POWER_SENSOR,
    CONF_WALLBOX_MAX_CURRENT_NUMBER,
    CONF_WALLBOX_PHASES_SELECT,
    CONF_WALLBOX_SOCKET,
    CONF_WALLBOX_STATUS_SENSOR,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    STEPS_WATT,
    VOLTAGE,
    WALLBOX_AMP_MAX,
    WALLBOX_AMP_MIN,
    WALLBOX_AMP_STOP,
    WALLBOX_BATTERY_LOAD_MIN_LOWER,
    WALLBOX_BATTERY_LOAD_MIN_UPPER,
    WALLBOX_STATE_CODES_ACTIVE,
)

_LOGGER = logging.getLogger(__name__)


def convert_float_to_r32(float_value: float) -> list[int]:
    """Convert a float value to two 16-bit integers in Modbus format (r32 word-swapped-float32)."""
    packed_float = struct.pack(">f", float_value)
    high_word = struct.unpack(">H", packed_float[0:2])[0]
    low_word = struct.unpack(">H", packed_float[2:4])[0]
    return [high_word, low_word]


class PVLoadBalancerCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching PV Load Balancer data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )
        self.entry = entry
        self._last_pv_full_available_power = 0.0
        self._startup_time = time.monotonic()

        # Initialize statistics tracking for 60s averages
        self._pv_export_samples: list[tuple[float, float]] = []  # (timestamp, value)
        self._battery_power_samples: list[tuple[float, float]] = (
            []
        )  # (timestamp, value)

    def _get_sensor_value(self, entity_id: str, default: float = 0.0) -> float:
        """Get sensor value as float or return default."""
        if not entity_id:
            return default

        if state := self.hass.states.get(entity_id):
            # Skip warning for expected non-numeric states during startup
            if state.state in ("unknown", "unavailable", "none"):
                return default

            try:
                return float(state.state)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Sensor %s has non-numeric state: %s", entity_id, state.state
                )
        else:
            _LOGGER.debug("Sensor %s not available", entity_id)
        return default

    def _update_samples(
        self,
        samples: list[tuple[float, float]],
        new_value: float,
        max_age_seconds: int = 60,
    ) -> float:
        """Update samples list and calculate mean of last 60 seconds."""
        current_time = time.time()

        samples.append((current_time, new_value))

        cutoff_time = current_time - max_age_seconds
        while samples and samples[0][0] < cutoff_time:
            samples.pop(0)

        if not samples:
            return 0.0
        return sum(value for _, value in samples) / len(samples)

    def _is_initialization_window(self) -> bool:
        """Return True during the first minute after a reconnect/startup."""
        return time.monotonic() - getattr(self, "_startup_time", time.monotonic()) < 60

    def _get_minimum_safe_ampere(self, battery_level: float) -> float:
        """Return the minimum current that should be offered during startup."""
        if self._is_initialization_window():
            return max(WALLBOX_AMP_MIN, 5.0)
        return WALLBOX_AMP_MIN

    async def _async_set_wallbox_charging(
        self, phases: int, ampere: float, watt: float
    ) -> None:
        """Set wallbox charging parameters via Alfen Modbus entities."""
        socket = self.entry.data.get(CONF_WALLBOX_SOCKET)
        phases_select_entity = self.entry.data.get(CONF_WALLBOX_PHASES_SELECT)
        max_current_number_entity = self.entry.data.get(CONF_WALLBOX_MAX_CURRENT_NUMBER)

        try:
            # Set charging phases via select entity
            phase_option = "3 Phases" if phases == 3 else "1 Phase"
            await self.hass.services.async_call(
                "select",
                "select_option",
                {
                    "entity_id": phases_select_entity,
                    "option": phase_option,
                },
                blocking=True,
            )

            # Set max current via number entity
            await self.hass.services.async_call(
                "number",
                "set_value",
                {
                    "entity_id": max_current_number_entity,
                    "value": ampere,
                },
                blocking=True,
            )

            # Log to logbook
            msg = f"PV Load Balancer: Socket {socket} | {watt:.0f} W | {ampere:.1f} A | {phases} phase(s)"
            _LOGGER.info(msg)
            await self.hass.services.async_call(
                "logbook",
                "log",
                {"name": DOMAIN, "message": msg},
            )
        except Exception as err:
            _LOGGER.error("Failed to set wallbox charging parameters: %s", err)
            raise UpdateFailed(f"Wallbox control failed: {err}") from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from sensors and calculate new charging proposal."""
        # Get sensor entity IDs from config
        pv_export_sensor = self.entry.data.get(CONF_PV_EXPORT_POWER_SENSOR, "")
        battery_level_sensor = self.entry.data.get(CONF_PV_BATTERY_LEVEL_SENSOR, "")
        battery_power_sensor = self.entry.data.get(CONF_PV_BATTERY_POWER_SENSOR, "")
        wallbox_power_sensor = self.entry.data.get(
            CONF_WALLBOX_CHARGING_POWER_SENSOR, ""
        )
        wallbox_status_sensor = self.entry.data.get(CONF_WALLBOX_STATUS_SENSOR, "")
        lb_active_sensor = self.entry.data.get(CONF_LOAD_BALANCING_ACTIVE, "")
        lb_minimal_sensor = self.entry.data.get(CONF_LOAD_BALANCING_MINIMAL, "")

        # Get current values
        pv_export_power = self._get_sensor_value(pv_export_sensor)
        battery_level = self._get_sensor_value(battery_level_sensor)
        battery_power = self._get_sensor_value(battery_power_sensor)
        wallbox_charging_power = self._get_sensor_value(wallbox_power_sensor)

        # Update 60s averages
        pv_export_power_60s_avg = self._update_samples(
            self._pv_export_samples, pv_export_power
        )
        battery_power_60s_avg = self._update_samples(
            self._battery_power_samples, battery_power
        )

        # Check wallbox status
        wallbox_status = "Unknown"
        if status_state := self.hass.states.get(wallbox_status_sensor):
            wallbox_status = status_state.state

        # Check if load balancing is active
        load_balancing_active = False
        if lb_state := self.hass.states.get(lb_active_sensor):
            load_balancing_active = lb_state.state == "on"

        # Default values
        wallbox_watt_max = 3 * VOLTAGE * WALLBOX_AMP_MAX
        wallbox_watt_min = 1 * VOLTAGE * WALLBOX_AMP_MIN
        wallbox_watt_stop = 1 * VOLTAGE * WALLBOX_AMP_STOP

        phases = 3
        new_proposal_amp = WALLBOX_AMP_MAX
        new_proposal_watt = wallbox_watt_max

        if not load_balancing_active:
            # Some EVs need a valid current during the first minute of connection,
            # even when automatic PV balancing is disabled. Offer a safe startup
            # current during that window and then return to a stopped state.
            if self._is_initialization_window():
                phases = 1
                new_proposal_amp = max(5.0, WALLBOX_AMP_STOP)
                new_proposal_watt = VOLTAGE * phases * new_proposal_amp
            else:
                new_proposal_amp = WALLBOX_AMP_STOP
                new_proposal_watt = 0.0

        if load_balancing_active:
            # Load balancing is active, calculate proposal
            new_proposal_amp = WALLBOX_AMP_STOP
            new_proposal_watt = wallbox_watt_stop

            if wallbox_status in WALLBOX_STATE_CODES_ACTIVE:
                # Wallbox is charging/connected
                pv_full_available_power_60s_avg = pv_export_power_60s_avg

                # Add battery power if battery level is sufficient or battery is discharging
                if (
                    battery_level > WALLBOX_BATTERY_LOAD_MIN_LOWER
                    or battery_power_60s_avg < 0
                ):
                    pv_full_available_power_60s_avg += battery_power_60s_avg

                # Calculate new proposal
                if pv_full_available_power_60s_avg not in {
                    0.0,
                    self._last_pv_full_available_power,
                }:
                    self._last_pv_full_available_power = pv_full_available_power_60s_avg

                    if pv_full_available_power_60s_avg > 0:
                        # Add excess power to charging power
                        new_proposal_watt = (
                            wallbox_charging_power + pv_full_available_power_60s_avg
                        )
                    elif pv_full_available_power_60s_avg < (-1 * STEPS_WATT):
                        # Decrease charging power
                        if pv_full_available_power_60s_avg < (-40 * STEPS_WATT):
                            # Very high export, stop charging
                            new_proposal_watt = wallbox_watt_stop
                        elif pv_full_available_power_60s_avg < (-30 * STEPS_WATT):
                            # Fast decrease
                            new_proposal_watt = wallbox_charging_power - 3 * STEPS_WATT
                        elif pv_full_available_power_60s_avg < (-20 * STEPS_WATT):
                            # Medium decrease
                            new_proposal_watt = wallbox_charging_power - 2 * STEPS_WATT
                        else:
                            # Slow decrease
                            new_proposal_watt = wallbox_charging_power - STEPS_WATT
                    else:
                        # Keep current charging power
                        new_proposal_watt = (
                            wallbox_charging_power
                            if wallbox_charging_power > 0
                            else wallbox_watt_stop
                        )

                # Calculate ampere and phases
                break_even_watt_3phases = 3 * VOLTAGE * WALLBOX_AMP_MIN
                if new_proposal_watt > break_even_watt_3phases:
                    phases = 3
                else:
                    phases = 1
                new_proposal_amp = round(new_proposal_watt / (VOLTAGE * phases), 3)

                # Final checks
                if new_proposal_amp > WALLBOX_AMP_MAX:
                    new_proposal_amp = WALLBOX_AMP_MAX
                    new_proposal_watt = wallbox_watt_max
                else:
                    minimum_amp = self._get_minimum_safe_ampere(battery_level)

                    if new_proposal_amp < minimum_amp:
                        # Check if minimal load balancing is active
                        load_balancing_minimal = False
                        if lb_min_state := self.hass.states.get(lb_minimal_sensor):
                            load_balancing_minimal = lb_min_state.state == "on"

                        if load_balancing_minimal or (
                            battery_level > WALLBOX_BATTERY_LOAD_MIN_UPPER
                            and new_proposal_amp > WALLBOX_AMP_MIN / 2
                        ):
                            new_proposal_amp = max(minimum_amp, WALLBOX_AMP_MIN)
                            new_proposal_watt = max(
                                wallbox_watt_min,
                                (VOLTAGE * phases * new_proposal_amp),
                            )
                            phases = 1
                        else:
                            new_proposal_amp = WALLBOX_AMP_STOP
                            new_proposal_watt = 0.0

        # Set new proposal to wallbox
        await self._async_set_wallbox_charging(
            phases, new_proposal_amp, new_proposal_watt
        )

        # Return data for sensors
        return {
            "pv_export_power_60s_avg": pv_export_power_60s_avg,
            "battery_power_60s_avg": battery_power_60s_avg,
            "new_charging_current": new_proposal_amp,
            "new_charging_power": new_proposal_watt,
            "new_charging_phases": phases,
            "load_balancing_active": load_balancing_active,
            "wallbox_status": wallbox_status,
            "pv_available_power": (
                pv_full_available_power_60s_avg
                if load_balancing_active
                and wallbox_status in WALLBOX_STATE_CODES_ACTIVE
                else 0.0
            ),
        }
