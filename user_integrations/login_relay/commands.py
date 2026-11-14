"""The three WebSocket commands the home server drives a vendor login with (HAM-261113-68 · 69).

* `login_relay/start` `{domain, start_url, reauth_entry_id}` → `{flow_id}` or `{error}` — opens the vendor's flow
  on our implementation (a reauth continues the flow HA already opened for that entry, or opens one), walking its forms
  (`{}` → `{"implementation": login_relay}`) until the external step, whose URL is the relay start URL given.
* `login_relay/finish` `{flow_id, token}` → `{result: created | reauth_successful, entry_id}` or
  `{result: failed, reason}` — passes the claimed token and walks `external_done` → `creation`.
* `login_relay/ready` → `{ready}` — true once our provider is registered and failed vendor entries were reloaded.

Neither answers nor logs carry a token.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResultType, UnknownFlow

from . import const
from .const import DOMAIN, MAX_WALK_STEPS

PICK_STEP = "pick_implementation"


@callback
def register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_start)
    websocket_api.async_register_command(hass, ws_finish)
    websocket_api.async_register_command(hass, ws_ready)


def _state(hass: HomeAssistant):
    from . import state_of  # the package holds the shared state
    return state_of(hass)


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/ready"})
@callback
def ws_ready(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    connection.send_result(msg["id"], {"ready": _state(hass).ready})


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/start",
    vol.Required("domain"): str,
    vol.Required("start_url"): str,
    vol.Optional("reauth_entry_id"): vol.Any(None, str),
})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_start(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    connection.send_result(msg["id"], await start(hass, msg["domain"], msg["start_url"], msg.get("reauth_entry_id")))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/finish",
    vol.Required("flow_id"): str,
    vol.Required("token"): dict,
})
@websocket_api.require_admin
@websocket_api.async_response
async def ws_finish(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    connection.send_result(msg["id"], await finish(hass, msg["flow_id"], msg["token"]))


async def start(hass: HomeAssistant, domain: str, start_url: str, reauth_entry_id: str | None) -> dict:
    state = _state(hass)
    if not state.ready:
        return {"error": "not_ready"}
    if domain not in const.VENDORS:
        return {"error": "unknown_domain"}
    state.pending_starts[domain] = start_url
    try:
        result = await _open(hass, domain, reauth_entry_id)
        for _ in range(MAX_WALK_STEPS):
            if result["type"] is FlowResultType.EXTERNAL_STEP:
                return {"flow_id": result["flow_id"]}
            if result["type"] is not FlowResultType.FORM:
                break
            given = {"implementation": DOMAIN} if result["step_id"] == PICK_STEP else {}
            result = await hass.config_entries.flow.async_configure(result["flow_id"], given)
    except (UnknownFlow, KeyError, ValueError):
        pass
    state.pending_starts.pop(domain, None)
    return {"error": "flow_failed"}


async def _open(hass: HomeAssistant, domain: str, reauth_entry_id: str | None):
    """A new flow, or for a reauth the one HA already has for that entry (one flow per entry — ours left hanging are
    aborted), else a new reauth flow."""
    if reauth_entry_id is None:
        return await hass.config_entries.flow.async_init(domain, context={"source": "user"})
    entry = hass.config_entries.async_get_entry(reauth_entry_id)
    if entry is None or entry.domain != domain:
        raise KeyError(reauth_entry_id)
    open_ones = [flow for flow in hass.config_entries.flow.async_progress_by_handler(domain)
                 if flow["context"].get("source") == SOURCE_REAUTH and flow["context"].get("entry_id") == entry.entry_id]
    for flow in open_ones[1:]:
        hass.config_entries.flow.async_abort(flow["flow_id"])
    if open_ones:
        return await hass.config_entries.flow.async_configure(open_ones[0]["flow_id"])
    return await hass.config_entries.flow.async_init(domain, context={
        "source": SOURCE_REAUTH, "entry_id": entry.entry_id, "unique_id": entry.unique_id,
        "title_placeholders": {"name": entry.title}}, data=entry.data)


async def finish(hass: HomeAssistant, flow_id: str, token: dict[str, Any]) -> dict:
    try:
        context = hass.config_entries.flow.async_get(flow_id)["context"]
        result = await hass.config_entries.flow.async_configure(flow_id, {"token": token})
        if result["type"] is FlowResultType.EXTERNAL_STEP_DONE:
            result = await hass.config_entries.flow.async_configure(flow_id)
    except UnknownFlow:
        return {"result": "failed", "reason": "unknown_flow"}
    if result["type"] is FlowResultType.CREATE_ENTRY:
        return {"result": "created", "entry_id": result["result"].entry_id}
    if result["type"] is FlowResultType.ABORT and result["reason"] == "reauth_successful":
        return {"result": "reauth_successful", "entry_id": context.get("entry_id")}
    return {"result": "failed", "reason": str(result.get("reason") or result["type"])}
