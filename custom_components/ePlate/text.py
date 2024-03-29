"""each room has description and qr-code."""
import logging
import re
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.text import RestoreText, TextEntityDescription,TextExtraStoredData
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_DEFAULT_TEXT,
    ATTR_DIS,
    ATTR_MAIL,
    ATTR_MEMBER_MAX,
    ATTR_MSG,
    ATTR_MSG_INFO,
    ATTR_MSG_TITLE,
    ATTR_NAME,
    ATTR_QR,
    ATTR_ROOM_TYPE,
    ATTR_TEL,
    DOMAIN,
    PATTERN_BASE_PAYLOAD,
    PATTERN_MEMBER_PAYLOAD,
    PATTERN_MSG,
    PATTERN_MSG_PAYLOAD,
)

_logger = logging.getLogger(__name__)


TEXT_TYPES = {
    ATTR_QR: TextEntityDescription(
        key=ATTR_QR, name=ATTR_QR, native_min=0, native_max=50
    ),
    ATTR_DIS: TextEntityDescription(
        key=ATTR_DIS, name=ATTR_DIS, native_min=0, native_max=50
    ),
    ATTR_NAME: TextEntityDescription(
        key=ATTR_NAME, name=ATTR_NAME, native_min=0, native_max=40
    ),
    ATTR_TEL: TextEntityDescription(
        key=ATTR_TEL, name=ATTR_TEL, native_min=0, native_max=30
    ),
    ATTR_MAIL: TextEntityDescription(
        key=ATTR_MAIL, name=ATTR_MAIL, native_min=0, native_max=40
    ),
    ATTR_MSG: TextEntityDescription(
        key=ATTR_MSG, name=ATTR_MSG, native_min=0, native_max=30
    ),
    ATTR_MSG_TITLE: TextEntityDescription(
        key=ATTR_MSG_TITLE, name=ATTR_MSG_TITLE, native_min=0, native_max=20
    ),
    ATTR_MSG_INFO: TextEntityDescription(
        key=ATTR_MSG_INFO, name=ATTR_MSG_INFO, native_min=0, native_max=90
    ),
}


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
            BasicInfoText(
                hass=hass,
                device=device,
                info_type=itype,
                data_package=data_package,
            )
            for itype in PATTERN_BASE_PAYLOAD
        ]
    )

    if room_type == 1:  # contiue to add member
        for member_bit in range(1, ATTR_MEMBER_MAX + 1):
            async_add_entities(
                [
                    MemberInfoText(
                        hass=hass,
                        device=device,
                        info_type=itype,
                        member_bit=f"member{member_bit}",
                        data_package=data_package,
                    )
                    for itype in PATTERN_MEMBER_PAYLOAD[f"member{member_bit}"]
                ]
            )
        async_add_entities(
            [
                MSGInfoText(
                    hass=hass,
                    device=device,
                    info_type=itype,
                    data_package=data_package,
                )
                for itype in PATTERN_MSG_PAYLOAD
            ]
        )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.BINARY_SENSOR)
    )
    return True


class InfoText(RestoreText):
    """parent class for all text entities."""

    def __init__(self, hass, device, info_type, data_package) -> None:
        """Initialize the text."""
        self._hass = hass
        self._device = device
        self._info_type = info_type
        self._data_package = data_package
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "sw_version": device.sw_version,
        }
        self._attr_native_value: Any

        self.entity_description = TEXT_TYPES[self._info_type]

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.name}"

    @property
    def name(self) -> str:
        return f"{self._device.name}_{self._info_type}"

    async def async_added_to_hass(self):
        """wenn restart, restore the state."""
        await super().async_added_to_hass()
        last_text = await self.async_get_last_text_data()
        if last_text and last_text.native_value != '':
            self._attr_native_value = last_text.native_value
        else:
            self._attr_native_value = ATTR_DEFAULT_TEXT

    async def async_will_remove_from_hass(self) -> None:
        """Remove the entity."""
        await super().async_will_remove_from_hass()
        self._attr_native_value = ''

class BasicInfoText(InfoText):
    """save the description and qr-code of the room."""

    async def async_set_value(self, value: str) -> None:
        # when the value changed, make the mqtt publish
        self._attr_native_value = value
        try:
            self._data_package["payload"]["base"][self._info_type] = value
            await mqtt.async_publish(
                hass=self._hass,
                topic=self._data_package["topic"]["base"],
                payload=self._data_package["payload"]["base"],
                qos=0,
                retain=True,
            )
        except Exception as err:
            _logger.error(err)


class MSGInfoText(InfoText):
    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value
        try:
            self._data_package["payload"]["room"]["message"][self._info_type] = value
            await mqtt.async_publish(
                hass=self._hass,
                topic=PATTERN_MSG.format(roomID=self._attr_device_info["name"]),
                payload=self._data_package["payload"]["room"]["message"],
                qos=0,
                retain=True,
            )
        except Exception as err:
            _logger.error(err)


class MemberInfoText(InfoText):
    """save the memberinfo of the office."""

    def __init__(self, hass, device, info_type, member_bit, data_package) -> None:
        """Initialize the text."""
        super().__init__(hass, device, info_type, data_package)
        self._member_bit = member_bit

    @property
    def name(self) -> str:
        return f"{self._device.name}_{self._member_bit}_{self._info_type}"

    async def async_set_value(self, value: str) -> None:
        #if self._info_type == ATTR_TEL and not re.match(
         #   pattern="^[0-9]*$", string=value
        #):
         #   raise ValueError("invalid tel")
        if self._info_type == ATTR_MAIL and not re.match(
            pattern="^\\w+([-+.]\\w+)*@\\w+([-.]\\w+)*\\.\\w+([-.]\\w+)*$", string=value
        ):
            raise ValueError("invalid mail")
        self._attr_native_value = value
        member = self._data_package["payload"]["room"][self._member_bit]
        member[self._info_type] = value
        _logger.debug({self._member_bit: member})
        try:
            await mqtt.async_publish(
                hass=self._hass,
                topic=self._data_package["topic"]["room"] + "/" + self._member_bit,
                payload={self._member_bit: member},
                qos=0,
                retain=True,
            )
        except Exception as err:
            _logger.error(err)
