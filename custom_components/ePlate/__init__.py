"""The ePlate integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    ATTR_FRIENDLY_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_ROOM_ID,
    ATTR_ROOM_TYPE,
    ATTR_SENSOR_INFO,
    ATTR_SENSOR_TYPE,
    ATTR_SENSOR_UNIT,
    ATTR_SENSOR_NAME,
    DOMAIN,
    PATTERN_BASE,
    PATTERN_BASE_PAYLOAD,
    PATTERN_CMD_GLOBAL,
    PATTERN_DELAY,
    PATTERN_INIT,
    PATTERN_MEMBER,
    PATTERN_MEMBER_PAYLOAD,
    PATTERN_PLAN,
    PATTERN_PLAN_PAYLOAD,
    PATTERN_SENSOR,
    TOPIC_ID,
)

_logger = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.TEXT, Platform.BINARY_SENSOR]
PLATFORMS_E: list[Platform] = [
    Platform.BUTTON,
    Platform.TEXT,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up from yaml."""
    hass.data[DOMAIN] = {}
    return True


async def load_first_info(hass: HomeAssistant, entry: ConfigEntry):
    """first time add device."""
    device_registry = dr.async_get(hass)
    hass.data[DOMAIN][entry.entry_id]["device"] = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.data["device"]["identifiers"])},
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
                entry.data["config"],
                entry.options.get("delay", entry.data["config"]["delay"]),
                PATTERN_BASE_PAYLOAD,
                PATTERN_PLAN_PAYLOAD,
                dict.fromkeys(entry.options["sensor"])
                if entry.options.get("sensor", None)
                else None,
            ],
        )
    )
    # init topic publish
    await once_mqtt_publish(hass, row_topic=entry, row_payload="init", retain=False)
    # create entity
    change_publish_interval(
        hass, entry, timedelta(minutes=entry.data["config"]["delay"])
    )
    if entry.data["config"][ATTR_ROOM_TYPE] == 0:  # classroom
        _logger.debug("begin to load class device")
    elif entry.data["config"][ATTR_ROOM_TYPE] == 1:  # office
        _logger.debug("begin to load office device")
        hass.data[DOMAIN][entry.entry_id]["topic"]["room"] = PATTERN_MEMBER.format(
            roomID=room_id
        )
        hass.data[DOMAIN][entry.entry_id]["payload"]["room"] = PATTERN_MEMBER_PAYLOAD

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.BUTTON)
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    hass.data[DOMAIN].setdefault(
        entry.entry_id,
        {
            "unique_id": entry.data["unique_id"],
            "device": None,
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
    delay = entry.options.get("delay", data_package["payload"]["delay"])
    sensors = entry.options.get("sensor", None)
    cmd = entry.options.get("cmd", None)
    if delay != data_package["payload"]["delay"]:
        _logger.debug("delay changed to %s", delay)
        data_package["payload"]["delay"] = delay
        if hass.data[DOMAIN][entry.entry_id]["services"].get("timmer", None):
            hass.data[DOMAIN][entry.entry_id]["services"]["timmer"]()
        await once_mqtt_publish(
            hass=hass, row_topic=entry, row_payload="delay", retain=True
        )
        change_publish_interval(
            hass=hass, entry=entry, time_interval=timedelta(minutes=delay / 2)
        )
    elif (not data_package["payload"]["sensor"]) or (
        sensors != list(data_package["payload"]["sensor"].keys())
    ):
        # make the sensor to ailas
        _logger.debug("sensor%s", sensors)
        if "delete" in sensors:
            data_package["payload"]["sensor"] = None
            return
        _logger.debug("sensor changed to %s", sensors)
        data_package["payload"]["sensor"] = dict.fromkeys(sensors)
    # additional cmd control
    elif cmd:
        _logger.debug("cmd %s", PATTERN_CMD_GLOBAL[cmd - 1])
        await mqtt.async_publish(
            hass=hass,
            topic=PATTERN_CMD_GLOBAL[cmd - 1],
            payload="{on}",
            qos=0,
            retain=False,
        )


def change_publish_interval(
    hass: HomeAssistant, entry: ConfigEntry, time_interval: timedelta
):
    """Update publish_interval."""

    async def rountine_mqtt_publish(event_time):
        # lect and sensor data
        data_package = hass.data[DOMAIN][entry.entry_id]

        async def get_sensor_data(data_package):
            # update sensor information
            for sensor in data_package["payload"]["sensor"]:
                state = hass.states.get(sensor)
                if state is None:
                    continue
                data_package["payload"]["sensor"][sensor] = {
                    ATTR_SENSOR_INFO: str(state.state),
                    ATTR_SENSOR_UNIT: str(
                        state.attributes.get(ATTR_UNIT_OF_MEASUREMENT, None)
                    ),
                    ATTR_SENSOR_TYPE: state.attributes.get(ATTR_DEVICE_CLASS, None),
                    ATTR_SENSOR_NAME: state.attributes.get(ATTR_FRIENDLY_NAME, None),
                }

        if data_package["payload"]["init"][ATTR_ROOM_TYPE] == 0:  # classroom
            await once_mqtt_publish(
                hass, row_topic=entry, row_payload="room", retain=True
            )
        if data_package["payload"]["sensor"]:
            _logger.debug(data_package["payload"]["sensor"])
            await get_sensor_data(data_package)
            await once_mqtt_publish(
                hass, row_topic=entry, row_payload="sensor", retain=True
            )

    _logger.debug("change publish interval to %s", time_interval)
    hass.data[DOMAIN][entry.entry_id]["services"]["timmer"] = async_track_time_interval(
        hass, rountine_mqtt_publish, time_interval / 2
    )


async def once_mqtt_publish(
    hass: HomeAssistant, row_topic, row_payload, retain
) -> bool:
    """make a mqtt publish once."""
    entry, topic_id = row_topic, row_payload
    data_package = hass.data[DOMAIN][entry.entry_id]
    topic = data_package["topic"][topic_id]
    payload = payload_fix(data_package["payload"][topic_id], topic_id)
    _logger.debug("------publishing--------------------")
    _logger.debug("topic:%s", topic)
    _logger.debug("payload:%s", payload)
    _logger.debug("time:%s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        await mqtt.async_publish(
            hass=hass,
            topic=topic,
            payload=payload,
            qos=0,
            retain=retain,
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
        if entry.data["config"][ATTR_ROOM_TYPE] == 0:
            unload_ok = await hass.config_entries.async_unload_platforms(
                entry, PLATFORMS_E
            )
        elif entry.data["config"][ATTR_ROOM_TYPE] == 1:
            unload_ok = await hass.config_entries.async_unload_platforms(
                entry, PLATFORMS
            )
        for service in hass.data[DOMAIN][entry.entry_id]["services"].values():
            service()
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)

    except Exception as err:
        _logger.error(err)

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, entry.unique_id)},
    )

    if device is not None:
        device_registry.async_remove_device(device.id)

    return unload_ok


def payload_fix(payload, topid_id):
    """fix payload."""

    if topid_id in ["init", "delay"]:
        return payload
    if topid_id == "room":
        start = end = None
        if payload["next"]["rest/begin_time"]:
            start, end = payload["next"]["lect_info"].values()
        return {
            "classNow": str(payload["current"]["lectures"] or ""),
            "classNowRemainTime": str(payload["current"]["rest/begin_time"] or 0),
            "classNext": str(payload["next"]["lectures"] or ""),
            "classNextWaitTime": str(payload["next"]["rest/begin_time"] or 0),
            "classNextStartTime": str(start or ""),
            "classNextEndTime": str(end or ""),
        }
    if topid_id == "sensor":
        if payload:
            dump = {}
            for key, values in payload.items():
                info, unit, types, name = values.values()
                if unit == "°C" or "°F":
                    unit = unit[-1]
                if not types:
                    if name:
                        types = name
                    else:
                        types = key.strip("sensor.")
                dump.update(
                    {f"{types}": {ATTR_SENSOR_INFO: info, ATTR_SENSOR_UNIT: unit}}
                )
            return dump
        return None
