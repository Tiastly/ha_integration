"""classroo, sensor platform."""
from __future__ import annotations

import datetime
import logging
from typing import Any
from .scrap import ClassroomData
from .const import DOMAIN, ATTR_LECT, ATTR_INFO, ATTR_TIME, LectureType, SCAN_INTERVAL

from homeassistant.core import HomeAssistant

# ,callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback


import homeassistant.util.dt as dt_util
from homeassistant.util import Throttle

# from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)


"""
"now" should be replaced as dt.now(timezone.utc)
"""


SWEEP_TIME = datetime.timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Setup sensors from a config entry created in the integrations UI"""
    time_interval = entry.data["config"]["time_delay"]
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.unique_id)})

    if device is None:
        return False
    session = async_get_clientsession(hass)
    classroom = ClassroomData(
        session=session,
        location=device.name,
        time_interval=time_interval,
    )

    async_add_entities(
        [
            LectureEntity(
                hass=hass,
                classroom=classroom,
                lect_type=lect,
                time_interval=datetime.timedelta(minutes=time_interval),
                unique_id=entry.unique_id,
                entry_id=entry.entry_id,
                device=device,
            )
            for lect in LectureType
        ]
    )
    # dt.now(timezone.utc)
    return True


class LectureEntity(Entity):
    """each lecture+lecture_info+rest/beginTime"""

    def __init__(
        self,
        hass,
        classroom,
        lect_type,
        time_interval,
        unique_id,
        entry_id,
        device: dr.DeviceEntry,
    ):
        self._hass = hass
        self._entry_id = entry_id
        self._name = device.name
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "sw_version": device.sw_version,
        }

        self._data = classroom
        self._state = None  # updatetime
        self._lect_type = lect_type
        self._time_interval = time_interval
        self._attrs = {
            ATTR_LECT: "",
            ATTR_INFO: "",
            ATTR_TIME: "",
        }
        # self._update = Throttle(time_interval)(self.async_update)
        # self._update()

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return f"{self.name}"

    @property
    def name(self) -> str:
        return f"{self._data.locations}_{self._lect_type}"

    @property
    def state(self) -> str | None:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._attrs

    async def async_update(self) -> None:
        """update the sensor infomations"""

        @Throttle(self._time_interval)
        async def async_update_lect(self) -> None:
            await self._data.async_update()
            self._state = dt_util.now()
            if self._lect_type == "current_lecture":
                self._attrs[ATTR_LECT] = self._data.curr_lecture
                self._attrs[ATTR_INFO] = self._data.curr_info
                self._attrs[ATTR_TIME] = self._data.rest_time
            elif self._lect_type == "next_lecture":
                self._attrs[ATTR_LECT] = self._data.next_lecture
                self._attrs[ATTR_INFO] = self._data.next_info
                self._attrs[ATTR_TIME] = self._data.begin_time

        async def update_lect(call):
            await async_update_lect(call)

        self._hass.services.async_register(DOMAIN, "update_lect", update_lect)
