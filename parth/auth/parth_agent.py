"""Free Parth Agent tier — OpenCode Zen with public bearer (no API key)."""
from __future__ import annotations

import uuid

from ..constants import (
    OPENCODE_ZEN_BASE_URL,
    PROVIDER_PARTH_AGENT,
    PROVIDER_OPENCODE_ZEN,
    is_parth_agent_model,
)
from ._zen_wire import session_id, zen_client_kwargs
from .opencode_client import OpenCodeClient
from .opencode_zen import has_opencode_zen_key


def should_use_parth_agent_client(model: str | None = None, *, source: str = "") -> bool:
    """Free public Zen tier — Parth Agent source, or no Zen key on first run."""
    if source == PROVIDER_OPENCODE_ZEN:
        return False
    if source == PROVIDER_PARTH_AGENT:
        return True
    from .. import state

    if getattr(state, "parth_agent_free", False) and is_parth_agent_model(
        (model if model is not None else state.MODEL).strip()
    ):
        return True
    m = (model if model is not None else state.MODEL).strip()
    if not is_parth_agent_model(m):
        return False
    return not has_opencode_zen_key()


def build_parth_agent_client() -> OpenCodeClient:
    """OpenCode Zen client for the free Parth Agent tier."""
    sid = session_id(uuid.uuid4().hex[:12])
    return OpenCodeClient(
        base_url=f"{OPENCODE_ZEN_BASE_URL}/",
        **zen_client_kwargs(sid),
    )
