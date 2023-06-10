"""classroom platform."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.mqtt.subscription import (
    async_prepare_subscribe_topics,
    async_subscribe_topics,
    async_unsubscribe_topics,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_ROOM_TYPE, DOMAIN, PATTERN_STATE

_logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Setup sensors from a config entry created in the integrations UI."""
    data_package = hass.data[DOMAIN][entry.entry_id]
    device = data_package["device"]
    room_type = data_package["payload"]["init"][ATTR_ROOM_TYPE]
    if device is None:
        return False
    async_add_entities(
        [
            DeviceSensor(
                hass=hass,
                device=device,
            )
        ]
    )

    if room_type == 0:  # contiue to add lecture
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, Platform.SENSOR)
        )
    else:
        _logger.debug("--------------init finished----------------------")
    return True


class DeviceSensor(BinarySensorEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        device,
    )->None:
        self._hass = hass
        self._device = device
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "sw_version": device.sw_version,
        }
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_is_on = True
        self._listeners = {}

    @property
    def unique_id(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return f"{self._device.name}_display"

    async def async_added_to_hass(self) -> None:
        """Subscribe to device status."""

        @callback
        def update(message) -> None:
            """update status."""
            _logger.debug("update device status%s", message.payload)
            if message.payload == "online":
                self._attr_is_on = True
            elif message.payload == "offline":
                self._attr_is_on = False
            else:
                assert False, f"unknown satatus {message.payload}"

        self._listeners = async_prepare_subscribe_topics(
            self.hass,
            self._listeners,
            {
                f"{self.unique_id}-state": {
                    "topic": PATTERN_STATE.format(roomID=self._device.name),
                    "msg_callback": update,
                    "qos": 0,
                },
            },
        )

        await async_subscribe_topics(self.hass, self._listeners)

    async def async_will_remove_from_hass(self) -> None:
        if self._listeners is not None:
            async_unsubscribe_topics(self.hass, self._listeners)
