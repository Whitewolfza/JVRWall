"""JVRWall family dashboard integration."""
from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import (
    CARD_URL,
    COMPANION_URL,
    DAYS,
    DOMAIN,
    MEAL_SLOTS,
    SIGNAL_UPDATED,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .data import JVRWallData

PLATFORMS = ["sensor"]


class JVRWallManager:
    """Owns the data and persists it."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data = JVRWallData()

    async def async_load(self) -> None:
        self.data = JVRWallData(await self.store.async_load())

    async def async_changed(self) -> None:
        await self.store.async_save(self.data.as_dict())
        async_dispatcher_send(self.hass, SIGNAL_UPDATED)


SERVICES = {
    "set_meal": (
        vol.Schema(
            {
                vol.Required("day"): vol.In(DAYS),
                vol.Required("meal"): cv.string,
                vol.Optional("slot", default="dinner"): vol.In(MEAL_SLOTS),
            }
        ),
        lambda d, c: d.set_meal(c["day"], c["meal"], c["slot"]),
    ),
    "add_shopping_item": (
        vol.Schema({vol.Required("name"): cv.string}),
        lambda d, c: d.add_shopping_item(c["name"]),
    ),
    "check_shopping_item": (
        vol.Schema(
            {vol.Required("id"): cv.string, vol.Optional("checked", default=True): cv.boolean}
        ),
        lambda d, c: d.set_shopping_checked(c["id"], c["checked"]),
    ),
    "remove_shopping_item": (
        vol.Schema({vol.Required("id"): cv.string}),
        lambda d, c: d.remove_shopping_item(c["id"]),
    ),
    "clear_checked_shopping": (
        vol.Schema({}),
        lambda d, c: d.clear_checked_shopping(),
    ),
    "add_chore": (
        vol.Schema(
            {
                vol.Required("title"): cv.string,
                vol.Optional("assignee"): cv.string,
                vol.Optional("due"): cv.string,
            }
        ),
        lambda d, c: d.add_chore(c["title"], c.get("assignee"), c.get("due")),
    ),
    "update_chore": (
        vol.Schema(
            {
                vol.Required("id"): cv.string,
                vol.Optional("title"): cv.string,
                vol.Optional("assignee"): cv.string,
                vol.Optional("due"): cv.string,
            }
        ),
        lambda d, c: d.update_chore(
            c["id"], title=c.get("title"), assignee=c.get("assignee"), due=c.get("due")
        ),
    ),
    "complete_chore": (
        vol.Schema(
            {vol.Required("id"): cv.string, vol.Optional("done", default=True): cv.boolean}
        ),
        lambda d, c: d.set_chore_done(c["id"], c["done"]),
    ),
    "add_recipe": (
        vol.Schema(
            {
                vol.Optional("name", default=""): cv.string,
                vol.Optional("url"): cv.string,
                vol.Optional("notes"): cv.string,
                vol.Optional("source"): cv.string,
            }
        ),
        lambda d, c: d.add_recipe(
            c["name"], c.get("url"), c.get("notes"), c.get("source")
        ),
    ),
    "remove_recipe": (
        vol.Schema({vol.Required("id"): cv.string}),
        lambda d, c: d.remove_recipe(c["id"]),
    ),
    "remove_chore": (
        vol.Schema({vol.Required("id"): cv.string}),
        lambda d, c: d.remove_chore(c["id"]),
    ),
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JVRWall from a config entry."""
    manager = JVRWallManager(hass)
    await manager.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager

    if not hass.data[DOMAIN].get("_frontend"):
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    CARD_URL,
    COMPANION_URL,
                    str(Path(__file__).parent / "frontend" / "jvrwall-card.js"),
                    False,
                )
            ]
        )
        from homeassistant.components.frontend import add_extra_js_url

        add_extra_js_url(hass, CARD_URL)
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    COMPANION_URL,
                    str(Path(__file__).parent / "companion"),
                    False,
                )
            ]
        )
        hass.data[DOMAIN]["_frontend"] = True

    def _register(name, schema, action):
        async def handler(call: ServiceCall) -> None:
            try:
                action(manager.data, call.data)
            except (KeyError, ValueError) as err:
                raise vol.Invalid(f"{name} failed: {err}") from err
            await manager.async_changed()

        hass.services.async_register(DOMAIN, name, handler, schema=schema)

    for name, (schema, action) in SERVICES.items():
        _register(name, schema, action)

    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        for name in SERVICES:
            hass.services.async_remove(DOMAIN, name)
    return unload_ok
