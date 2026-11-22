"""Values that change how the login relay integration behaves — the one place they are set.

Contract: cloud-server `contracts/oauth-relay.md` §3 (the home HA's own OAuth integration) and the command shape
ha-manager sent core-server and HA Gate (HAM-261113-68 · 69).
"""
from __future__ import annotations

DOMAIN = "login_relay"

# Vendors the relay logs in for (cloud-server relay table). A vendor not here gets no implementation from us, so
# its own flow never offers ours. Add one only when the relay has its credentials.
VENDORS: frozenset[str] = frozenset({"netatmo"})

# The config entry's fields — written by the home server when it sets this integration up.
CONF_SERVER_URL = "server_url"   # the home server's base URL as HA reaches it
CONF_TOKEN = "token"             # the integration's own bearer token for the home server (not HA's token for the server)

# The home server path the integration asks a refresh at (core-server opens it): POST {server}{path} {"refresh_token"}.
REFRESH_PATH = "/ha/oauth/{vendor}/refresh"
# Seconds a refresh call to the home server may take (the server's relay round trip is cut at 20 s).
REFRESH_TIMEOUT_SECONDS = 30

# The token fields the relay gives (contract §2-2) — nothing else is kept from an answer.
TOKEN_FIELDS = ("access_token", "refresh_token", "expires_in", "token_type", "scope")

# The flow context key every flow `login_relay/start` opens carries (value True). A later start aborts the leftover
# `user`-source flows that carry it, so a login the person left half-way does not hold the vendor's one unique id
# (`already_in_progress`). A flow a person opened in HA's own UI never carries it and is left alone.
RELAY_CONTEXT_KEY = "login_relay_opened"

# Steps the reauth walk may take before the external step (confirm form → pick implementation → external).
MAX_WALK_STEPS = 4
