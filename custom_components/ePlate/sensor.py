"""classroom platform."""
from __future__ import annotations

import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.components import mqtt
from homeassistant.components.mqtt.subscription import (
    async_prepare_subscribe_topics,
    async_subscribe_topics,
    async_unsubscribe_topics,
)
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)

from .const import (
    ATTR_DELAY_MIN,
    ATTR_ROOM_TYPE,
    ATTR_INFO,
    ATTR_LECT,
    ATTR_TIME,
    DOMAIN,
    LECT_TYPE,
    PATTERN_PLAN_SUB_PAYLOAD,
    PATTERN_STATE,
)
from .scrap import ClassroomData

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
        session = async_get_clientsession(hass)
        classroom = ClassroomData(
            session=session,
            location=device.name,
            time_interval=ATTR_DELAY_MIN,
        )
        lectures = [
            LectureEntity(
                hass=hass,
                classroom=classroom,
                lect_type=lect,
                time_interval=timedelta(minutes=ATTR_DELAY_MIN),
                device=device,
                data_package=data_package,
            )
            for lect in LECT_TYPE
        ]
        for lect in lectures:
            await lect.async_update_lect()

        async_add_entities(lectures)
    _logger.debug("init finished")
    return True


class DeviceSensor(BinarySensorEntity):
    def __init__(
        self,
        hass: HomeAssistant,
        device,
    ):
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
        def update(message)->None:
            """update status."""
            _logger.debug("update %s",message.payload)
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
                    "topic": PATTERN_STATE.format(roomID = self._device.name),
                    "msg_callback": update,
                    "qos": 0,
                },
            },
        )

        await async_subscribe_topics(self.hass, self._listeners)


    async def async_will_remove_from_hass(self) -> None:
        if self._listeners is not None:
            async_unsubscribe_topics(self.hass, self._listeners)

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
    def extra_state_attributes(self) -> dict[str]:
        return self._attrs

    async def async_update_lect(self) -> None:
        """update the sensor infomations."""
        await self._data.async_update()
        self._state = self._data.now.strftime("%Y-%m-%d %H:%M:%S")
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
