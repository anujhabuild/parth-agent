"""Model preference survives restarts and startup fallbacks."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from parth.bootstrap import ensure_parth_agent_defaults
from parth.constants.providers import PARTH_AGENT_DEFAULT_MODEL, PROVIDER_ANTHROPIC
from parth.storage.settings import Settings


@pytest.fixture
def global_settings(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr("parth.storage.settings.SETTINGS_FILE", settings_file)
    monkeypatch.setattr("parth.storage.settings.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("parth.storage.settings._singleton", None)
    return settings_file


def test_save_last_model_writes_global_only(global_settings, monkeypatch):
    from parth import state
    from parth.storage.prefs import load_saved_model, save_last_model
    from parth.storage.settings import Settings

    monkeypatch.setattr(
        "parth.storage.settings.get_settings",
        lambda: Settings(global_settings),
    )

    state.MODEL = "claude-sonnet-4-6"
    state.provider = PROVIDER_ANTHROPIC
    save_last_model()

    assert load_saved_model() == "claude-sonnet-4-6"
    doc = json.loads(global_settings.read_text())
    assert doc["model"] == "claude-sonnet-4-6"
    assert doc["provider"] == PROVIDER_ANTHROPIC


def test_project_settings_do_not_override_saved_model(global_settings, tmp_path, monkeypatch):
    global_settings.write_text(
        json.dumps({"model": "claude-sonnet-4-6", "provider": "anthropic"}) + "\n"
    )
    project_dir = tmp_path / "proj" / ".parth"
    project_dir.mkdir(parents=True)
    (project_dir / "settings.json").write_text(
        json.dumps({"model": "deepseek-v4-flash-free"}) + "\n"
    )
    monkeypatch.chdir(tmp_path / "proj")
    monkeypatch.setattr(
        "parth.storage.settings._read_project_settings",
        lambda: {"model": "deepseek-v4-flash-free"},
    )

    s = Settings(global_settings)
    s.load()
    assert s.get("model") == "claude-sonnet-4-6"


def test_bootstrap_respects_saved_model(monkeypatch):
    monkeypatch.setattr("parth.storage.prefs.should_use_first_run_parth_defaults", lambda: False)

    from parth import state

    state.MODEL = "claude-sonnet-4-6"
    state.provider = "anthropic"
    ensure_parth_agent_defaults()
    assert state.MODEL == "claude-sonnet-4-6"


def test_first_install_uses_parth_even_with_credentials(tmp_path, monkeypatch, global_settings):
    """Fresh install must not auto-jump to Anthropic when API keys exist on disk."""
    provider_file = tmp_path / "provider"
    provider_file.write_text("anthropic")
    monkeypatch.setattr("parth.auth.client.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.constants.paths.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.auth.client.KEY_FILE", tmp_path / "key")
    (tmp_path / "key").write_text("sk-test-key")
    monkeypatch.setattr("parth.storage.prefs.load_saved_model", lambda: "")
    monkeypatch.setattr("parth.storage.prefs.should_use_first_run_parth_defaults", lambda: True)
    monkeypatch.setattr("parth.auth.client._build_opencode_zen_client_for_model", lambda *a, **k: MagicMock())
    monkeypatch.setattr("parth.auth.parth_agent.build_parth_agent_client", lambda: MagicMock())

    from parth import state
    from parth.auth.client import make_client
    from parth.constants.providers import PARTH_AGENT_DEFAULT_MODEL, PROVIDER_OPENCODE_ZEN

    client = make_client(interactive=False)
    assert client is not None
    assert state.provider == PROVIDER_OPENCODE_ZEN
    assert state.MODEL == PARTH_AGENT_DEFAULT_MODEL
    assert state.parth_agent_free is True


def test_stale_provider_file_does_not_override_saved_model(
    tmp_path, monkeypatch, global_settings
):
    """Saved settings win over a stale ~/.config/parth-agent/provider file."""
    global_settings.write_text(
        json.dumps({"model": "nemotron-3-super-free", "provider": "opencode_zen"}) + "\n"
    )
    provider_file = tmp_path / "provider"
    provider_file.write_text("anthropic")
    key_file = tmp_path / "key"
    key_file.write_text("sk-test")
    monkeypatch.setattr("parth.auth.client.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.constants.paths.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.auth.client.KEY_FILE", key_file)
    monkeypatch.setattr("parth.storage.prefs.load_saved_model", lambda: "nemotron-3-super-free")
    monkeypatch.setattr(
        "parth.storage.prefs.load_saved_preferences",
        lambda: ("nemotron-3-super-free", "opencode_zen"),
    )
    monkeypatch.setattr("parth.storage.prefs.should_use_first_run_parth_defaults", lambda: False)
    monkeypatch.setattr("parth.auth.client._build_opencode_zen_client_for_model", lambda *a, **k: MagicMock())

    from parth import state
    from parth.auth.client import make_client
    from parth.constants.providers import PROVIDER_OPENCODE_ZEN

    client = make_client(interactive=False)
    assert client is not None
    assert state.MODEL == "nemotron-3-super-free"
    assert state.provider == PROVIDER_OPENCODE_ZEN
    assert state.parth_agent_free is True
    assert provider_file.read_text().strip() == PROVIDER_OPENCODE_ZEN


def test_make_client_does_not_clobber_saved_model_on_free_tier_fallback(
    tmp_path, monkeypatch, global_settings
):
    global_settings.write_text(
        json.dumps({"model": "claude-sonnet-4-6", "provider": "anthropic"}) + "\n"
    )
    provider_file = tmp_path / "provider"
    monkeypatch.setattr("parth.auth.client.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.constants.paths.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.auth.client.AUTH_MODE_FILE", tmp_path / "auth_mode")
    monkeypatch.setattr("parth.auth.client.KEY_FILE", tmp_path / "missing-key")
    monkeypatch.setattr("parth.auth.client._has_usable_provider_credentials", lambda: False)
    monkeypatch.setattr("parth.auth.client._resolve_provider", lambda **kwargs: "opencode_zen")
    monkeypatch.setattr("parth.storage.prefs.load_saved_model", lambda: "claude-sonnet-4-6")
    monkeypatch.setattr("parth.storage.prefs.should_use_first_run_parth_defaults", lambda: False)
    monkeypatch.setattr("parth.auth.client._build_opencode_zen_client_for_model", lambda *a, **k: MagicMock())
    monkeypatch.setattr("parth.auth.parth_agent.build_parth_agent_client", lambda: MagicMock())

    from parth import state
    from parth.auth.client import make_client
    from parth.constants.providers import PROVIDER_OPENCODE_ZEN

    state.MODEL = "claude-sonnet-4-6"
    client = make_client(interactive=False)
    assert client is not None
    assert state.MODEL == "claude-sonnet-4-6"
    assert state.provider == PROVIDER_OPENCODE_ZEN
    assert json.loads(global_settings.read_text())["model"] == "claude-sonnet-4-6"


def test_make_client_first_run_without_saved_model_uses_parth_default(
    tmp_path, monkeypatch, global_settings
):
    provider_file = tmp_path / "provider"
    monkeypatch.setattr("parth.auth.client.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.constants.paths.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.auth.client.AUTH_MODE_FILE", tmp_path / "auth_mode")
    monkeypatch.setattr("parth.auth.client.KEY_FILE", tmp_path / "missing-key")
    (tmp_path / "auth_mode").write_text("oauth")
    monkeypatch.setattr("parth.auth.client.load_oauth_tokens", lambda: None)
    monkeypatch.setattr("parth.auth.client.load_codex_oauth_tokens", lambda: None)
    monkeypatch.setattr("parth.auth.client._has_usable_provider_credentials", lambda: False)
    monkeypatch.setattr("parth.auth.client._resolve_provider", lambda **kwargs: "opencode_zen")
    monkeypatch.setattr("parth.storage.prefs.load_saved_model", lambda: "")
    monkeypatch.setattr("parth.storage.prefs.should_use_first_run_parth_defaults", lambda: True)
    monkeypatch.setattr("parth.auth.client._build_opencode_zen_client_for_model", lambda *a, **k: MagicMock())
    monkeypatch.setattr("parth.auth.parth_agent.build_parth_agent_client", lambda: MagicMock())

    from parth import state
    from parth.auth.client import make_client
    from parth.constants.providers import PROVIDER_OPENCODE_ZEN

    state.MODEL = PARTH_AGENT_DEFAULT_MODEL
    client = make_client(interactive=False)
    assert client is not None
    assert state.provider == PROVIDER_OPENCODE_ZEN
    assert state.MODEL == PARTH_AGENT_DEFAULT_MODEL
    assert state.parth_agent_free is True
