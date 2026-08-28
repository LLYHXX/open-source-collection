"""OpenAI chat-completions provider (current GPT / o-series models + tools)."""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional, Union

from utils.logger import get_logger

logger = get_logger(__name__)

OPENAI_MODELS: List[str] = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4.1-nano",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "o1",
    "o1-mini",
    "o3-mini",
    "o4-mini",
]

_SYSTEM = (
    "You are a security expert specializing in penetration testing "
    "and vulnerability research."
)


def is_reasoning_model(model: str) -> bool:
    m = (model or "").lower().split("/")[-1]
    return m.startswith("o1") or m.startswith("o3") or m.startswith("o4")


class OpenAIProvider:
    def __init__(self, config: Dict):
        self.config = config or {}
        self.api_key = (self.config.get("api_key") or "").strip()
        self.model = self.config.get("model") or "gpt-4o"
        self.temperature = float(self.config.get("temperature", 0.7))
        self.max_tokens = int(self.config.get("max_tokens", 2000) or 2000)
        self.base_url = (self.config.get("base_url") or "").strip() or None
        self.timeout = float(self.config.get("timeout", 60) or 60)
        self.organization = (self.config.get("organization") or "").strip() or None

        if (
            not self.api_key
            or self.api_key.startswith("your-")
            or self.api_key.startswith("sk-your")
        ):
            raise ValueError("OpenAI API key not provided or still a placeholder")

        from openai import OpenAI

        kwargs = {"api_key": self.api_key, "timeout": self.timeout}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        if self.organization:
            kwargs["organization"] = self.organization
        self.client = OpenAI(**kwargs)

    def list_models(self) -> List[str]:
        known = list(OPENAI_MODELS)
        try:
            page = self.client.models.list()
            ids = []
            for m in getattr(page, "data", None) or []:
                mid = getattr(m, "id", None)
                if mid and (
                    "gpt" in mid
                    or mid.startswith("o1")
                    or mid.startswith("o3")
                    or mid.startswith("o4")
                ):
                    ids.append(mid)
            if ids:
                return list(dict.fromkeys(ids + known))
        except Exception as e:
            logger.debug(f"OpenAI models.list failed: {e}")
        return known

    def generate(self, prompt: str, **kwargs) -> str:
        tools = kwargs.pop("tools", None)
        handlers = kwargs.pop("handlers", None)
        if tools and handlers:
            from ai_providers.tool_runtime import run_tool_loop

            return run_tool_loop(
                self,
                prompt,
                tools,
                handlers,
                max_rounds=int(kwargs.pop("max_tool_rounds", 5) or 5),
                **kwargs,
            )

        model = kwargs.get("model") or self.model
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = int(kwargs.get("max_tokens", self.max_tokens) or self.max_tokens)
        system = kwargs.get("system") or _SYSTEM

        try:
            if is_reasoning_model(model):
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": f"{system}\n\n{prompt}"}],
                    max_completion_tokens=max_tokens,
                )
            else:
                response = self._chat_create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            return _extract_openai_text(response)
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise

    def generate_with_tools(
        self,
        prompt: str,
        tools: List[Any],
        messages: Optional[List[Dict]] = None,
        tool_results: Optional[List[Dict]] = None,
        system: Optional[str] = None,
        **kwargs,
    ):
        from ai_providers.tool_runtime import (
            ToolCall,
            ToolRoundResult,
            normalize_tools,
            parse_json_args,
        )

        model = kwargs.get("model") or self.model
        if is_reasoning_model(model):
            # tool calling unreliable on o-series — text only
            text = self.generate(prompt, system=system, model=model, **{
                k: v for k, v in kwargs.items() if k not in ("model",)
            })
            return ToolRoundResult(text=text, finish_reason="stop")

        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = int(kwargs.get("max_tokens", self.max_tokens) or self.max_tokens)
        system = system or _SYSTEM
        specs = normalize_tools(tools)
        openai_tools = [s.to_openai() for s in specs]

        if messages is None:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        else:
            messages = list(messages)

        if tool_results:
            for tr in tool_results:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr.get("id") or "",
                        "content": tr.get("content") or "",
                    }
                )

        try:
            response = self._chat_create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=openai_tools,
                tool_choice=kwargs.get("tool_choice", "auto"),
            )
        except Exception as e:
            logger.error(f"OpenAI tool call error: {e}")
            raise

        choice = response.choices[0]
        msg = getattr(choice, "message", None)
        finish = getattr(choice, "finish_reason", "") or ""
        text = (getattr(msg, "content", None) or "") if msg is not None else ""
        text = text.strip() if isinstance(text, str) else ""

        raw_calls = getattr(msg, "tool_calls", None) if msg is not None else None
        tool_calls: List[ToolCall] = []
        if raw_calls:
            assistant_msg = {
                "role": "assistant",
                "content": getattr(msg, "content", None),
                "tool_calls": [],
            }
            for tc in raw_calls:
                tc_id = getattr(tc, "id", None) or str(uuid.uuid4())
                fn = getattr(tc, "function", None)
                name = getattr(fn, "name", None) if fn is not None else None
                args_raw = getattr(fn, "arguments", None) if fn is not None else "{}"
                if name is None and isinstance(tc, dict):
                    tc_id = tc.get("id") or tc_id
                    fn = tc.get("function") or {}
                    name = fn.get("name")
                    args_raw = fn.get("arguments")
                args = parse_json_args(args_raw)
                tool_calls.append(ToolCall(id=tc_id, name=name or "", arguments=args))
                assistant_msg["tool_calls"].append(
                    {
                        "id": tc_id,
                        "type": "function",
                        "function": {
                            "name": name or "",
                            "arguments": args_raw
                            if isinstance(args_raw, str)
                            else json.dumps(args),
                        },
                    }
                )
            messages.append(assistant_msg)

        result = ToolRoundResult(
            text=text,
            tool_calls=tool_calls,
            raw={"messages": messages, "response": response},
            finish_reason=str(finish),
        )
        result.messages = messages  # type: ignore[attr-defined]
        return result

    def _chat_create(
        self,
        model: str,
        messages: List[Dict],
        temperature: float,
        max_tokens: int,
        tools: Optional[List] = None,
        tool_choice: Any = None,
    ):
        base = {"model": model, "messages": messages, "temperature": temperature}
        if tools:
            base["tools"] = tools
            if tool_choice is not None:
                base["tool_choice"] = tool_choice
        try:
            return self.client.chat.completions.create(
                max_completion_tokens=max_tokens, **base
            )
        except TypeError:
            return self.client.chat.completions.create(max_tokens=max_tokens, **base)
        except Exception as e:
            if "max_completion_tokens" in str(e).lower():
                return self.client.chat.completions.create(max_tokens=max_tokens, **base)
            raise


def _extract_openai_text(response) -> str:
    choice = response.choices[0]
    msg = getattr(choice, "message", None)
    content = getattr(msg, "content", None) if msg is not None else None
    if content is None and isinstance(choice, dict):
        content = (choice.get("message") or {}).get("content")
    text = (content or "").strip() if isinstance(content, str) else str(content or "").strip()
    if not text:
        raise RuntimeError("empty OpenAI response")
    return text
