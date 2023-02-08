"""The scheduletracker integration."""
from __future__ import annotations
import json
import asyncio
import logging

# from .views import MediaPlayerThumbnailView
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_NAME, Platform

# from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN
from .coordinator import DeviceCoordinator
_LOGGER = logging.getLogger(__name__)


# todo if test input change state and immediate some service
async def text_listener(hass: HomeAssistant, entry: ConfigEntry, apis):
    ...


async def mqtt_publish():
    # ref https://github.com/home-assistant/example-custom-config/blob/master/custom_components/mqtt_basic_async/__init__.py
    ...


async def load_device_info(hass: HomeAssistant, entry: ConfigEntry):
    """first time add device"""
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        # identifiers=entry.data["device"]["identifiers"],
        identifiers={(DOMAIN, entry.unique_id)},  # NOT CHANGE!
        name=entry.data["config"]["room"],  # roomNr
        manufacturer=entry.data["device"]["manufacturer"],
        model=entry.data["device"]["model"],
        sw_version=entry.data["device"]["sw_version"],
    )
    if entry.data["config"]["room_type"] == 0:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, Platform.SENSOR)
        )
        # await hass.config_entries.async_setup_platforms(entry, PLATFORMS)
        _LOGGER.debug("loading %s device %s", Platform.SENSOR, device_registry)
        # todo basic_topic publish
    else:  # office
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, Platform.TEXT)
        )
        _LOGGER.debug("loading %s device %s", Platform.TEXT, device_registry)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    # hass.data[DOMAIN][entry.entry_id] = DeviceCoordinator(hass, entry=entry, device=dr.DeviceEntry)
    hass.data[DOMAIN].setdefault(
        entry.entry_id,
        {

            # "base_topic": "",
            # "base_topic_published": False,
            # "mqtt_topic": "",
            # "room_type": "",
            # "time_delay": "",
            # "other_sensor": {},

        },
    )
    if hass.data[DOMAIN][entry.entry_id] is not None:
        hass.data[DOMAIN][entry.entry_id][
            "base_topic"
        ] = f'/init/{entry.data["unique_id"]}'

        hass.data[DOMAIN][entry.entry_id]["base_topic_published"] = (False,)
        hass.data[DOMAIN][entry.entry_id][
            "mqtt_topic"
        ] = f'/{entry.data["config"]["room"]}/plan'
        hass.data[DOMAIN][entry.entry_id]["room_type"] = entry.data["config"][
            "room_type"
        ]
        hass.data[DOMAIN][entry.entry_id]["time_delay"] = entry.data["config"][
            "time_delay"
        ]
        # "other_sensor":{},

    # load device
    await load_device_info(hass, entry)

    # todo other sensor
    # entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True
    # hass.data[DOMAIN].setdefault(
    #     entry.entry_id,
    #     {"thumbnail": None, "loaded": False},
    # )

    # hass.async_create_task(
    #     handle_apis_changed(hass, entry, apis),
    # )
    # hass.data[DOMAIN][entry.entry_id]["apis"] = apis

    # device = entry.data["device"]["name"]

    # sub_state = hass.data[DOMAIN][entry.entry_id]["internal_mqtt"]

    # hass.data[DOMAIN][entry.entry_id]["internal_mqtt"] = sub_state


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, [Platform.SENSOR]
    )

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
    # loaded = hass.data[DOMAIN][entry.entry_id].get("loaded", None)

    # if loaded is not None:
    #     media_player = loaded.get("media_player", False)
    #     if media_player:
    #         if unload_ok := await hass.config_entries.async_unload_platforms(
    #             entry, [Platform.SENSOR]
    #         ):
    #             _LOGGER.debug("unloaded %s for %s", "media_player", entry.unique_id)
    # else:
    #     _LOGGER.warning("config entry (%s) with has no apis loaded?", entry.entry_id)


async def async_setup(hass: HomeAssistant, config) -> bool:
    # """Set up the MQTT async component."""
    # topic = config[DOMAIN][CONF_TOPIC]
    # entity_id = 'mqtt_linstener'

    # # Listen to a message on MQTT.
    # @callback
    # def message_received(topic: str, payload: str, qos: int) -> None:
    #     """A new MQTT message has been received."""
    #     hass.states.async_set(entity_id, payload)

    # await hass.components.mqtt.async_subscribe(topic, message_received)

    # hass.states.async_set(entity_id, 'No messages')

    # # Service to publish a message on MQTT.
    # @callback
    # def set_state_service(call: ServiceCall) -> None:
    #     """Service to send a message."""
    #     hass.components.mqtt.async_publish(topic, call.data.get('new_state'))

    # # Register our service with Home Assistant.
    # hass.services.async_register(DOMAIN, 'set_state', set_state_service)

    # Return boolean to indicate that initialization was successfully.
    return True
