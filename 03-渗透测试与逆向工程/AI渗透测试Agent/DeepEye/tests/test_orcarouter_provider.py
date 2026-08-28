"""OrcaRouter completion provider unit tests (mocked SDK)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_orcarouter_generate_chat(monkeypatch):
    from ai_providers import orcarouter_provider as mod

    fake_client = MagicMock()
    msg = MagicMock()
    msg.content = "payload list here"
    choice = MagicMock()
    choice.message = msg
    fake_resp = MagicMock()
    fake_resp.choices = [choice]
    fake_client.chat.completions.create.return_value = fake_resp

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __getattr__(self, name):
            return getattr(fake_client, name)

    monkeypatch.setattr(mod, "OpenAI", FakeOpenAI, raising=False)
    import openai as openai_mod

    monkeypatch.setattr(openai_mod, "OpenAI", FakeOpenAI)

    p = mod.OrcaRouterProvider(
        {"api_key": "sk-orca-test-key-not-placeholder", "model": "openai/gpt-4o", "max_tokens": 100}
    )
    p.client = fake_client
    out = p.generate("give me xss payloads")
    assert "payload" in out.lower()
    assert fake_client.chat.completions.create.called


def test_orcarouter_rejects_placeholder_key():
    import pytest

    from ai_providers.orcarouter_provider import OrcaRouterProvider

    with pytest.raises(ValueError):
        OrcaRouterProvider({"api_key": "sk-orca-your-orcarouter-api-key-here", "model": "openai/gpt-4o"})


def test_orcarouter_default_base_url():
    from ai_providers.orcarouter_provider import OrcaRouterProvider

    p = OrcaRouterProvider({"api_key": "sk-orca-test-key-not-placeholder", "model": "openai/gpt-4o"})
    assert p.base_url == "https://api.orcarouter.ai/v1"
    assert p.client is not None
