"""Tool-calling runtime tests (OpenAI + Claude, mocked SDK)."""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def test_normalize_tools_openai_and_flat():
    from ai_providers.tool_runtime import ToolSpec, normalize_tools

    specs = normalize_tools(
        [
            ToolSpec("lookup", "look up CVE", {"type": "object", "properties": {"id": {"type": "string"}}}),
            {
                "type": "function",
                "function": {
                    "name": "echo",
                    "description": "echo",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {"name": "flat", "description": "flat tool", "input_schema": {"type": "object"}},
        ]
    )
    names = {s.name for s in specs}
    assert names == {"lookup", "echo", "flat"}
    assert specs[0].to_openai()["type"] == "function"
    assert "input_schema" in specs[0].to_anthropic()


def test_run_handlers():
    from ai_providers.tool_runtime import ToolCall, run_handlers

    calls = [ToolCall(id="1", name="add", arguments={"a": 1, "b": 2})]
    out = run_handlers(calls, {"add": lambda a, b: a + b})
    assert out[0]["content"] == "3"


def test_openai_tool_loop(monkeypatch):
    from ai_providers import openai_provider as mod
    from ai_providers.tool_runtime import ToolSpec
    import openai as openai_mod

    # round1: tool call; round2: final text
    call1 = MagicMock()
    call1.id = "call_1"
    call1.function = MagicMock()
    call1.function.name = "get_cve"
    call1.function.arguments = json.dumps({"cve_id": "CVE-2021-44228"})

    msg1 = MagicMock()
    msg1.content = None
    msg1.tool_calls = [call1]
    choice1 = MagicMock()
    choice1.message = msg1
    choice1.finish_reason = "tool_calls"
    resp1 = MagicMock()
    resp1.choices = [choice1]

    msg2 = MagicMock()
    msg2.content = "Log4Shell critical RCE"
    msg2.tool_calls = None
    choice2 = MagicMock()
    choice2.message = msg2
    choice2.finish_reason = "stop"
    resp2 = MagicMock()
    resp2.choices = [choice2]

    fake_client = MagicMock()
    fake_client.chat.completions.create.side_effect = [resp1, resp2]

    class FakeOpenAI:
        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(openai_mod, "OpenAI", FakeOpenAI)

    p = mod.OpenAIProvider({"api_key": "sk-test-not-placeholder", "model": "gpt-4o"})
    p.client = fake_client

    tools = [
        ToolSpec(
            "get_cve",
            "Get CVE details",
            {
                "type": "object",
                "properties": {"cve_id": {"type": "string"}},
                "required": ["cve_id"],
            },
        )
    ]
    handlers = {"get_cve": lambda cve_id: {"id": cve_id, "score": 10.0}}

    out = p.generate("What is Log4Shell?", tools=tools, handlers=handlers)
    assert "Log4Shell" in out or "RCE" in out
    assert fake_client.chat.completions.create.call_count == 2


def test_claude_tool_loop(monkeypatch):
    from ai_providers import claude_provider as mod
    from ai_providers.tool_runtime import ToolSpec
    import anthropic as anth

    tu = MagicMock()
    tu.type = "tool_use"
    tu.id = "toolu_1"
    tu.name = "lookup"
    tu.input = {"q": "ssrf"}

    resp1 = MagicMock()
    resp1.content = [tu]
    resp1.stop_reason = "tool_use"

    tb = MagicMock()
    tb.type = "text"
    tb.text = "SSRF hits cloud metadata"
    resp2 = MagicMock()
    resp2.content = [tb]
    resp2.stop_reason = "end_turn"

    fake_messages = MagicMock()
    fake_messages.create.side_effect = [resp1, resp2]

    class FakeAnthropic:
        def __init__(self, **kwargs):
            self.messages = fake_messages

    monkeypatch.setattr(anth, "Anthropic", FakeAnthropic)

    p = mod.ClaudeProvider(
        {"api_key": "sk-ant-test-not-placeholder", "model": "claude-sonnet-4-20250514"}
    )
    p.client = MagicMock()
    p.client.messages = fake_messages

    tools = [ToolSpec("lookup", "lookup", {"type": "object", "properties": {"q": {"type": "string"}}})]
    handlers = {"lookup": lambda q: f"results for {q}"}

    out = p.generate("find ssrf", tools=tools, handlers=handlers)
    assert "SSRF" in out
    assert fake_messages.create.call_count == 2


def test_manager_generate_with_tools(monkeypatch):
    from ai_providers.provider_manager import AIProviderManager
    from ai_providers.tool_runtime import ToolSpec

    class FakeProv:
        def generate(self, prompt, **kwargs):
            if kwargs.get("tools") and kwargs.get("handlers"):
                from ai_providers.tool_runtime import run_tool_loop

                return run_tool_loop(self, prompt, kwargs["tools"], kwargs["handlers"])
            return "plain"

        def generate_with_tools(self, prompt, tools, messages=None, tool_results=None, system=None, **kwargs):
            from ai_providers.tool_runtime import ToolCall, ToolRoundResult

            if tool_results:
                return ToolRoundResult(text=f"used {tool_results[0]['content']}", tool_calls=[])
            return ToolRoundResult(
                text="",
                tool_calls=[ToolCall(id="1", name="ping", arguments={})],
                raw={"messages": [{"role": "user", "content": prompt}]},
            )

    mgr = AIProviderManager({"ai_providers": {}})
    mgr.providers = {"openai": FakeProv()}
    mgr.set_provider("openai")
    out = mgr.generate_with_tools(
        "hi",
        tools=[ToolSpec("ping", "ping", {"type": "object", "properties": {}})],
        handlers={"ping": lambda: "pong"},
    )
    assert "pong" in out
    assert mgr.supports_tools()
