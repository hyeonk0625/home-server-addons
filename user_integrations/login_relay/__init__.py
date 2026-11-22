"""Login relay — the home HA's own OAuth integration for vendors whose login the seller's relay does
(cloud-server `contracts/oauth-relay.md` §3, user decision-261113-22 · decision-261113-95 1).

What it does:

* **provider** — registers itself with `async_add_implementation_provider`, giving each relay vendor (`VENDORS`) one
  `RelayImplementation`. The vendor's integration gets no application credentials.
* **commands** — the home server drives a login through four WebSocket commands (`commands.py`):
  `login_relay/start` · `login_relay/finish` · `login_relay/ready` · `login_relay/alive`. Whether a flow is still alive
  is asked here (`alive`): HA's own flow list (`config_entries/flow/progress`) leaves out `user`-source flows, so a new
  login's flow is never in it.
* **start order** — a vendor entry set up before us fails (its implementation is unknown). The moment the provider
  is registered, every vendor entry that names us and is in `SETUP_ERROR` is reloaded; only then is `ready` true.

Installed by the seller's add-on (core-server, `home-server-addons`) into `custom_components/login_relay`. Tokens and
the relay's sealed values are never written to a log.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.typing import ConfigType

from . import commands, const
from .const import CONF_SERVER_URL, CONF_TOKEN, DOMAIN
from .implementation import RelayImplementation

_LOGGER = logging.getLogger(__name__)


@dataclass
class RelayState:
    """What the commands and the provider share (`hass.data[DOMAIN]`)."""
    server_url: str | None = None
    server_token: str | None = None
    ready: bool = False
    pending_starts: dict[str, str] = field(default_factory=dict)   # vendor -> start URL for the next flow
    locks: dict[str, asyncio.Lock] = field(default_factory=dict)    # sealed refresh value -> lock


def state_of(hass: HomeAssistant) -> RelayState:
    return hass.data.setdefault(DOMAIN, RelayState())


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """The commands stand from HA's start (`ready` answers false until an entry is set up)."""
    state_of(hass)
    commands.register(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    state = state_of(hass)
    state.server_url = entry.data[CONF_SERVER_URL]
    state.server_token = entry.data[CONF_TOKEN]

    async def provide(hass: HomeAssistant, domain: str) -> list[config_entry_oauth2_flow.AbstractOAuth2Implementation]:
        if domain not in const.VENDORS or state.server_url is None or state.server_token is None:
            return []
        return [RelayImplementation(hass, domain, state.server_url, state.server_token, state.pending_starts,
                                    state.locks)]

    config_entry_oauth2_flow.async_add_implementation_provider(hass, DOMAIN, provide)
    entry.async_create_background_task(hass, _reload_failed(hass, state), "login_relay reload failed vendors")
    return True


async def _reload_failed(hass: HomeAssistant, state: RelayState) -> None:
    """Reload every vendor entry that names us and failed to set up (it started before us), then say ready."""
    for vendor in sorted(const.VENDORS):
        for entry in hass.config_entries.async_entries(vendor):
            if entry.data.get("auth_implementation") == DOMAIN and entry.state is ConfigEntryState.SETUP_ERROR:
                await hass.config_entries.async_reload(entry.entry_id)
    state.ready = True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    state = state_of(hass)
    state.ready = False
    state.server_url = state.server_token = None
    hass.data.get(config_entry_oauth2_flow.DATA_PROVIDERS, {}).pop(DOMAIN, None)
    return True
