"""Shared tool-calling helpers for AI providers."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

ToolHandler = Callable[..., Any]


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})

    def to_openai(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters or {"type": "object", "properties": {}},
            },
        }

    def to_anthropic(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters or {"type": "object", "properties": {}},
        }


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolRoundResult:
    text: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    raw: Any = None
    finish_reason: str = ""


def normalize_tools(tools: Optional[List[Union[ToolSpec, Dict]]]) -> List[ToolSpec]:
    out: List[ToolSpec] = []
    for t in tools or []:
        if isinstance(t, ToolSpec):
            out.append(t)
            continue
        if not isinstance(t, dict):
            continue
        # OpenAI shape
        if t.get("type") == "function" and isinstance(t.get("function"), dict):
            fn = t["function"]
            out.append(
                ToolSpec(
                    name=fn.get("name") or "",
                    description=fn.get("description") or "",
                    parameters=fn.get("parameters") or {"type": "object", "properties": {}},
                )
            )
            continue
        # Anthropic / flat shape
        name = t.get("name") or ""
        if name:
            out.append(
                ToolSpec(
                    name=name,
                    description=t.get("description") or "",
                    parameters=t.get("parameters")
                    or t.get("input_schema")
                    or {"type": "object", "properties": {}},
                )
            )
    return [t for t in out if t.name]


def parse_json_args(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        try:
            val = json.loads(raw)
            return val if isinstance(val, dict) else {"value": val}
        except Exception:
            return {"_raw": raw}
    return {"value": raw}


def run_handlers(
    calls: List[ToolCall],
    handlers: Dict[str, ToolHandler],
) -> List[Dict[str, Any]]:
    """Execute tool calls; return list of {id, name, content}."""
    results = []
    for call in calls:
        fn = handlers.get(call.name)
        if not fn:
            content = json.dumps({"error": f"unknown tool: {call.name}"})
        else:
            try:
                args = call.arguments if isinstance(call.arguments, dict) else {}
                out = fn(**args) if args else fn()
                if not isinstance(out, str):
                    out = json.dumps(out, default=str)
                content = out
            except TypeError:
                try:
                    out = fn(call.arguments)
                    content = out if isinstance(out, str) else json.dumps(out, default=str)
                except Exception as e:
                    content = json.dumps({"error": str(e)})
            except Exception as e:
                content = json.dumps({"error": str(e)})
        results.append({"id": call.id, "name": call.name, "content": content})
    return results


def run_tool_loop(
    provider,
    prompt: str,
    tools: List[Union[ToolSpec, Dict]],
    handlers: Dict[str, ToolHandler],
    *,
    max_rounds: int = 5,
    system: Optional[str] = None,
    **kwargs,
) -> str:
    """
    Multi-round tool calling until model returns text only or max_rounds.
    Requires provider.generate_with_tools(prompt|messages, tools=..., tool_results=...).
    """
    specs = normalize_tools(tools)
    if not specs:
        return provider.generate(prompt, system=system, **kwargs) if system else provider.generate(prompt, **kwargs)

    if not hasattr(provider, "generate_with_tools"):
        # fallback: ignore tools
        return provider.generate(prompt, system=system, **kwargs) if system else provider.generate(prompt, **kwargs)

    messages: Optional[List[Dict]] = None
    tool_results = None
    last_text = ""

    for _ in range(max(1, int(max_rounds))):
        round_result: ToolRoundResult = provider.generate_with_tools(
            prompt,
            tools=specs,
            messages=messages,
            tool_results=tool_results,
            system=system,
            **kwargs,
        )
        last_text = (round_result.text or "").strip()
        if not round_result.tool_calls:
            return last_text or ""

        executed = run_handlers(round_result.tool_calls, handlers)
        # provider may stash conversation state on result.raw
        messages = getattr(round_result, "messages", None) or (
            round_result.raw.get("messages") if isinstance(round_result.raw, dict) else None
        )
        tool_results = executed
        # continue loop with same prompt; providers use messages/tool_results

    return last_text
