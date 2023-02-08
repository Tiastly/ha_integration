"""Coordinator for all the sensors."""
from __future__ import annotations

import datetime
import logging

# from home_assistant_bluetooth import BluetoothServiceInfoBleak
# from homeassistant.components.bluetooth import (
#     BluetoothCallbackMatcher,
#     BluetoothChange,
#     BluetoothScanningMode,
#     async_register_callback,
#     async_track_unavailable,
# )
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback

# from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


_logger = logging.getLogger(__name__)


class DeviceCoordinator(DataUpdateCoordinator):
    """Define an object to hold Fully Kiosk Browser data."""
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: str,
        include_extra: bool = False,
    ) -> None:
        """Initialize."""
        self._hass = hass
        super().__init__(
            hass,
            logger=_logger,
            name=f"{device.name}-DeviceCoordinator",
            update_interval=datetime.timedelta(
                minutes=entry.data["config"]["time_delay"]
            ),
        )

        self._device = device
        self._payload = {}
        # self.available = False
        # self.last_updated: datetime | None = None
        # self._updating = asyncio.Lock()
        self._cancel_track_unavailable: CALLBACK_TYPE | None = None
        self._cancel_bluetooth_advertisements: CALLBACK_TYPE | None = None
        _logger.info(f" {self.name} Setup")

    def set_basic_info(self, name, value) -> None:
        """put basic info into payload"""
        self._payload[name] = value

    @property
    def device_info(self):
        """Return information about the device."""
        return DeviceInfo(
            identifiers = self._device.identifiers,
            name =self._device.name,
            manufacturer = self._device.manufacturer,
            model = self._device.model,
            sw_version =self._device.sw_version,
        )

        # return {
        #     "identifiers": self._device.identifiers,
        #     "name": self._device.name,
        #     "manufacturer": self._device.manufacturer,
        #     "model": self._device.model,
        #     "sw_version": self._device.sw_version,
        # }

    async def mqtt_publisch(self) -> bool:
        pass
