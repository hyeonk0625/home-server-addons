"""The one login relay entry — the home server's URL and the integration's own token for it, given by the home server
when it sets the integration up. One per home."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_SERVER_URL, CONF_TOKEN, DOMAIN


class LoginRelayFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """The form is shown even when the entry exists: a home server that lost its key file (restored without a
        backup) gives a new key the same way, and the entry takes it and reloads, then the flow ends
        `already_configured` (CS-261114-37 — before, the flow ended before the form and the old key stayed)."""
        await self.async_set_unique_id(DOMAIN)
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=vol.Schema({
                vol.Required(CONF_SERVER_URL): str, vol.Required(CONF_TOKEN): str}))
        self._abort_if_unique_id_configured(updates=user_input)
        return self.async_create_entry(title="Login relay", data=user_input)
