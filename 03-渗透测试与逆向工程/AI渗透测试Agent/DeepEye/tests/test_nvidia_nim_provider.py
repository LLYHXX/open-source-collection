"""NVIDIA NIM completion provider unit tests (mocked SDK)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_nvidia_nim_generate_chat(monkeypatch):
    from ai_providers import nvidia_nim_provider as mod

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

    p = mod.NvidiaNIMProvider(
        {
            "api_key": "nvapi-test-key-not-placeholder",
            "model": "nvidia/nemotron-3-ultra-550b-a55b",
            "max_tokens": 100,
            "site_url": "https://example.com",
            "site_name": "Test Site",
        }
    )
    p.client = fake_client
    out = p.generate("give me sql injection payloads")
    assert "payload" in out.lower()
    assert fake_client.chat.completions.create.called

    # Verify call arguments
    call_kwargs = fake_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
    assert call_kwargs["max_tokens"] == 100
    assert call_kwargs["extra_headers"]["HTTP-Referer"] == "https://example.com"
    assert call_kwargs["extra_headers"]["X-Title"] == "Test Site"


def test_nvidia_nim_rejects_placeholder_key():
    from ai_providers.nvidia_nim_provider import NvidiaNIMProvider

    with pytest.raises(ValueError):
        NvidiaNIMProvider({
            "api_key": "your-nvidia-nim-api-key-here",
            "model": "nvidia/nemotron-3-ultra-550b-a55b"
        })

    with pytest.raises(ValueError):
        NvidiaNIMProvider({
            "api_key": "",
            "model": "nvidia/nemotron-3-ultra-550b-a55b"
        })


def test_nvidia_nim_config_defaults():
    from ai_providers.nvidia_nim_provider import NvidiaNIMProvider

    p = NvidiaNIMProvider({
        "api_key": "nvapi-test-valid-key",
    })
    assert p.base_url == "https://integrate.api.nvidia.com/v1"
    assert p.model == "nvidia/nemotron-3-ultra-550b-a55b"
    assert p.temperature == 0.7
    assert p.max_tokens == 2000
    assert p.timeout == 60.0
    assert p.client is not None


def test_nvidia_nim_custom_base_url():
    from ai_providers.nvidia_nim_provider import NvidiaNIMProvider

    p = NvidiaNIMProvider({
        "api_key": "nvapi-test-valid-key",
        "base_url": "https://custom.nvidia.nim/v1",
        "model": "meta/llama-3.1-70b-instruct",
        "timeout": 45,
    })
    assert p.base_url == "https://custom.nvidia.nim/v1"
    assert p.model == "meta/llama-3.1-70b-instruct"
    assert p.timeout == 45.0


def test_nvidia_nim_generate_error(monkeypatch):
    from ai_providers import nvidia_nim_provider as mod

    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = RuntimeError("API rate limit exceeded")

    p = mod.NvidiaNIMProvider({
        "api_key": "nvapi-test-valid-key",
    })
    p.client = fake_client

    with pytest.raises(RuntimeError) as exc_info:
        p.generate("test prompt")
    assert "rate limit" in str(exc_info.value)


def test_provider_manager_initializes_nvidia_nim(monkeypatch):
    from ai_providers.provider_manager import AIProviderManager

    fake_client = MagicMock()
    msg = MagicMock()
    msg.content = "response from nvidia nim"
    fake_resp = MagicMock()
    fake_resp.choices = [MagicMock(message=msg)]
    fake_client.chat.completions.create.return_value = fake_resp

    from ai_providers import nvidia_nim_provider as mod
    monkeypatch.setattr(mod, "OpenAI", lambda **kwargs: fake_client)

    cfg = {
        "ai_providers": {
            "nvidia_nim": {
                "enabled": True,
                "api_key": "nvapi-test-valid-key",
                "model": "nvidia/nemotron-3-ultra-550b-a55b",
            }
        },
        "scanner": {
            "ai_provider": "nvidia_nim"
        }
    }

    manager = AIProviderManager(cfg)
    assert "nvidia_nim" in manager.get_available_providers()
    assert manager._active_name == "nvidia_nim"

    # Test generate through manager
    manager.active_provider.client = fake_client
    res = manager.generate("hello")
    assert res == "response from nvidia nim"
