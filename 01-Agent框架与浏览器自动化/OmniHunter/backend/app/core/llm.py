"""LLM 客户端：多模型多协议 + tool calling，借鉴 AutoHunter 的 tool_compat 兼容策略。

支持协议（llm_protocol / llm_small_protocol）：
- openai    : 所有 OpenAI 兼容端点（DeepSeek / Qwen / Kimi / GLM / OpenRouter /
              硅基流动 / Ollama / LM Studio / Gemini OpenAI 兼容端点 ...）
- anthropic : Claude 官方 messages 协议（tool calling 走提示词模拟）

兼容模式（tool_compat，仅 openai 协议生效）：
- native: 仅使用原生 function calling（模型必须支持）
- prompt: 强制提示词模拟（哑模型用）
- auto  : 原生优先，失败回退提示词模拟
"""
import json
from typing import Any, Callable

import httpx
from openai import OpenAI

from ..config import get_settings


class LLMClient:
    def __init__(self, settings=None, api_key: str | None = None,
                 base_url: str | None = None, model: str | None = None,
                 protocol: str | None = None):
        self.settings = settings or get_settings()
        self.api_key = api_key or self.settings.llm_api_key or "empty"
        self.base_url = base_url or self.settings.llm_base_url
        self.model = model or self.settings.llm_model
        self.protocol = (protocol or self.settings.llm_protocol or "openai").lower()
        self._client: OpenAI | None = None

    @classmethod
    def small(cls, settings=None) -> "LLMClient":
        """小模型层客户端；未配置小模型时回退大模型。"""
        s = settings or get_settings()
        if not s.llm_small_model:
            return cls(settings=s)
        return cls(
            settings=s,
            api_key=s.llm_small_api_key or "empty",
            base_url=s.llm_small_base_url or s.llm_base_url,
            model=s.llm_small_model,
            protocol=s.llm_small_protocol,
        )

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def chat(self, messages: list[dict], temperature: float = 0.3) -> str:
        if self.protocol == "anthropic":
            return self._chat_anthropic(messages, temperature)
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=temperature
        )
        return resp.choices[0].message.content or ""

    def _chat_anthropic(self, messages: list[dict], temperature: float) -> str:
        """Claude messages 协议（httpx 同步实现，不引入 anthropic SDK）。"""
        system_parts = [m["content"] for m in messages if m.get("role") == "system"]
        turns = [m for m in messages if m.get("role") != "system"]
        # base_url 兼容：主域或带 /v1 结尾均可
        base = self.base_url.rstrip("/")
        if base.endswith("/v1"):
            base = base[: -len("/v1")]
        resp = httpx.post(
            f"{base}/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 4096,
                "temperature": temperature,
                "system": "\n\n".join(system_parts) or None,
                "messages": [{"role": m["role"], "content": m["content"]}
                             for m in turns],
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        return "".join(
            block.get("text", "") for block in data.get("content", [])
            if block.get("type") == "text"
        )

    def chat_json(self, messages: list[dict], temperature: float = 0.2) -> Any:
        text = self.chat(messages, temperature=temperature)
        return _safe_json(text)

    def react(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_executor: Callable[[str, dict], str],
        max_steps: int = 8,
        temperature: float = 0.3,
        on_step: Callable[[dict], None] | None = None,
    ) -> tuple[str, list[dict]]:
        """带工具调用的 ReAct 循环。

        tools 为 OpenAI function-calling 格式。tool_executor(name, args)->str。
        on_step 回调每一步用于事件流上报。
        """
        compat = self.settings.tool_compat
        # anthropic 协议暂走提示词模拟工具调用；openai 协议按 compat 决定
        use_native = self.protocol == "openai" and compat != "prompt"
        history = list(messages)
        last_text = ""

        for _ in range(max_steps):
            if use_native and tools:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=history,
                    tools=tools,
                    tool_choice="auto",
                    temperature=temperature,
                )
            else:
                # 提示词模拟：把工具描述注入 system
                injected = _inject_tools_prompt(history, tools)
                resp = self.client.chat.completions.create(
                    model=self.model, messages=injected, temperature=temperature
                )
            msg = resp.choices[0].message
            history.append(msg.model_dump(exclude_none=True))

            tool_calls = getattr(msg, "tool_calls", None)
            if use_native and tool_calls:
                for tc in tool_calls:
                    name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    result = tool_executor(name, args)
                    if on_step:
                        on_step({"tool": name, "args": args, "result": result})
                    history.append(
                        {"role": "tool", "tool_call_id": tc.id, "content": str(result)}
                    )
                continue
            # 提示词模拟模式：尝试解析文本里的工具调用
            if not use_native:
                parsed = _parse_prompt_tool_call(msg.content or "")
                if parsed:
                    name, args = parsed
                    result = tool_executor(name, args)
                    if on_step:
                        on_step({"tool": name, "args": args, "result": result})
                    history.append(
                        {"role": "user", "content": f"工具 {name} 执行结果:\n{result}"}
                    )
                    continue
            last_text = msg.content or ""
            return last_text, history

        return last_text, history


def _safe_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    return None


def _inject_tools_prompt(history: list[dict], tools: list[dict]) -> list[dict]:
    if not tools:
        return history
    desc = "\n".join(
        f"- {t['function']['name']}: {t['function'].get('description', '')}"
        for t in tools
    )
    guide = (
        "你可调用以下工具。需要调用时，输出一行 JSON："
        '{"tool":"工具名","args":{...}}\n可用工具：\n' + desc
    )
    out = list(history)
    if out and out[0]["role"] == "system":
        out[0] = {**out[0], "content": out[0]["content"] + "\n\n" + guide}
    else:
        out.insert(0, {"role": "system", "content": guide})
    return out


def _parse_prompt_tool_call(text: str) -> tuple[str, dict] | None:
    idx = text.find('{"tool"')
    if idx < 0:
        idx = text.find("{\n  \"tool\"")
    if idx < 0:
        return None
    end = text.find("}", idx)
    if end < 0:
        return None
    try:
        obj = json.loads(text[idx : end + 1])
        return obj.get("tool"), obj.get("args", {})
    except json.JSONDecodeError:
        return None
