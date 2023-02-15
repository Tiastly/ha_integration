"""Config flow for ePlate."""
from __future__ import annotations
import json
import re
import logging
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.data_entry_flow import FlowResult

from homeassistant.helpers.service_info.mqtt import MqttServiceInfo
from .roomlist import ROOM_LIST
from .const import (
    DOMAIN,
    ROOM_TYPE,
    CMD_TYPE,
    ATTR_DELAY_MIN,
    ATTR_DELAY_MAX,
    ATTR_SENSOR_MAX,
    PATTERN_INIT_PAYLOAD,
)

_logger = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for scheduletracker."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._device = vol.UNDEFINED
        self._data = {"unique_id": None,"device": None,"config": None,}
        self._room_id = "undefined"

    async def async_step_mqtt(self, discovery_info: MqttServiceInfo) -> FlowResult:
        """Handle a flow initialized by MQTT discovery."""
        # if self._async_in_progress() or self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        payload = json.loads(discovery_info.payload)
        self._data["unique_id"] = payload["unique_id"]
        self._data["device"] = payload["device"]

        _logger.debug(
            "found device unique_id by mqtt: %s", self._data["unique_id"]
        )

        for entity in self._async_current_entries():
            if entity.unique_id == self._data["unique_id"]:
                self._abort_if_unique_id_configured()
                return self.async_abort(reason="already_configured")

        _logger.debug("discovery_info %s", discovery_info)

        return await self.async_step_settings()

    # async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
    #     """Handle a flow initialized by the user."""
    #     if self._async_in_progress() or self._async_current_entries():
    #         return self.async_abort(reason="single_instance_allowed")
    #     return self.async_abort(reason="not_allowed")

    async def async_step_user(  # test
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """test trigger entry"""
        if user_input is not None:
            self._data["unique_id"] = "test000"
            self._data["device"] = {
                "identifiers": "dummy",
                "manufacturer": "Tiastly",
                "model": "test000",
                "name": "test000",
                "sw_version": "2.0",
            }
            _logger.debug("test trigger entry")
            return await self.async_step_settings()
        return self.async_show_form(
                step_id="user"
        )
    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow device settings."""
        errors = {}
        if user_input is not None:
            if user_input["roomID"] in ROOM_LIST:
                self._data["config"] = dict(
                    zip(PATTERN_INIT_PAYLOAD, user_input.values())
                )
                self._room_id = user_input["roomID"]
                return await self.async_step_confirm()

            errors["base"] = "invalid room"
        # todo: selective room
        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required("roomID"):str,
                    vol.Required("roomtype"): vol.In(ROOM_TYPE),
                    vol.Required("delay", default=5): vol.All(
                        int, vol.Range(min=ATTR_DELAY_MIN, max=ATTR_DELAY_MAX)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_confirm(self, user_input=None) -> FlowResult:
        """Confirm the setup."""
        if self._data is not None:
            return self.async_create_entry(title=self._room_id, data=self._data)
        return self.async_abort(reason="no_data")

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._delay = config_entry.options.get("delay", 5)

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle init flow."""
        if user_input:
            if user_input.get("async_step_update_timedelay", False):
                return await self.async_step_update_timedelay()
            if user_input.get("async_step_add_sensors", False):
                return await self.async_step_add_sensors()
            if user_input.get("async_step_cmd", False):
                return await self.async_step_cmd()
        fields = {}
        fields[vol.Optional("async_step_update_timedelay")] = bool
        fields[vol.Optional("async_step_cmd")] = bool
        fields[vol.Optional("async_step_add_sensors")] = bool
        return self.async_show_form(step_id="init", data_schema=vol.Schema(fields))

    async def async_step_update_timedelay(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """update timedelay."""
        if user_input:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="update_timedelay",
            data_schema=vol.Schema(
                {
                    vol.Required("delay", default=self._delay): vol.All(
                        int, vol.Range(min=ATTR_DELAY_MIN, max=ATTR_DELAY_MAX)
                    ),
                }
            ),
        )

    async def async_step_add_sensors(self, user_input=None) -> FlowResult:
        """Manage to add other sensors."""
        all_sensors = []
        errors = {}
        # add some regex to filter out other sensors
        for sensor in self.hass.states.async_entity_ids("sensor"):
            _logger.debug(sensor)
            if not re.match(pattern = "sensor.*_(current|next)", string = sensor):
                all_sensors.append(sensor)
        all_sensors.sort()
        all_sensors.append("delete all sensors")
        if user_input:
            if len(user_input["sensor"]) > ATTR_SENSOR_MAX:
                errors["base"] = "too_many_sensors"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="add_sensors",
            data_schema=vol.Schema(
                {
                    vol.Required("sensor", default=[]): cv.multi_select(all_sensors),
                }
            ),
            errors=errors,
        )

    async def async_step_cmd(self,user_input = None)->FlowResult:
        """select cmd"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="cmd",
            data_schema=vol.Schema(
                {
                    vol.Required("cmd"): vol.In(CMD_TYPE),
                }
            )
        )