"""Config flow for scheduletracker."""
from __future__ import annotations
import json
import logging
import voluptuous as vol
from typing import Any

from homeassistant.core import callback
from homeassistant import config_entries
# from homeassistant.const import (ATTR_DISCOVERY_TOPIC,CONF_TOPIC)
from homeassistant.data_entry_flow import FlowResult
# from homeassistant.components.mqtt import ReceiveMessage, valid_subscribe_topic
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from .const import DOMAIN, CONF_CONTROLLER
from .roomlist import ROOM_LIST

_LOGGER = logging.getLogger(__name__)

ROOM_TYPE = {0: "classroom type", 1: "office type"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._device = vol.UNDEFINED
        self._data = {"unique_id":None,"device": None, "config": None}

    # TODO how to trigger?
    async def async_step_mqtt(self, discovery_info: MqttServiceInfo) -> FlowResult:
        """Handle a flow initialized by MQTT discovery."""
        if self._async_in_progress() or self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        device = discovery_info.topic.split("init/devices/")[1]
        payload = json.loads(discovery_info.payload)
        self._data["unique_id"] = payload["unique_id"]

        _LOGGER.debug("found device. Name: %s, unique_id: %s", device, self._data["unique_id"])

        self._data["device"] = payload["dev"]
        for entity in self._async_current_entries():
            if entity.unique_id == self._data["unique_id"]:
                self._abort_if_unique_id_configured()
                return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(self._data["unique_id"])
        # assert discovery_info.subscribed_topic == "init/devices//#"
        _LOGGER.debug("discovery_info %s", discovery_info)
        self._device = device
        return await self.async_step_settings()

    async def async_step_user(  # user add integration
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._device = user_input.get(CONF_CONTROLLER)
            self._data["unique_id"] = "test001"
            self._data["device"] = {
                "identifiers":"dummy",
                "manufacturer": "DUMMY",
                "model": "model",
                "name": "test000",
                "sw_version": "1.0",
            }
            return await self.async_step_settings()

        all_devices = [
            device
            for device in self.hass.states.async_entity_ids("sensor")
        ]
        controller_options = sorted(all_devices)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_CONTROLLER): vol.In(controller_options)}
            ),
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow device settings."""
        errors = {}
        if user_input is not None:
            _LOGGER.debug(user_input)

            if user_input["room"] in ROOM_LIST:
                self._data["config"] = {
                    "room": user_input["room"],
                    "room_type": user_input["roomtype"],
                    "time_delay": user_input["time_delay"],
                }
                return await self.async_step_confirm()
            else:
                errors["base"] = "invalid room"

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    vol.Required("room"): str,
                    vol.Required("roomtype"): vol.In(ROOM_TYPE),
                    vol.Required("time_delay", default=5): vol.All(
                        int, vol.Range(min=1, max=30)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_confirm(self, user_input=None) -> FlowResult:
        """Confirm the setup."""
        return self.async_create_entry(title=DOMAIN, data=self._data)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


# TODO add other sensor
class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    # async def async_step_init(
    #     self, user_input: dict[str, Any] | None = None
    # ) -> FlowResult:
    #     """Manage the options."""
    #     if user_input is not None:
    #         user_input[CONF_DEFAULT_NOTIFICATION_TITLE] = user_input[
    #             CONF_DEFAULT_NOTIFICATION_TITLE
    #         ].strip()

    #         return self.async_create_entry(title="", data=user_input)

    #     return self.async_show_form(
    #         step_id="init",
    #         data_schema=vol.Schema(
    #             {
    #                 vol.Optional(
    #                     CONF_DEFAULT_NOTIFICATION_TITLE,
    #                     default=self.config_entry.options.get(
    #                         CONF_DEFAULT_NOTIFICATION_TITLE, ATTR_TITLE_DEFAULT
    #                     ),
    #                 ): str
    #             }
    #         ),
    #     )


# config_entry_flow.register_discovery_flow(DOMAIN, "scheduletracker", _async_has_devices)
