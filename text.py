"""each room has description and qr-code"""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.text import TextEntity, TextEntityDescription

from .const import DOMAIN
from .coordinator import DeviceCoordinator

_logger = logging.getLogger(__name__)


# async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
#         """Set up Text entities."""
#         component = hass.data[DOMAIN] = EntityComponent[TextEntity](
#             _LOGGER, DOMAIN, hass, SCAN_INTERVAL
#         )
#         await component.async_setup(config)

#         component.async_register_entity_service(
#             SERVICE_SET_VALUE,
#             {vol.Required(ATTR_VALUE): cv.string},
#             async_set_value,
#         )

TEXT_TYPES = {
    "QR-Code": TextEntityDescription(
        key="QR-Code",
        name="QR-Code",
        native_min=1,
        native_max=50
    ),
    "description": TextEntityDescription(
    key="description",
    name="description",
    native_min=1,
    native_max=20
),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Setup sensors from a config entry created in the integrations UI"""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.unique_id)})

    if device is None:
        return False
    # coordinator: DeviceCoordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator = None
    async_add_entities(
        [
            BasicInfoText(
                coordinator=coordinator,
                entry_id=entry.entry_id,
                device=device,
                info_type=itype,
            )
            for itype in TEXT_TYPES
        ]
    )

    return True


class BasicInfoText(TextEntity):
    """save the description and qr-code of the room"""

    def __init__(self, coordinator, entry_id, device, info_type):
        self._device = device
        self._name = info_type
        self._attr_native_value = None
        self.entity_description = TEXT_TYPES[info_type]
        self._coordinator = coordinator
        # self._attr_device_info = coordinator.device_info
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
        return f"{self._device.name}_{self._name}"

    async def async_set_value(self, value: str) -> None:
        # self._coordinator.set_basic_info(self._name, value)
        self._attr_native_value = f"{self._name}, {value}"
