"""Unit tests for shared adapter utilities in base.py."""

import json

import pytest

from tracer.utils.adapters.base import (
    _flatten_tool_calls,
    extract_query,
    first_not_none,
    flatten_input_messages,
    flatten_output_messages,
    guess_provider,
    parse_json_attr,
    set_io_value,
    strip_keys,
)

# ---------------------------------------------------------------------------
# parse_json_attr
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParseJsonAttr:
    def test_valid_json_object(self):
        assert parse_json_attr('{"a": 1}') == {"a": 1}

    def test_valid_json_array(self):
        assert parse_json_attr("[1, 2, 3]") == [1, 2, 3]

    def test_invalid_json_returns_original(self):
        assert parse_json_attr("hello world") == "hello world"

    def test_already_parsed_dict(self):
        assert parse_json_attr({"a": 1}) == {"a": 1}

    def test_already_parsed_list(self):
        assert parse_json_attr([1, 2]) == [1, 2]

    def test_none_returns_none(self):
        assert parse_json_attr(None) is None

    def test_int_returns_int(self):
        assert parse_json_attr(42) == 42

    def test_empty_string(self):
        assert parse_json_attr("") == ""

    def test_json_string_value(self):
        assert parse_json_attr('"hello"') == "hello"


# ---------------------------------------------------------------------------
# first_not_none
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFirstNotNone:
    def test_all_none(self):
        assert first_not_none(None, None, None) is None

    def test_first_value(self):
        assert first_not_none("a", "b") == "a"

    def test_second_value(self):
        assert first_not_none(None, "val") == "val"

    def test_zero_is_not_none(self):
        assert first_not_none(0, "fallback") == 0

    def test_empty_string_is_not_none(self):
        assert first_not_none("", "fallback") == ""

    def test_false_is_not_none(self):
        assert first_not_none(False, "fallback") is False

    def test_no_args(self):
        assert first_not_none() is None


# ---------------------------------------------------------------------------
# guess_provider
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGuessProvider:
    def test_openai_gpt(self):
        assert guess_provider("gpt-4o") == "openai"

    def test_openai_o1(self):
        assert guess_provider("o1-preview") == "openai"

    def test_openai_o3(self):
        assert guess_provider("o3-mini") == "openai"

    def test_openai_o4(self):
        assert guess_provider("o4-mini") == "openai"

    def test_openai_chatgpt(self):
        assert guess_provider("chatgpt-4o-latest") == "openai"

    def test_anthropic(self):
        assert guess_provider("claude-3.5-sonnet") == "anthropic"

    def test_google(self):
        assert guess_provider("gemini-2.0-flash") == "google"

    def test_cohere(self):
        assert guess_provider("command-r-plus") == "cohere"

    def test_mistralai(self):
        assert guess_provider("mistral-large") == "mistralai"

    def test_mixtral(self):
        assert guess_provider("mixtral-8x7b") == "mistralai"

    def test_meta_llama(self):
        assert guess_provider("llama-3.1-70b") == "meta"

    def test_deepseek(self):
        assert guess_provider("deepseek-chat") == "deepseek"

    def test_unknown_model(self):
        assert guess_provider("some-custom-model") == ""

    def test_case_insensitive(self):
        assert guess_provider("GPT-4o") == "openai"

    def test_case_insensitive_claude(self):
        assert guess_provider("Claude-3.5-Sonnet") == "anthropic"


# ---------------------------------------------------------------------------
# strip_keys
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStripKeys:
    def test_single_prefix(self):
        attrs = {"langfuse.type": "gen", "langfuse.model": "gpt", "llm.model": "gpt"}
        strip_keys(attrs, "langfuse.")
        assert "langfuse.type" not in attrs
        assert "langfuse.model" not in attrs
        assert attrs["llm.model"] == "gpt"

    def test_multiple_prefixes(self):
        attrs = {
            "gen_ai.system": "openai",
            "traceloop.kind": "wf",
            "fi.span.kind": "LLM",
        }
        strip_keys(attrs, "gen_ai.", "traceloop.")
        assert "gen_ai.system" not in attrs
        assert "traceloop.kind" not in attrs
        assert attrs["fi.span.kind"] == "LLM"

    def test_no_match(self):
        attrs = {"llm.model": "gpt", "fi.span.kind": "LLM"}
        strip_keys(attrs, "langfuse.")
        assert len(attrs) == 2

    def test_empty_dict(self):
        attrs = {}
        strip_keys(attrs, "anything.")
        assert attrs == {}


# ---------------------------------------------------------------------------
# set_io_value
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSetIoValue:
    def test_dict_value(self):
        attrs = {}
        set_io_value(attrs, "input", {"query": "hello"})
        assert attrs["input.value"] == '{"query": "hello"}'
        assert attrs["input.mime_type"] == "application/json"

    def test_list_value(self):
        attrs = {}
        set_io_value(attrs, "input", [{"role": "user"}])
        assert json.loads(attrs["input.value"]) == [{"role": "user"}]
        assert attrs["input.mime_type"] == "application/json"

    def test_string_value(self):
        attrs = {}
        set_io_value(attrs, "output", "Hello!")
        assert attrs["output.value"] == "Hello!"
        assert attrs["output.mime_type"] == "text/plain"

    def test_int_value(self):
        attrs = {}
        set_io_value(attrs, "output", 42)
        assert attrs["output.value"] == "42"
        assert attrs["output.mime_type"] == "text/plain"

    def test_none_value_is_noop(self):
        attrs = {}
        set_io_value(attrs, "input", None)
        assert "input.value" not in attrs
        assert "input.mime_type" not in attrs


# ---------------------------------------------------------------------------
# _flatten_tool_calls
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFlattenToolCalls:
    def test_structured_list(self):
        attrs = {}
        msg = {
            "tool_calls": [
                {
                    "id": "call_1",
                    "function": {"name": "get_weather", "arguments": '{"city": "NYC"}'},
                },
                {
                    "id": "call_2",
                    "function": {"name": "get_time", "arguments": "{}"},
                },
            ]
        }
        _flatten_tool_calls(msg, "pfx", attrs)
        assert attrs["pfx.tool_calls.0.tool_call.id"] == "call_1"
        assert attrs["pfx.tool_calls.0.tool_call.function.name"] == "get_weather"
        assert (
            attrs["pfx.tool_calls.0.tool_call.function.arguments"] == '{"city": "NYC"}'
        )
        assert attrs["pfx.tool_calls.1.tool_call.id"] == "call_2"
        assert attrs["pfx.tool_calls.1.tool_call.function.name"] == "get_time"

    def test_indexed_keys(self):
        attrs = {}
        msg = {
            "tool_calls.0.function.name": "search",
            "tool_calls.0.function.arguments": '{"q": "test"}',
            "tool_calls.1.function.name": "calc",
        }
        _flatten_tool_calls(msg, "pfx", attrs)
        assert attrs["pfx.tool_calls.0.tool_call.function.name"] == "search"
        assert attrs["pfx.tool_calls.1.tool_call.function.name"] == "calc"

    def test_no_tool_calls(self):
        attrs = {}
        _flatten_tool_calls({"role": "user", "content": "hi"}, "pfx", attrs)
        assert attrs == {}

    def test_non_dict_tool_call_skipped(self):
        attrs = {}
        msg = {"tool_calls": ["not_a_dict", {"id": "c1", "function": {"name": "fn"}}]}
        _flatten_tool_calls(msg, "pfx", attrs)
        assert "pfx.tool_calls.0.tool_call.id" not in attrs
        assert attrs["pfx.tool_calls.1.tool_call.function.name"] == "fn"


# ---------------------------------------------------------------------------
# flatten_input_messages
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFlattenInputMessages:
    def test_basic_messages(self):
        attrs = {}
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
        ]
        flatten_input_messages(msgs, attrs)
        assert attrs["llm.input_messages.0.message.role"] == "system"
        assert attrs["llm.input_messages.0.message.content"] == "You are helpful."
        assert attrs["llm.input_messages.1.message.role"] == "user"
        assert attrs["llm.input_messages.1.message.content"] == "Hi"

    def test_text_only_message(self):
        """Message with 'text' key but no 'role' defaults to user."""
        attrs = {}
        flatten_input_messages([{"text": "hello"}], attrs)
        assert attrs["llm.input_messages.0.message.role"] == "user"
        assert attrs["llm.input_messages.0.message.content"] == "hello"

    def test_multipart_content(self):
        attrs = {}
        msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image"},
                    {"type": "image_url", "image_url": {"url": "http://..."}},
                ],
            }
        ]
        flatten_input_messages(msgs, attrs)
        assert (
            attrs["llm.input_messages.0.message.contents.0.message_content.type"]
            == "text"
        )
        assert (
            attrs["llm.input_messages.0.message.contents.0.message_content.text"]
            == "Describe this image"
        )
        assert (
            attrs["llm.input_messages.0.message.contents.1.message_content.type"]
            == "image_url"
        )

    def test_with_tool_calls(self):
        attrs = {}
        msgs = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": "c1", "function": {"name": "fn1", "arguments": "{}"}}
                ],
            }
        ]
        flatten_input_messages(msgs, attrs)
        assert (
            attrs["llm.input_messages.0.message.tool_calls.0.tool_call.function.name"]
            == "fn1"
        )

    def test_not_a_list_is_noop(self):
        attrs = {}
        flatten_input_messages("not a list", attrs)
        assert attrs == {}

    def test_non_dict_items_skipped(self):
        attrs = {}
        flatten_input_messages(["not_a_dict", {"role": "user", "content": "ok"}], attrs)
        assert "llm.input_messages.0.message.role" not in attrs
        assert attrs["llm.input_messages.1.message.role"] == "user"


# ---------------------------------------------------------------------------
# flatten_output_messages
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFlattenOutputMessages:
    def test_string_output(self):
        attrs = {}
        flatten_output_messages("Hello!", attrs)
        assert attrs["llm.output_messages.0.message.role"] == "assistant"
        assert attrs["llm.output_messages.0.message.content"] == "Hello!"
        assert attrs["response"] == "Hello!"

    def test_dict_with_content(self):
        attrs = {}
        flatten_output_messages({"role": "assistant", "content": "Sure"}, attrs)
        assert attrs["llm.output_messages.0.message.role"] == "assistant"
        assert attrs["llm.output_messages.0.message.content"] == "Sure"
        assert attrs["response"] == "Sure"

    def test_dict_with_text_key(self):
        attrs = {}
        flatten_output_messages({"text": "Hi there"}, attrs)
        assert attrs["llm.output_messages.0.message.content"] == "Hi there"
        assert attrs["response"] == "Hi there"

    def test_dict_tool_calls_only(self):
        """Assistant message with empty content but tool_calls should not be dropped."""
        attrs = {}
        msg = {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": "c1", "function": {"name": "fn", "arguments": "{}"}}],
        }
        flatten_output_messages(msg, attrs)
        assert attrs["llm.output_messages.0.message.role"] == "assistant"
        assert (
            attrs["llm.output_messages.0.message.tool_calls.0.tool_call.function.name"]
            == "fn"
        )
        assert "response" not in attrs  # No content → no response

    def test_dict_content_plus_tool_calls(self):
        attrs = {}
        msg = {
            "role": "assistant",
            "content": "Let me check.",
            "tool_calls": [
                {"id": "c1", "function": {"name": "search", "arguments": "{}"}}
            ],
        }
        flatten_output_messages(msg, attrs)
        assert attrs["response"] == "Let me check."
        assert (
            attrs["llm.output_messages.0.message.tool_calls.0.tool_call.function.name"]
            == "search"
        )

    def test_list_of_messages(self):
        attrs = {}
        msgs = [
            {"role": "assistant", "content": "First"},
            {"role": "assistant", "content": "Second"},
        ]
        flatten_output_messages(msgs, attrs)
        assert attrs["llm.output_messages.0.message.content"] == "First"
        assert attrs["llm.output_messages.1.message.content"] == "Second"
        assert attrs["response"] == "First"  # First non-empty content

    def test_list_with_tool_calls(self):
        attrs = {}
        msgs = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": "c1", "function": {"name": "fn", "arguments": "{}"}}
                ],
            }
        ]
        flatten_output_messages(msgs, attrs)
        assert (
            attrs["llm.output_messages.0.message.tool_calls.0.tool_call.function.name"]
            == "fn"
        )

    def test_list_with_indexed_tool_calls(self):
        attrs = {}
        msgs = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls.0.function.name": "indexed_fn",
                "tool_calls.0.function.arguments": "{}",
            }
        ]
        flatten_output_messages(msgs, attrs)
        assert (
            attrs["llm.output_messages.0.message.tool_calls.0.tool_call.function.name"]
            == "indexed_fn"
        )

    def test_not_a_recognized_type(self):
        attrs = {}
        flatten_output_messages(12345, attrs)
        assert attrs == {}

    def test_dict_no_content_no_tool_calls(self):
        attrs = {}
        flatten_output_messages({"role": "assistant"}, attrs)
        assert attrs == {}


# ---------------------------------------------------------------------------
# extract_query
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExtractQuery:
    def test_basic(self):
        attrs = {}
        msgs = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"},
        ]
        extract_query(msgs, attrs)
        assert attrs["query"] == "Hello!"

    def test_multi_user_takes_last(self):
        attrs = {}
        msgs = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Reply"},
            {"role": "user", "content": "Second"},
        ]
        extract_query(msgs, attrs)
        assert attrs["query"] == "Second"

    def test_no_user_message(self):
        attrs = {}
        extract_query([{"role": "system", "content": "sys"}], attrs)
        assert "query" not in attrs

    def test_content_is_list(self):
        attrs = {}
        content = [{"type": "text", "text": "Hello"}]
        extract_query([{"role": "user", "content": content}], attrs)
        assert attrs["query"] == json.dumps(content)

    def test_not_a_list_is_noop(self):
        attrs = {}
        extract_query("not a list", attrs)
        assert attrs == {}

    def test_empty_list(self):
        attrs = {}
        extract_query([], attrs)
        assert "query" not in attrs
