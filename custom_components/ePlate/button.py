"""each room can use cmd control."""
import logging

from homeassistant.components import mqtt
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ATTR_ROOM_ID,
    PATTERN_CMD,
)

_logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Setup cmd_control from a config entry created in the integrations UI."""
    data_package = hass.data[DOMAIN][entry.entry_id]
    device = data_package["device"]
    if device is None:
        return False
    async_add_entities(
        [
            CMD_Control(
                hass=hass,
                device=device,
                roomID=entry.data["config"][ATTR_ROOM_ID],
                cmd_topic = topic
            )for topic in PATTERN_CMD
        ]
    )
    # continue to add base info text
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.TEXT)
    )

    return True

class CMD_Control(ButtonEntity):
    """use button to send cmd to device."""
    def __init__(self, hass, device, roomID,cmd_topic) -> None:
        """Initialize the text."""
        self._hass = hass
        self._device = device
        self._topic = cmd_topic.format(roomID=roomID)
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "sw_version": device.sw_version,
        }

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self.name}"

    @property
    def name(self) -> str:
        return f"{self._device.name}_{self._topic.rsplit('/', maxsplit=1)[-1]}"

    async def async_press(self) -> None:
        try:
            await mqtt.async_publish(
                hass=self._hass,
                topic=self._topic,
                payload="{on}",
                qos=0,
                retain=False,
            )
        except Exception as err:
            _logger.error(err)
