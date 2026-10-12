"""Config flow for JVRWall."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.helpers import selector

from .const import CONF_CALENDARS, CONF_MEMBERS, DOMAIN


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Optional(
                CONF_CALENDARS, default=defaults.get(CONF_CALENDARS, [])
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="calendar", multiple=True)
            ),
            vol.Optional(
                CONF_MEMBERS, default=defaults.get(CONF_MEMBERS, [])
            ): selector.TextSelector(selector.TextSelectorConfig(multiple=True)),
        }
    )


class JVRWallConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-instance config flow. Pick Google Calendar entities and family members."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title="JVRWall", data={}, options=user_input)
        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    def async_get_options_flow(config_entry):
        return JVRWallOptionsFlow()


class JVRWallOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init", data_schema=_schema(dict(self.config_entry.options))
        )
