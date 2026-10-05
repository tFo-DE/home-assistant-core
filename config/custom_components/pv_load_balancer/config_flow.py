"""Config flow for PV Load Balancer integration."""

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

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
    DEFAULT_SOCKET,
    DOMAIN,
)


class PVLoadBalancerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PV Load Balancer."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate that all entities exist
            for entity_key in [
                CONF_PV_EXPORT_POWER_SENSOR,
                CONF_PV_BATTERY_LEVEL_SENSOR,
                CONF_PV_BATTERY_POWER_SENSOR,
                CONF_WALLBOX_CHARGING_POWER_SENSOR,
                CONF_WALLBOX_STATUS_SENSOR,
                CONF_LOAD_BALANCING_ACTIVE,
                CONF_LOAD_BALANCING_MINIMAL,
                CONF_WALLBOX_PHASES_SELECT,
                CONF_WALLBOX_MAX_CURRENT_NUMBER,
            ]:
                entity_id = user_input.get(entity_key)
                if entity_id and not self.hass.states.get(entity_id):
                    errors[entity_key] = "entity_not_found"

            if not errors:
                return self.async_create_entry(
                    title="PV Load Balancer",
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_PV_EXPORT_POWER_SENSOR,
                    default="sensor.export_power_raw",  # type: ignore
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_PV_BATTERY_LEVEL_SENSOR,
                    default="sensor.battery_level",  # type: ignore
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_PV_BATTERY_POWER_SENSOR,
                    default="sensor.signed_battery_power",  # type: ignore
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_WALLBOX_CHARGING_POWER_SENSOR,
                    default="sensor.alf_ace0195477_alfen_s2_real_power_sum",  # type: ignore
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_WALLBOX_STATUS_SENSOR,
                    default="sensor.alf_ace0195477_alfen_s2_mode_3_state",  # type: ignore
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_LOAD_BALANCING_ACTIVE,
                    default="input_boolean.load_balancing_active",  # type: ignore
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="input_boolean")
                ),
                vol.Required(
                    CONF_LOAD_BALANCING_MINIMAL,
                    default="input_boolean.load_balancing_minimal",  # type: ignore
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="input_boolean")
                ),
                vol.Required(
                    CONF_WALLBOX_PHASES_SELECT,
                    default="select.alf_ace0195477_alfen_usable_phases2",  # type: ignore
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="select")
                ),
                vol.Required(
                    CONF_WALLBOX_MAX_CURRENT_NUMBER,
                    default="number.alf_ace0195477_alfen_max_current_limit_s2",  # type: ignore
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="number")
                ),
                vol.Required(
                    CONF_WALLBOX_SOCKET,
                    default=DEFAULT_SOCKET,  # type: ignore
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=2)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
