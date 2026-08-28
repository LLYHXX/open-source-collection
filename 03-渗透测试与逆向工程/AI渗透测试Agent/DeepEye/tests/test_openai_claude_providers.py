"""OpenAI + Anthropic completion provider unit tests (mocked SDK)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_openai_models_catalog():
    from ai_providers.openai_provider import OPENAI_MODELS, is_reasoning_model

    assert "gpt-4o" in OPENAI_MODELS
    assert "o1" in OPENAI_MODELS
    assert is_reasoning_model("o1-mini")
    assert not is_reasoning_model("gpt-4o")


def test_openai_generate_chat(monkeypatch):
    from ai_providers import openai_provider as mod

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
    # patch import path used inside __init__
    import openai as openai_mod

    monkeypatch.setattr(openai_mod, "OpenAI", FakeOpenAI)

    p = mod.OpenAIProvider(
        {"api_key": "sk-test-key-not-placeholder", "model": "gpt-4o", "max_tokens": 100}
    )
    p.client = fake_client
    out = p.generate("give me xss payloads")
    assert "payload" in out.lower()
    assert fake_client.chat.completions.create.called


def test_openai_rejects_placeholder_key():
    from ai_providers.openai_provider import OpenAIProvider
    import pytest

    with pytest.raises(ValueError):
        OpenAIProvider({"api_key": "sk-your-openai-api-key-here", "model": "gpt-4o"})


def test_claude_models_catalog():
    from ai_providers.claude_provider import CLAUDE_MODELS, _DEFAULT_MODEL

    assert "claude-sonnet-4-20250514" in CLAUDE_MODELS
    assert "claude" in _DEFAULT_MODEL


def test_claude_generate(monkeypatch):
    from ai_providers import claude_provider as mod
    import anthropic as anth

    block = MagicMock()
    block.text = "here are sqli payloads"
    fake_resp = MagicMock()
    fake_resp.content = [block]

    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_resp

    class FakeAnthropic:
        def __init__(self, **kwargs):
            self.messages = fake_client.messages

    monkeypatch.setattr(anth, "Anthropic", FakeAnthropic)

    p = mod.ClaudeProvider(
        {
            "api_key": "sk-ant-test-key-not-placeholder",
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 200,
        }
    )
    p.client = fake_client
    out = p.generate("sql injection payloads")
    assert "payload" in out.lower()
    fake_client.messages.create.assert_called()
    kwargs = fake_client.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-sonnet-4-20250514"
    assert kwargs["messages"][0]["role"] == "user"


def test_claude_rejects_placeholder():
    from ai_providers.claude_provider import ClaudeProvider
    import pytest

    with pytest.raises(ValueError):
        ClaudeProvider({"api_key": "sk-ant-your-claude-api-key-here"})


def test_manager_inits_openai_and_claude(monkeypatch):
    from ai_providers.provider_manager import AIProviderManager
    from ai_providers.openai_provider import OpenAIProvider
    from ai_providers.claude_provider import ClaudeProvider

    class FakeOA(OpenAIProvider):
        def __init__(self, config):
            self.config = config
            self.model = config.get("model", "gpt-4o")

        def generate(self, prompt, **kwargs):
            return "openai-ok"

    class FakeCL(ClaudeProvider):
        def __init__(self, config):
            self.config = config
            self.model = config.get("model", "claude-sonnet-4-20250514")

        def generate(self, prompt, **kwargs):
            return "claude-ok"

    monkeypatch.setattr("ai_providers.openai_provider.OpenAIProvider", FakeOA)
    monkeypatch.setattr("ai_providers.claude_provider.ClaudeProvider", FakeCL)

    # re-import path used inside manager
    import ai_providers.openai_provider as oam
    import ai_providers.claude_provider as cam

    monkeypatch.setattr(oam, "OpenAIProvider", FakeOA)
    monkeypatch.setattr(cam, "ClaudeProvider", FakeCL)

    mgr = AIProviderManager(
        {
            "ai_providers": {
                "openai": {
                    "enabled": True,
                    "api_key": "sk-test-real",
                    "model": "gpt-4o",
                },
                "claude": {
                    "enabled": True,
                    "api_key": "sk-ant-test-real",
                    "model": "claude-sonnet-4-20250514",
                },
            }
        }
    )
    # manager imports classes by path — patch those modules before re-init
    import importlib
    import ai_providers.provider_manager as pm

    monkeypatch.setattr(
        pm,
        "AIProviderManager",
        pm.AIProviderManager,
    )

    # Direct unit: instantiate manager with patched imports inside _initialize_providers
    original_init = AIProviderManager._initialize_providers

    def patched_init(self):
        ai_config = self.config.get("ai_providers", {})
        if ai_config.get("openai", {}).get("enabled"):
            self.providers["openai"] = FakeOA(ai_config["openai"])
        if ai_config.get("claude", {}).get("enabled"):
            self.providers["claude"] = FakeCL(ai_config["claude"])

    monkeypatch.setattr(AIProviderManager, "_initialize_providers", patched_init)
    mgr = AIProviderManager(
        {
            "ai_providers": {
                "openai": {"enabled": True, "api_key": "sk-test-real", "model": "gpt-4o"},
                "claude": {
                    "enabled": True,
                    "api_key": "sk-ant-test-real",
                    "model": "claude-sonnet-4-20250514",
                },
            }
        }
    )
    assert "openai" in mgr.providers
    assert "claude" in mgr.providers
    mgr.set_provider("openai")
    assert mgr.generate("hi") == "openai-ok"
    mgr.set_provider("claude")
    assert mgr.generate("hi") == "claude-ok"
