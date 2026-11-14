"""One vendor's OAuth implementation whose tokens come from the seller's relay (contract §3).

The vendor's own client secret never reaches the home: the relay exchanges the code and refreshes. So this
implementation never talks to the vendor. The authorize URL is the relay's start URL the home server opened a session
for (`pending_starts`), the token is what the home server claimed from the relay and passed in (`commands.finish`), and
a refresh goes through the home server (`REFRESH_PATH`), which calls the relay.

`refresh_token` holds the relay's sealed value — kept and sent as it is, never opened (contract §5).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    OAuth2TokenRequestConnectionError,
    OAuth2TokenRequestReauthError,
    OAuth2TokenRequestTransientError,
)
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, REFRESH_PATH, REFRESH_TIMEOUT_SECONDS, TOKEN_FIELDS

_LOGGER = logging.getLogger(__name__)


class BadToken(Exception):
    """A token answer missing its access token or with no positive whole `expires_in` — never carries the answer."""


def clean_token(answer: Any) -> dict:
    """The relay's token fields only (contract §2-2), checked: a non-empty `access_token` and a positive whole
    `expires_in`. Anything else raises `BadToken` with no text of the answer (tokens are never logged)."""
    if not isinstance(answer, dict):
        raise BadToken
    token = {field: answer[field] for field in TOKEN_FIELDS if field in answer}
    expires_in = token.get("expires_in")
    if not token.get("access_token") or isinstance(expires_in, bool) or not isinstance(expires_in, int) \
            or expires_in < 1:
        raise BadToken
    return token


class RelayImplementation(config_entry_oauth2_flow.AbstractOAuth2Implementation):
    """The relay's implementation for one vendor (`vendor`). Its `domain` is ours — the vendor's entries then keep
    `auth_implementation: login_relay` and find us again through the provider."""

    def __init__(self, hass: HomeAssistant, vendor: str, server_url: str, server_token: str,
                 pending_starts: dict[str, str], locks: dict[str, asyncio.Lock]) -> None:
        self.hass = hass
        self.vendor = vendor
        self._server_url = server_url.rstrip("/")
        self._server_token = server_token
        self._pending_starts = pending_starts   # vendor -> the start URL `login_relay/start` was given
        self._locks = locks                     # sealed refresh value -> its lock, shared by all vendors

    @property
    def name(self) -> str:
        return "Login relay"

    @property
    def domain(self) -> str:
        return DOMAIN

    @property
    def service_domain(self) -> str:
        return self.vendor

    async def async_generate_authorize_url(self, flow_id: str) -> str:
        """The relay start URL the home server opened for this vendor — once. None given means the flow was not
        started by the home server; it then has no URL to show and stops (`KeyError` → the flow's own abort)."""
        return self._pending_starts.pop(self.vendor)

    async def async_resolve_external_data(self, external_data: Any) -> dict:
        """The token the home server passed (`commands.finish`), checked. A bad one ends the flow as a failure."""
        try:
            return clean_token((external_data or {}).get("token"))
        except BadToken as err:
            raise OAuth2TokenRequestConnectionError(domain=self.vendor) from err

    async def _async_refresh_token(self, token: dict) -> dict:
        """Ask the home server to refresh through the relay. One refresh per sealed value at a time; the answer is
        merged with the old token directly (its `scope` kept when the answer has none). Errors map as the contract
        says: only 400 with `invalid_grant` asks for a new login."""
        sealed = token.get("refresh_token")
        if not isinstance(sealed, str) or not sealed:
            raise OAuth2TokenRequestReauthError(domain=self.vendor, request_info=None, history=(), status=400)
        lock = self._locks.setdefault(sealed, asyncio.Lock())
        async with lock:
            answer = await self._ask_refresh(sealed)
        try:
            fresh = clean_token(answer)
        except BadToken as err:
            raise OAuth2TokenRequestConnectionError(domain=self.vendor) from err
        return {**token, **fresh, "scope": fresh.get("scope", token.get("scope"))}

    async def _ask_refresh(self, sealed: str) -> Any:
        url = self._server_url + REFRESH_PATH.format(vendor=self.vendor)
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(REFRESH_TIMEOUT_SECONDS):
                response = await session.post(url, json={"refresh_token": sealed},
                                              headers={"Authorization": f"Bearer {self._server_token}"})
                status = response.status
                try:
                    body = await response.json(content_type=None)
                except (ValueError, aiohttp.ContentTypeError):
                    body = None
        except (TimeoutError, aiohttp.ClientError) as err:
            raise OAuth2TokenRequestConnectionError(domain=self.vendor) from err
        if status == 200:
            if not isinstance(body, dict):
                raise OAuth2TokenRequestConnectionError(domain=self.vendor)
            return body.get("token", body)
        if status == 400 and isinstance(body, dict) and body.get("error") == "invalid_grant":
            raise OAuth2TokenRequestReauthError(domain=self.vendor, request_info=getattr(response, "request_info", None),
                                                history=(), status=status)
        if body is None:
            raise OAuth2TokenRequestConnectionError(domain=self.vendor)
        raise OAuth2TokenRequestTransientError(domain=self.vendor, request_info=getattr(response, "request_info", None),
                                               history=(), status=status)

    def logger(self) -> logging.Logger:  # the base class names it a method
        return _LOGGER
