"""classroom platform."""
from __future__ import annotations

from datetime import timedelta, timezone
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_DELAY_MIN,
    ATTR_INFO,
    ATTR_LECT,
    ATTR_TIME,
    DOMAIN,
    LECT_TYPE,
    PATTERN_PLAN_SUB_PAYLOAD,
    TIME_SHIFT,
)
from .scrap import ClassroomData

_logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Setup sensors from a config entry created in the integrations UI."""
    data_package = hass.data[DOMAIN][entry.entry_id]
    device = data_package["device"]
    # delay = data_package["payload"][TOPIC_ID[0]][ATTR_DELAY]
    delay = ATTR_DELAY_MIN
    if device is None:
        return False
    session = async_get_clientsession(hass)
    classroom = ClassroomData(
        session=session,
        location=device.name,
        time_interval=delay,
    )
    lectures = [
        LectureEntity(
            hass=hass,
            classroom=classroom,
            lect_type=lect,
            time_interval=timedelta(minutes=delay),
            device=device,
            data_package=data_package,
        )
        for lect in LECT_TYPE
    ]
    for lect in lectures:
        await lect.async_update_lect()
        
    async_add_entities(lectures)
    _logger.debug("init sensor finished")
    return True


class LectureEntity(Entity):
    """each lecture+lecture_info+rest/beginTime."""

    def __init__(
        self,
        hass: HomeAssistant,
        classroom,
        lect_type,
        time_interval,
        device,
        data_package,
    ):
        self._hass = hass
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "sw_version": device.sw_version,
        }
        self._device = device
        self._data_package = data_package
        self._data = classroom
        self._state = None  # updatetime
        self._lect_type = lect_type
        self._time_interval = time_interval
        self._attrs = {
            ATTR_LECT: None,
            ATTR_INFO: None,
            ATTR_TIME: None,
        }
        self.set_time_interval(hass, self._time_interval)

    @property
    def unique_id(self) -> str:
        return self.name

    @property
    def name(self) -> str:
        return f"{self._device.name}_{LECT_TYPE[self._lect_type]}"

    @property
    def state(self) -> str | None:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self._attrs

    async def async_update_lect(self) -> None:
        """update the sensor infomations."""
        await self._data.async_update()
        self._state = dt_util.now(timezone(offset=TIME_SHIFT)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        # self._state = self._data.now_time#update time
        if self._lect_type == 0:
            self._attrs[ATTR_TIME] = self._data.rest_time
            self._attrs[ATTR_LECT] = self._data.curr_lecture
            self._attrs[ATTR_INFO] = self._data.curr_info
        elif self._lect_type == 1:
            self._attrs[ATTR_TIME] = self._data.begin_time
            self._attrs[ATTR_LECT] = self._data.next_lecture
            self._attrs[ATTR_INFO] = self._data.next_info
        self._data_package["payload"]["room"][LECT_TYPE[self._lect_type]] = dict(
            zip(PATTERN_PLAN_SUB_PAYLOAD.keys(), self._attrs.values())
        )

    def set_time_interval(self, hass, time_interval: timedelta):
        """Update scan interval."""

        async def refresh(event_time):
            await self.async_update_lect()

        async_track_time_interval(self._hass, refresh, self._time_interval)
