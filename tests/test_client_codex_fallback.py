"""Startup auth resolution when Codex OAuth is missing."""
from unittest.mock import MagicMock, patch

from parth.auth.client import _resolve_provider, make_client
from parth.constants.providers import PROVIDER_ANTHROPIC, PROVIDER_OPENAI_CODEX


def test_resolve_provider_ignores_stale_codex_pin(tmp_path, monkeypatch):
    provider_file = tmp_path / "provider"
    provider_file.write_text(PROVIDER_OPENAI_CODEX)
    monkeypatch.setattr("parth.constants.paths.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.auth.client.load_codex_oauth_tokens", lambda: None)
    monkeypatch.setattr("parth.auth.client.load_oauth_tokens", lambda: {"access_token": "a", "refresh_token": "r"})
    monkeypatch.setattr("parth.auth.client.KEY_FILE", tmp_path / "missing-key")
    # Clear saved preferences so _resolve_provider falls through to the provider file
    monkeypatch.setattr("parth.storage.prefs.load_saved_preferences", lambda: ("", ""))
    monkeypatch.setattr("parth.storage.prefs.load_saved_provider", lambda: "")
    assert _resolve_provider(interactive=True) == PROVIDER_ANTHROPIC


def test_make_client_first_run_uses_parth_agent(tmp_path, monkeypatch, tmp_path_factory):
    """Stale auth marker files without tokens should still boot Parth Agent."""
    settings_dir = tmp_path / "cfg"
    settings_dir.mkdir()
    settings_file = settings_dir / "settings.json"
    settings_file.write_text("{}\n")
    monkeypatch.setattr("parth.storage.settings.SETTINGS_FILE", settings_file)
    monkeypatch.setattr("parth.storage.settings.CONFIG_DIR", settings_dir)
    monkeypatch.setattr("parth.storage.settings._singleton", None)
    monkeypatch.setattr("parth.auth.client.AUTH_MODE_FILE", tmp_path / "auth_mode")
    monkeypatch.setattr("parth.auth.client.PROVIDER_FILE", tmp_path / "provider")
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
    from parth.constants.providers import PARTH_AGENT_DEFAULT_MODEL, PROVIDER_OPENCODE_ZEN
    state.MODEL = PARTH_AGENT_DEFAULT_MODEL
    client = make_client(interactive=False)
    assert client is not None
    assert state.provider == PROVIDER_OPENCODE_ZEN
    assert state.MODEL == PARTH_AGENT_DEFAULT_MODEL
    assert state.parth_agent_free is True


def test_make_client_falls_back_when_codex_oauth_missing(tmp_path, monkeypatch):
    provider_file = tmp_path / "provider"
    provider_file.write_text(PROVIDER_OPENAI_CODEX)
    monkeypatch.setattr("parth.auth.client.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.constants.paths.PROVIDER_FILE", provider_file)
    monkeypatch.setattr("parth.auth.client._build_codex_client", lambda: None)
    monkeypatch.setattr(
        "parth.auth.client._pick_fallback_provider",
        lambda **kwargs: PROVIDER_ANTHROPIC,
    )

    fake_client = MagicMock()
    monkeypatch.setattr("parth.storage.prefs.load_saved_model", lambda: "claude-sonnet-4-6")
    monkeypatch.setattr("parth.storage.prefs.should_use_first_run_parth_defaults", lambda: False)
    # Prevent _resolve_provider from returning the user's real saved provider
    monkeypatch.setattr("parth.storage.prefs.load_saved_preferences", lambda: ("", ""))
    monkeypatch.setattr("parth.storage.prefs.load_saved_provider", lambda: "")
    with patch("parth.auth.client._build_client_from_mode", return_value=fake_client):
        with patch("parth.auth.client.sync_anthropic_model_ids"):
            monkeypatch.setattr("parth.auth.client.load_oauth_tokens", lambda: {"access_token": "a", "refresh_token": "r"})
            monkeypatch.setattr("parth.auth.client.AUTH_MODE_FILE", tmp_path / "auth_mode")
            monkeypatch.setattr("parth.auth.client.KEY_FILE", tmp_path / "key")
            client = make_client(interactive=True)
    assert client is fake_client
