"""Parth Agent (free OpenCode Zen) tests."""
import unittest
import uuid
from unittest import mock

from parth import state
from parth.auth import _zen_wire
from parth.auth.parth_agent import build_parth_agent_client, should_use_parth_agent_client
from parth.constants.providers import (
    PARTH_AGENT_DEFAULT_MODEL,
    PARTH_AGENT_MODELS,
    OPENCODE_ZEN_MODELS,
    PROVIDER_PARTH_AGENT,
    PROVIDER_OPENCODE_ZEN,
    connected_model_sources,
    is_parth_agent_model,
    models_for_source,
)


class ParthAgentTests(unittest.TestCase):
    def test_parth_agent_models_listed(self):
        ids = {m for m, _ in PARTH_AGENT_MODELS}
        self.assertEqual(
            ids,
            {"deepseek-v4-flash-free", "nemotron-3-super-free", "nemotron-3-ultra-free", "mimo-v2.5-free", "big-pickle", "minimax-m3-free"},
        )

    def test_parth_agent_always_in_model_sources(self):
        sources = connected_model_sources()
        self.assertIn(PROVIDER_PARTH_AGENT, sources)
        self.assertEqual(sources[0], PROVIDER_PARTH_AGENT)

    def test_models_for_parth_agent_source(self):
        models = models_for_source(PROVIDER_PARTH_AGENT)
        self.assertEqual(len(models), 6)
        self.assertEqual(models[0][0], PARTH_AGENT_DEFAULT_MODEL)

    def test_opencode_zen_models_include_exclusive_and_shared(self):
        ids = {m for m, _ in OPENCODE_ZEN_MODELS}
        self.assertIn("minimax-m2.5-free", ids)
        self.assertIn("deepseek-v4-flash-free", ids)
        self.assertIn("mimo-v2.5-free", ids)
        self.assertIn("big-pickle", ids)

    def test_is_parth_agent_model(self):
        self.assertTrue(is_parth_agent_model("deepseek-v4-flash-free"))
        self.assertTrue(is_parth_agent_model("mimo-v2.5-free"))
        self.assertFalse(is_parth_agent_model("minimax-m2.5-free"))

    def test_should_use_parth_agent_client(self):
        state.MODEL = "deepseek-v4-flash-free"
        self.assertTrue(should_use_parth_agent_client(source=PROVIDER_PARTH_AGENT))
        self.assertFalse(should_use_parth_agent_client(source=PROVIDER_OPENCODE_ZEN))
        state.MODEL = "claude-sonnet-4-6"
        self.assertFalse(should_use_parth_agent_client())
        self.assertFalse(should_use_parth_agent_client(source=PROVIDER_OPENCODE_ZEN))

    def test_build_parth_agent_client_headers(self):
        with mock.patch("parth.auth.parth_agent.uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = uuid.UUID("00000000-0000-0000-0000-000000000001")
            client = build_parth_agent_client()
        wire = _zen_wire.zen_client_kwargs(_zen_wire.session_id("000000000000"))
        self.assertEqual(client._oai.api_key, wire["api_key"])
        self.assertTrue(client._oai.base_url.path.endswith("/zen/v1/"))
        hdrs = client._oai.default_headers
        for k, v in wire["default_headers"].items():
            self.assertEqual(hdrs[k], v)
        req_hdr = wire["request_id_header"]
        prefix = wire["request_id_prefix"]
        self.assertEqual(client.next_request_headers(), {req_hdr: f"{prefix}1"})
        self.assertEqual(client.next_request_headers(), {req_hdr: f"{prefix}2"})


if __name__ == "__main__":
    unittest.main()
