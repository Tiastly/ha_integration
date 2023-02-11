"""each room has description and qr-code"""
import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.components import mqtt
from homeassistant.components.text import TextEntity, TextEntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import (
    DOMAIN,
    ATTR_ROOM_TYPE,
    ATTR_QR,
    ATTR_DIS,
    ATTR_NAME,
    ATTR_TEL,
    ATTR_MAIL,
    ATTR_MSG,
    PATTERN_BASE_PAYLOAD,
    PATTERN_MEMBER_PAYLOAD,
    # ATTR_DELAY,
    # ATTR_DELAY_MIN,
    # ATTR_DELAY_MAX,
)

_logger = logging.getLogger(__name__)


TEXT_TYPES = {
    # ATTR_DELAY: TextEntityDescription(
    #     key=ATTR_DELAY, name=ATTR_DELAY, native_min=ATTR_DELAY_MIN, native_max=ATTR_DELAY_MAX,
    # ),
    ATTR_QR: TextEntityDescription(
        key=ATTR_QR, name=ATTR_QR, native_min=0, native_max=50
    ),
    ATTR_DIS: TextEntityDescription(
        key=ATTR_DIS, name=ATTR_DIS, native_min=0, native_max=20
    ),
    ATTR_NAME: TextEntityDescription(
        key=ATTR_NAME, name=ATTR_NAME, native_min=1, native_max=20
    ),
    ATTR_TEL: TextEntityDescription(
        key=ATTR_TEL, name=ATTR_TEL, native_min=0, native_max=20
    ),
    ATTR_MAIL: TextEntityDescription(
        key=ATTR_MAIL, name=ATTR_MAIL, native_min=0, native_max=20
    ),
    ATTR_MSG: TextEntityDescription(
        key=ATTR_MSG, name=ATTR_MSG, native_min=0, native_max=50
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Setup sensors from a config entry created in the integrations UI"""
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

    if room_type == 0:  # contiue to add lecture
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, Platform.SENSOR)
        )
    elif room_type == 1:  # contiue to add member
        async_add_entities(
            [
                MemberInfoText(
                    hass=hass,
                    device=device,
                    info_type=itype,
                    data_package=data_package,
                )
                for itype in PATTERN_MEMBER_PAYLOAD["member1"]
            ]
        )
    return True


class InfoText(TextEntity):
    """parent class for all text entities"""

    def __init__(self, hass, device, info_type: str, data_package) -> None:
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
        self.entity_description = TEXT_TYPES[self._info_type]

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return None

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self.name}"

    @property
    def name(self) -> str:
        return f"{self._device.name}_{self._info_type}"


class BasicInfoText(InfoText):
    """save the description and qr-code of the room"""

    async def async_set_value(self, value: str) -> None:
        # when the value changed, make the mqtt publish
        self._data_package["payload"]["base"][self._info_type] = value
        # self._data_package["topic_id"]["base"] = 1
        try:
            await mqtt.async_publish(
                hass=self._hass,
                topic=self._data_package["topic"]["base"],
                payload=self._data_package["payload"]["base"],
                qos=0,
                retain=False,
            )
        except Exception as err:
            _logger.error(err)
            # self._data_package["topic_id"]["base"] = 0


# todo need to improve the data structure
class MemberInfoText(InfoText):
    """save the memberinfo of the office"""

    async def async_set_value(self, value: str) -> None:
        """TOPIC_ID[3] = "member" """
        # for member in self._data_package["payload"]["room"]:
        #     if member[PATTERN_MEMBER_PAYLOAD[self._info_type]] != str:
        #         member[PATTERN_MEMBER_PAYLOAD[self._info_type]] = value
        #         break
        # # self._data_package["payload"][TOPIC_ID[3]][self._info_type] = value
        self._data_package["topic_id"]["room"] = 1