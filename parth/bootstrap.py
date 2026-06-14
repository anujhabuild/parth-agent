"""Startup defaults — Parth Agent works with zero API keys on first run."""
from __future__ import annotations

import os


def _has_any_credentials_fast() -> bool:
    """Cheap credential probe — avoids importing the full auth client stack."""
    if any(
        os.getenv(k)
        for k in (
            "ANTHROPIC_API_KEY",
            "OPENROUTER_API_KEY",
            "OPENCODE_API_KEY",
            "OPENCODE_ZEN_API_KEY",
        )
    ):
        return True

    from .constants import (
        KEY_FILE,
        OPENROUTER_KEY_FILE,
        OPENCODE_KEY_FILE,
        OPENCODE_ZEN_KEY_FILE,
        OAUTH_FILE,
    )
    from .constants.paths import CODEX_OAUTH_FILE

    for path in (
        KEY_FILE,
        OPENROUTER_KEY_FILE,
        OPENCODE_KEY_FILE,
        OPENCODE_ZEN_KEY_FILE,
        OAUTH_FILE,
        CODEX_OAUTH_FILE,
    ):
        try:
            if path.exists() and path.read_text().strip():
                return True
        except OSError:
            pass
    return False


def ensure_parth_agent_defaults() -> None:
    """Pin free Parth Agent on first install (before the user picks a model)."""
    from . import state
    from .constants.providers import PARTH_AGENT_DEFAULT_MODEL, PROVIDER_OPENCODE_ZEN
    from .storage.prefs import should_use_first_run_parth_defaults

    if not should_use_first_run_parth_defaults():
        return
    state.provider = PROVIDER_OPENCODE_ZEN
    state.MODEL = PARTH_AGENT_DEFAULT_MODEL
    state.parth_agent_free = True
