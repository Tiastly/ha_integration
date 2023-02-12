"""The ePlate integration."""
from __future__ import annotations
import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_interval
from .const import (
    DOMAIN,
    TOPIC_ID,
    ATTR_ROOM_ID,
    ATTR_ROOM_TYPE,
    PATTERN_INIT,
    PATTERN_DELAY,
    PATTERN_BASE,
    PATTERN_PLAN,
    PATTERN_MEMBER,
    PATTERN_SENSOR,
    PATTERN_INIT_PAYLOAD,
    PATTERN_BASE_PAYLOAD,
    PATTERN_PLAN_PAYLOAD,
    PATTERN_MEMBER_PAYLOAD,
    # PATTERN_SENSOR_PAYLOAD,
)

_logger = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.TEXT]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up from yaml."""
    hass.data[DOMAIN] = {}
    return True


async def load_first_info(hass: HomeAssistant, entry: ConfigEntry):
    """first time add device"""
    device_registry = dr.async_get(hass)
    hass.data[DOMAIN][entry.entry_id]["device"] = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["device"]["identifiers"])},  # NOT CHANGE!
        #identifiers={(DOMAIN, str(entry.unique_id)+"_"+entry.data["device"]["identifiers"])},
        name=entry.data["config"][ATTR_ROOM_ID],  # roomNr
        manufacturer=entry.data["device"]["manufacturer"],
        model=entry.data["device"]["model"],
        sw_version=entry.data["device"]["sw_version"],
    )
    unique_id = entry.data["unique_id"]
    room_id = entry.data["config"][ATTR_ROOM_ID]

    # general setting
    hass.data[DOMAIN][entry.entry_id]["topic"] = dict(
        zip(
            TOPIC_ID,
            [
                PATTERN_INIT.format(unique_id=unique_id),
                PATTERN_DELAY.format(roomID=room_id),
                PATTERN_BASE.format(roomID=room_id),
                PATTERN_PLAN.format(roomID=room_id),
                PATTERN_SENSOR.format(roomID=room_id),
            ],
        )
    )
    hass.data[DOMAIN][entry.entry_id]["payload"] = dict(
        zip(
            TOPIC_ID,
            [
                entry.data["config"],  # init payload
                int,  # delay payload
                PATTERN_BASE_PAYLOAD,
                PATTERN_PLAN_PAYLOAD,
                None,  # sensor payload
            ],
        )
    )
    # init topic publish
    await once_mqtt_publish(hass, entry, "init")

    # create entity
    if entry.data["config"][ATTR_ROOM_TYPE] == 0:  # classroom
        _logger.debug("loading class device %s", device_registry)
        PLATFORMS.append(Platform.SENSOR)
        change_publish_interval(
            hass, entry, timedelta(minutes=entry.data["config"]["delay"])
        )# only classroom need routine publish
    else:  # office
        _logger.debug("loading office device %s", device_registry)
        hass.data[DOMAIN][entry.entry_id]["topic"]["room"] = PATTERN_MEMBER.format(
            roomID=room_id
        )
        hass.data[DOMAIN][entry.entry_id]["payload"]["room"] = PATTERN_MEMBER_PAYLOAD

    # firstly add base info text
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.TEXT)
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data[DOMAIN].setdefault(
        entry.entry_id,
        {
            "unique_id": entry.data["unique_id"],
            "device": None,
            # "topic_id": dict.fromkeys(TOPIC_ID),
            "topic": {},
            "payload": {},
            "services": {},
        },
    )
    # load device
    hass.data[DOMAIN][entry.entry_id]["services"][
        "options_listener"
    ] = entry.add_update_listener(options_listener)

    await load_first_info(hass, entry)

    return True


async def options_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    data_package = hass.data[DOMAIN][entry.entry_id]
    delay = entry.options.get("delay", None)
    sensors = entry.options.get("sensor", None)
    if delay:
        _logger.debug("delay changed to %s", delay)
        data_package["payload"]["delay"] = delay
        if hass.data[DOMAIN][entry.entry_id]["services"].get("timmer",None):
            hass.data[DOMAIN][entry.entry_id]["services"]["timmer"]()
        await once_mqtt_publish(hass=hass, entry=entry, topic_id="delay")
        change_publish_interval(
            hass=hass, entry=entry, time_interval=timedelta(minutes=delay)
        )
    if sensors:
        # make the sensor to ailas
        _logger.debug("sensor changed to %s", sensors)
        data_package["payload"]["sensor"] = dict.fromkeys(sensors)


def change_publish_interval(
    hass: HomeAssistant, entry: ConfigEntry, time_interval: timedelta
):
    """Update publish_interval."""

    async def rountine_mqtt_publish(event_time):
        # lect and sensor data
        data_package = hass.data[DOMAIN][entry.entry_id]

        async def get_sensor_data(data_package):
            # update sensor information
            for sensor in data_package["payload"]["sensor"].keys():
                data_package["payload"]["sensor"][sensor] = hass.states.get(
                    sensor
                ).state

        if data_package["payload"]["init"][ATTR_ROOM_TYPE] == 0:  # classroom
            await once_mqtt_publish(hass, entry, "room")
        if data_package["payload"]["sensor"]:
            data_package["payload"]["sensor"] = await get_sensor_data(data_package)
            await once_mqtt_publish(hass, entry, "sensor")
    _logger.debug("change publish interval to %s", time_interval)
    hass.data[DOMAIN][entry.entry_id]["services"]["timmer"] = async_track_time_interval(
        hass, rountine_mqtt_publish, time_interval
    )


async def once_mqtt_publish(hass: HomeAssistant, entry: ConfigEntry, topic_id) -> bool:
    """make a mqtt publish once."""
    data_package = hass.data[DOMAIN][entry.entry_id]
    _logger.debug("publishing %s", data_package["topic"][topic_id])
    try:
        await mqtt.async_publish(
            hass=hass,
            topic=data_package["topic"][topic_id],
            payload=payload_fix(data_package["payload"][topic_id], topic_id),
            qos=0,
            retain=False,
        )
        return True
    except Exception as err:
        _logger.error(err)
    return False


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, PLATFORMS
        )
        # Remove all services.
        for service in hass.data[DOMAIN][entry.entry_id]["services"].values():
            service()

        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)

    except ValueError:
        pass

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, entry.unique_id)},
    )

    if device is not None:
        device_registry.async_remove_device(device.id)

    return unload_ok


def payload_fix(payload, topid_id):
    """fix payload"""
    if topid_id in ["init", "delay"]:
        return payload
    if topid_id == "room":
        start = end = None
        if payload["next"]["rest/begin_time"]:
            start, end = payload["current"]["rest/begin_time"].values()
        return {
            "classNow": payload["current"]["lectures"],
            "classNowRemainTime": payload["current"]["rest/begin_time"],
            "classNext": payload["next"]["lectures"],
            "classNextWaitTime": payload["next"]["rest/begin_time"],
            "classNextStartTime": start,
            "classNextEndTime": end,
        }
    if topid_id == "sensor":
        if payload:
            dump = {}
            i = 1
            for key, value in payload.items():
                dump.update({f"sensor{i}": {"name": key, "info": value}})
                i += 1
            return dump
        # if sensor is empty
        return None
