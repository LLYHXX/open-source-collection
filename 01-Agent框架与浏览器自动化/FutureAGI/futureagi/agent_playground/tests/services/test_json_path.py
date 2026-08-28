"""Tests for JSON dot notation utilities."""

import pytest

from agent_playground.services.engine.utils.json_path import (
    ParsedVariable,
    extract_json_path,
    get_output_schema_for_response_format,
    parse_variable,
    resolve_variable,
)

# =============================================================================
# parse_variable
# =============================================================================


@pytest.mark.unit
class TestParseVariable:
    """Tests for parse_variable()."""

    def test_simple_variable(self):
        result = parse_variable("question")
        assert result == ParsedVariable(
            parent_node_name=None,
            output_port_name=None,
            extraction_path=None,
            is_dot_notation=False,
        )

    def test_two_segments_no_extraction(self):
        result = parse_variable("Node1.response_1")
        assert result == ParsedVariable(
            parent_node_name="Node1",
            output_port_name="response_1",
            extraction_path=None,
            is_dot_notation=True,
        )

    def test_three_segments_with_extraction(self):
        result = parse_variable("Node1.response_1.data")
        assert result == ParsedVariable(
            parent_node_name="Node1",
            output_port_name="response_1",
            extraction_path=".data",
            is_dot_notation=True,
        )

    def test_deep_nested_extraction(self):
        result = parse_variable("Node1.response_1.data.name")
        assert result == ParsedVariable(
            parent_node_name="Node1",
            output_port_name="response_1",
            extraction_path=".data.name",
            is_dot_notation=True,
        )

    def test_array_index_extraction(self):
        result = parse_variable("Node1.response_1[0]")
        assert result == ParsedVariable(
            parent_node_name="Node1",
            output_port_name="response_1",
            extraction_path="[0]",
            is_dot_notation=True,
        )

    def test_array_index_with_key(self):
        result = parse_variable("Node1.response_1[0].key")
        assert result == ParsedVariable(
            parent_node_name="Node1",
            output_port_name="response_1",
            extraction_path="[0].key",
            is_dot_notation=True,
        )

    def test_mixed_dot_and_bracket(self):
        result = parse_variable("Node1.response.items[2].name")
        assert result == ParsedVariable(
            parent_node_name="Node1",
            output_port_name="response",
            extraction_path=".items[2].name",
            is_dot_notation=True,
        )

    def test_single_word(self):
        result = parse_variable("x")
        assert result.is_dot_notation is False
        assert result.parent_node_name is None

    def test_underscored_names(self):
        result = parse_variable("my_node.my_port.my_key")
        assert result.parent_node_name == "my_node"
        assert result.output_port_name == "my_port"
        assert result.extraction_path == ".my_key"


# =============================================================================
# extract_json_path
# =============================================================================


@pytest.mark.unit
class TestExtractJsonPath:
    """Tests for extract_json_path()."""

    def test_simple_key(self):
        assert extract_json_path({"name": "Alice"}, ".name") == "Alice"

    def test_nested_key(self):
        data = {"data": {"name": "Alice"}}
        assert extract_json_path(data, ".data.name") == "Alice"

    def test_deeply_nested(self):
        data = {"a": {"b": {"c": {"d": 42}}}}
        assert extract_json_path(data, ".a.b.c.d") == 42

    def test_array_index(self):
        assert extract_json_path(["a", "b", "c"], "[1]") == "b"

    def test_array_index_zero(self):
        assert extract_json_path([{"key": "v"}], "[0].key") == "v"

    def test_nested_array(self):
        data = {"items": [1, 2, 3]}
        assert extract_json_path(data, ".items[1]") == 2

    def test_negative_index(self):
        assert extract_json_path(["a", "b", "c"], "[-1]") == "c"

    def test_complex_nested(self):
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        assert extract_json_path(data, ".users[1].name") == "Bob"

    def test_missing_key_raises(self):
        with pytest.raises(ValueError, match="Key 'missing' not found"):
            extract_json_path({"a": 1}, ".missing")

    def test_index_out_of_range_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            extract_json_path([1, 2], "[5]")

    def test_key_on_non_dict_raises(self):
        with pytest.raises(ValueError, match="expected dict"):
            extract_json_path("not a dict", ".key")

    def test_index_on_non_list_raises(self):
        with pytest.raises(ValueError, match="expected list/tuple"):
            extract_json_path({"a": 1}, "[0]")

    def test_returns_dict(self):
        data = {"a": {"b": {"c": 1}}}
        assert extract_json_path(data, ".a.b") == {"c": 1}

    def test_returns_list(self):
        data = {"items": [1, 2, 3]}
        assert extract_json_path(data, ".items") == [1, 2, 3]


# =============================================================================
# resolve_variable
# =============================================================================


@pytest.mark.unit
class TestResolveVariable:
    """Tests for resolve_variable()."""

    def test_simple_variable(self):
        result = resolve_variable("question", {"question": "What is AI?"})
        assert result == "What is AI?"

    def test_port_reference_no_extraction(self):
        result = resolve_variable("Node1.response", {"Node1.response": "Hello"})
        assert result == "Hello"

    def test_port_reference_with_extraction(self):
        inputs = {"Node1.response.name": {"name": "Alice", "age": 30}}
        result = resolve_variable("Node1.response.name", inputs)
        assert result == "Alice"

    def test_array_extraction(self):
        inputs = {"Node1.response[0]": ["first", "second"]}
        result = resolve_variable("Node1.response[0]", inputs)
        assert result == "first"

    def test_deep_extraction(self):
        inputs = {"Node1.response.users[0].name": {"users": [{"name": "Alice"}]}}
        result = resolve_variable("Node1.response.users[0].name", inputs)
        assert result == "Alice"

    def test_extraction_failure_raises(self):
        """When extraction fails and variable is in inputs, raise ValueError."""
        inputs = {"Node1.response.missing_key": {"other": "data"}}
        with pytest.raises(ValueError):
            resolve_variable("Node1.response.missing_key", inputs)

    def test_variable_not_in_inputs_raises(self):
        with pytest.raises(ValueError, match="not found"):
            resolve_variable("nonexistent", {"other": "data"})

    def test_returns_structured_data(self):
        """Non-string values are returned as-is."""
        inputs = {"data": {"key": "value"}}
        result = resolve_variable("data", inputs)
        assert result == {"key": "value"}

    def test_returns_list_data(self):
        inputs = {"items": [1, 2, 3]}
        result = resolve_variable("items", inputs)
        assert result == [1, 2, 3]


# =============================================================================
# get_output_schema_for_response_format
# =============================================================================


@pytest.mark.unit
class TestGetOutputSchemaForResponseFormat:
    """Tests for get_output_schema_for_response_format() — string-only cases (no DB)."""

    def test_text_format(self):
        schema = get_output_schema_for_response_format("text")
        assert schema["type"] == "string"

    def test_none_format(self):
        schema = get_output_schema_for_response_format(None)
        assert schema["type"] == "string"

    def test_json_format(self):
        schema = get_output_schema_for_response_format("json")
        assert schema["type"] == "object"

    def test_unknown_string_format(self):
        """Non-UUID unknown string falls back to string type."""
        schema = get_output_schema_for_response_format("unknown")
        assert schema["type"] == "string"


@pytest.mark.unit
class TestGetOutputSchemaForResponseFormatDB:
    """Tests for get_output_schema_for_response_format() with UserResponseSchema DB lookup."""

    def test_uuid_string_fetches_from_db(self, db):
        """UUID string response_format fetches schema from UserResponseSchema."""
        from model_hub.models.run_prompt import UserResponseSchema

        stored_schema = {
            "type": "object",
            "required": ["summary"],
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "The generated summary.",
                }
            },
            "additional_properties": False,
        }
        urs = UserResponseSchema.no_workspace_objects.create(
            name="test-schema",
            schema=stored_schema,
        )
        schema = get_output_schema_for_response_format(str(urs.id))
        assert schema == stored_schema

    def test_uuid_string_not_found_fallback(self, db):
        """UUID string pointing to nonexistent record falls back to string type."""
        import uuid

        fake_uuid = str(uuid.uuid4())
        schema = get_output_schema_for_response_format(fake_uuid)
        assert schema["type"] == "string"

    def test_uuid_string_schema_preserved_exactly(self, db):
        """Schema fetched from DB preserves all fields exactly — required, descriptions, additional_properties."""
        from model_hub.models.run_prompt import UserResponseSchema

        stored_schema = {
            "type": "object",
            "required": ["city", "population"],
            "properties": {
                "city": {"type": "string", "description": "City name."},
                "population": {"type": "integer", "description": "City population."},
                "landmarks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Notable landmarks.",
                },
            },
            "additional_properties": False,
        }
        urs = UserResponseSchema.no_workspace_objects.create(
            name="city-schema",
            schema=stored_schema,
        )
        schema = get_output_schema_for_response_format(str(urs.id))
        assert schema == stored_schema
        assert schema["required"] == ["city", "population"]
        assert schema["additional_properties"] is False
        assert schema["properties"]["landmarks"]["type"] == "array"
