"""classroom platform."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    ATTR_LECT,
    ATTR_TIME,
    LECT_TYPE,
    ATTR_INFO,
    ATTR_DEFAULT_DELAY,
    PATTERN_PLAN_SUB_PAYLOAD,
)
from .scrap import ClassroomData

_logger = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """Setup sensors from a config entry created in the integrations UI."""
    data_package = hass.data[DOMAIN][entry.entry_id]
    device = data_package["device"]
    if device is None:
        return False

    session = async_get_clientsession(hass)
    classroom = ClassroomData(
        session=session,
        location=device.name,
        time_interval=ATTR_DEFAULT_DELAY / 2,
    )
    lectures = [
        LectureEntity(
            hass=hass,
            classroom=classroom,
            lect_type=lect,
            time_interval=timedelta(minutes=ATTR_DEFAULT_DELAY / 2),
            device=device,
            data_package=data_package,
        )
        for lect in LECT_TYPE
    ]
    for lect in lectures:
        await lect.async_update_lect()

    async_add_entities(lectures)
    _logger.debug("--------------init finished----------------------")
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
        self._attr_state = None  # updatetime
        self._lect_type = lect_type
        self._time_interval = time_interval
        self._attr_extra_state_attributes = {
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

    async def async_update_lect(self) -> None:
        """update the sensor infomations."""
        self._attr_state = self._data.now.strftime("%Y-%m-%d %H:%M:%S")
        await self._data.async_update()
        if self._lect_type == 0:
            self._attr_extra_state_attributes[ATTR_TIME] = self._data.rest_time
            self._attr_extra_state_attributes[ATTR_LECT] = self._data.curr_lecture
            self._attr_extra_state_attributes[ATTR_INFO] = self._data.curr_info
        elif self._lect_type == 1:
            self._attr_extra_state_attributes[ATTR_TIME] = self._data.begin_time
            self._attr_extra_state_attributes[ATTR_LECT] = self._data.next_lecture
            self._attr_extra_state_attributes[ATTR_INFO] = self._data.next_info
        self._data_package["payload"]["room"][LECT_TYPE[self._lect_type]] = dict(
            zip(
                PATTERN_PLAN_SUB_PAYLOAD.keys(),
                self._attr_extra_state_attributes.values(),
            )
        )

    def set_time_interval(self, hass, time_interval: timedelta):
        """Update scan interval."""

        async def refresh(event_time):
            await self.async_update_lect()

        async_track_time_interval(self._hass, refresh, self._time_interval)
