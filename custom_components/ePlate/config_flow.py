"""Config flow for ePlate."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

# import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from .const import (
    DOMAIN,
    CMD_TYPE,
    SUPPLY_TYPE,
    ATTR_DELAY,
    ATTR_SUPPLY,
    ATTR_ROOM_ID,
    ATTR_DELAY_MAX,
    ATTR_DELAY_MIN,
    ATTR_ROOM_TYPE,
    # ATTR_SENSOR_MAX,
    PATTERN_INIT_PAYLOAD,
)
from .roomlist import ROOM_LIST

_logger = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for scheduletracker."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._device = vol.UNDEFINED
        self._data = {
            "unique_id": None,
            "device": None,
            "config": PATTERN_INIT_PAYLOAD,
        }
        self._room_id = "undefined"

    async def async_step_mqtt(self, discovery_info: MqttServiceInfo) -> FlowResult:
        """Handle a flow initialized by MQTT discovery."""

        payload = json.loads(discovery_info.payload)
        self._data["unique_id"] = payload["unique_id"]
        self._data["device"] = payload["device"]

        _logger.debug("found device unique_id by mqtt: %s", self._data["unique_id"])

        for entity in self._async_current_entries():
            _logger.debug("entity.unique_id %s", entity.unique_id)
            if entity.unique_id == self._data["unique_id"]:
                self._abort_if_unique_id_configured()
                return self.async_abort(reason="already_configured")

        _logger.debug("discovery_info %s", discovery_info)

        return await self.async_step_setType()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manual Setup."""
        errors = {}
        if user_input is not None:
            if len(user_input["identifiers"]) == 4:
                self._data["unique_id"] = user_input["identifiers"]
                self._data["device"] = {
                    "identifiers": user_input["identifiers"],
                    "manufacturer": "Wareshare",
                    "model": "EPD7IN5",
                    "name": "1",
                    "sw_version": "1.0",
                }
                return await self.async_step_setType()
            errors["base"] = "invalid id"
            _logger.debug("user entry with %s", user_input["identifiers"])
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("identifiers"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_setType(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow device settings."""
        return self.async_show_menu(
            step_id="setType",
            menu_options=["setClass", "setOffice"],
            # description_placeholders={
            #     "model": "Example model",
            # }
        )

    async def async_step_setClass(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        if user_input is not None:
            self._room_id = user_input["roomID"]
            for sensor in self.hass.states.async_entity_ids("binary_sensor"):
                if re.match(f"binary_sensor.{self._room_id.lower()}_display", sensor):
                    errors["base"] = "sensor_exists"
                    break
            else:
                self._data["config"][ATTR_ROOM_TYPE] = 0
                self._data["config"][ATTR_ROOM_ID] = user_input["roomID"][:4]
                self._data["config"][ATTR_DELAY] = user_input["delay"]
                self._data["config"][ATTR_SUPPLY] = user_input["supply"]
                return await self.async_step_confirm()

        return self.async_show_form(
            step_id="setClass",
            data_schema=vol.Schema(
                {
                    vol.Required("roomID", default="A122"): vol.In(ROOM_LIST),
                    vol.Required("delay", default=5): vol.All(
                        int, vol.Range(min=ATTR_DELAY_MIN, max=ATTR_DELAY_MAX)
                    ),
                    vol.Required("supply", default=0): vol.In(SUPPLY_TYPE),
                }
            ),
            errors=errors,
        )

    async def async_step_setOffice(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        if user_input is not None:
            self._room_id = user_input["roomID"]
            for sensor in self.hass.states.async_entity_ids("binary_sensor"):
                if re.match(f"binary_sensor.{self._room_id.lower()}_display", sensor):
                    errors["base"] = "sensor_exists"
                    break
            else:
                if len(user_input["roomID"]) < 5:
                    self._data["config"][ATTR_ROOM_TYPE] = 1
                    self._data["config"][ATTR_ROOM_ID] = str(user_input["roomID"])
                    self._data["config"][ATTR_DELAY] = user_input["delay"]
                    self._data["config"][ATTR_SUPPLY] = user_input["supply"]
                    return await self.async_step_confirm()

                errors["base"] = "invalid room"

        return self.async_show_form(
            step_id="setOffice",
            data_schema=vol.Schema(
                {
                    vol.Required("roomID"): str,
                    vol.Required("delay", default=5): vol.All(
                        int, vol.Range(min=ATTR_DELAY_MIN, max=ATTR_DELAY_MAX)
                    ),
                    vol.Required("supply", default=0): vol.In(SUPPLY_TYPE),
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
        self._data = {
            "delay": config_entry.options.get("delay", 5),
            "sensor": config_entry.options.get("sensor", None),
            "cmd": None,
        }
        self._steps = []

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Handle init flow."""
        if user_input:
            if user_input.get("async_step_update_timedelay", False):
                self._steps.append(self.async_step_update_timedelay())
            if user_input.get("async_step_add_sensors", False):
                self._steps.append(self.async_step_add_sensors())
            if user_input.get("async_step_cmd", False):
                self._steps.append(self.async_step_cmd())

            if self._steps:
                self._steps.append(self.async_finish())
                return await self._steps.pop(0)

            return self.async_abort(reason="no_configurable_options")
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
            self._data["delay"] = user_input["delay"]
            return await self._steps.pop(0)
        return self.async_show_form(
            step_id="update_timedelay",
            data_schema=vol.Schema(
                {
                    vol.Required("delay", default=self._data["delay"]): vol.All(
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
            if not re.match(pattern="sensor.*_(current|next)", string=sensor):
                all_sensors.append(sensor)
        # all_sensors.sort()
        all_sensors.append("delete")
        # if user_input:
        #     if len(user_input["sensor"]) > ATTR_SENSOR_MAX:
        #         errors["base"] = "too_many_sensors"
        #     else:
        #         self._data["sensor"] = user_input["sensor"]
        #         return await self._steps.pop(0)

        # return self.async_show_form(
        #     step_id="add_sensors",
        #     data_schema=vol.Schema(
        #         {
        #             vol.Required(
        #                 "sensor", default=self._data["sensor"]
        #             ): cv.multi_select(all_sensors),
        #         }
        #     ),
        #     errors=errors,
        # )
        selected_sensors = dict(
            zip(
                ["sensor1", "sensor2", "sensor3"],
                self._data["sensor"] + [""] * (3 - len(self._data["sensor"]))
                if self._data["sensor"]
                else [""] * 3,
            )
        )
        sensor_data = []
        if user_input:
            for sensor in user_input.values():
                if sensor == "":
                    continue
                if sensor not in all_sensors:
                    errors["base"] = "not found"
                    break

                sensor_data.append(sensor)
            else:
                self._data["sensor"] = list(set(sensor_data))
                return await self._steps.pop(0)

        return self.async_show_form(
            step_id="add_sensors",
            data_schema=vol.Schema(
                {
                    vol.Required("sensor1", default=selected_sensors["sensor1"]): str,
                    vol.Optional("sensor2", default=selected_sensors["sensor2"]): str,
                    vol.Optional("sensor3", default=selected_sensors["sensor3"]): str,
                }
            ),
            errors=errors,
        )

    async def async_step_cmd(self, user_input=None) -> FlowResult:
        """select cmd."""
        if user_input is not None:
            self._data["cmd"] = user_input["cmd"]
            return await self._steps.pop(0)
        return self.async_show_form(
            step_id="cmd",
            data_schema=vol.Schema(
                {
                    vol.Required("cmd"): vol.In(CMD_TYPE),
                }
            ),
        )

    async def async_finish(self, user_input=None) -> FlowResult:
        """finish."""
        if self._data is not None:
            return self.async_create_entry(title="", data=self._data)
        return self.async_abort(reason="no_data")
