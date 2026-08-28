"""Comprehensive tests for port serializers."""

import uuid

import pytest

from agent_playground.models.choices import NodeType, PortDirection
from agent_playground.models.node import Node
from agent_playground.models.port import Port
from agent_playground.serializers.port import (
    PortCreateSerializer,
    PortReadSerializer,
    PortWriteSerializer,
    UpdatePortSerializer,
)


class TestPortReadSerializer:
    """Tests for PortReadSerializer."""

    def test_serializes_all_port_fields(self, input_port):
        """Test that all port fields are serialized correctly."""
        serializer = PortReadSerializer(input_port)
        data = serializer.data

        assert data["id"] == str(input_port.id)
        assert data["key"] == input_port.key
        assert data["direction"] == input_port.direction
        assert data["data_schema"] == input_port.data_schema
        assert data["required"] == input_port.required
        assert data["default_value"] == input_port.default_value
        assert data["metadata"] == input_port.metadata

    def test_serializes_input_port_direction(self, input_port):
        """Test serialization of input port direction."""
        serializer = PortReadSerializer(input_port)
        assert serializer.data["direction"] == PortDirection.INPUT

    def test_serializes_output_port_direction(self, output_port):
        """Test serialization of output port direction."""
        serializer = PortReadSerializer(output_port)
        assert serializer.data["direction"] == PortDirection.OUTPUT

    def test_serializes_port_with_default_value(self, dynamic_node):
        """Test serialization of port with default value."""
        port = Port.no_workspace_objects.create(
            node=dynamic_node,
            key="custom",
            display_name="with_default",
            direction=PortDirection.INPUT,
            data_schema={"type": "string"},
            required=False,
            default_value="default_text",
        )
        serializer = PortReadSerializer(port)
        assert serializer.data["default_value"] == "default_text"
        assert serializer.data["required"] is False

    def test_serializes_port_with_complex_schema(self, dynamic_node):
        """Test serialization of port with complex JSON schema."""
        complex_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["name"],
        }
        port = Port.no_workspace_objects.create(
            node=dynamic_node,
            key="custom",
            display_name="complex_port",
            direction=PortDirection.INPUT,
            data_schema=complex_schema,
        )
        serializer = PortReadSerializer(port)
        assert serializer.data["data_schema"] == complex_schema

    def test_serializes_port_with_metadata(self, dynamic_node):
        """Test serialization of port with metadata."""
        metadata = {
            "description": "A test port",
            "example": "Hello world",
            "ui_hints": {"color": "blue"},
        }
        port = Port.no_workspace_objects.create(
            node=dynamic_node,
            key="custom",
            display_name="with_metadata",
            direction=PortDirection.OUTPUT,
            metadata=metadata,
        )
        serializer = PortReadSerializer(port)
        assert serializer.data["metadata"] == metadata

    def test_serializes_many_ports(self, input_port, output_port):
        """Test serialization of multiple ports."""
        serializer = PortReadSerializer([input_port, output_port], many=True)
        data = serializer.data

        assert len(data) == 2
        directions = {p["direction"] for p in data}
        assert PortDirection.INPUT in directions
        assert PortDirection.OUTPUT in directions

    def test_all_fields_are_read_only(self):
        """Test that all fields in PortReadSerializer are read-only."""
        serializer = PortReadSerializer()
        for field_name in serializer.fields:
            assert serializer.fields[field_name].read_only


class TestPortWriteSerializer:
    """Tests for PortWriteSerializer."""

    # ==================== Valid Data Tests ====================

    def test_valid_input_port_minimal(self):
        """Test validation of minimal valid input port data."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "test_input",
            "display_name": "test_input",
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["key"] == "test_input"
        assert serializer.validated_data["direction"] == PortDirection.INPUT

    def test_valid_output_port_minimal(self):
        """Test validation of minimal valid output port data."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "test_output",
            "display_name": "test_output",
            "direction": PortDirection.OUTPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["direction"] == PortDirection.OUTPUT

    def test_valid_port_with_all_fields(self):
        """Test validation with all optional fields provided."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "full_port",
            "display_name": "full_port",
            "direction": PortDirection.INPUT,
            "data_schema": {
                "type": "object",
                "properties": {"foo": {"type": "string"}},
            },
            "required": False,
            "default_value": {"foo": "bar"},
            "metadata": {"description": "A fully configured port", "version": 1},
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["required"] is False
        assert serializer.validated_data["default_value"] == {"foo": "bar"}
        assert (
            serializer.validated_data["metadata"]["description"]
            == "A fully configured port"
        )

    def test_valid_port_with_complex_data_schema(self):
        """Test validation with complex JSON schema."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "complex_input",
            "display_name": "complex_input",
            "direction": PortDirection.INPUT,
            "data_schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "value": {"type": "string"},
                    },
                },
                "minItems": 1,
            },
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_port_with_null_default_value(self):
        """Test validation with explicit null default value."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "nullable_port",
            "display_name": "nullable_port",
            "direction": PortDirection.INPUT,
            "default_value": None,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["default_value"] is None

    # ==================== Required Field Validation Tests ====================

    def test_missing_id_fails(self):
        """Test that missing id fails validation."""
        data = {
            "key": "test_input",
            "display_name": "test_input",
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_missing_key_fails(self):
        """Test that missing key fails validation."""
        data = {
            "temp_id": "port-1",
            "display_name": "test_input",
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "key" in serializer.errors

    def test_missing_direction_fails(self):
        """Test that missing direction fails validation."""
        data = {
            "temp_id": "port-1",
            "key": "test_input",
            "display_name": "test_input",
        }
        serializer = PortWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "direction" in serializer.errors

    def test_empty_data_fails(self):
        """Test that empty data fails validation."""
        serializer = PortWriteSerializer(data={})
        assert not serializer.is_valid()
        assert "id" in serializer.errors
        assert "key" in serializer.errors
        assert "direction" in serializer.errors

    # ==================== Invalid Value Tests ====================

    def test_invalid_direction_fails(self):
        """Test that invalid direction fails validation."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "test_input",
            "display_name": "test_input",
            "direction": "invalid",
        }
        serializer = PortWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "direction" in serializer.errors

    def test_empty_id_fails(self):
        """Test that empty id fails validation."""
        data = {
            "id": "",
            "key": "test_input",
            "display_name": "test_input",
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "id" in serializer.errors

    def test_empty_key_fails(self):
        """Test that empty key fails validation."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "",
            "display_name": "",
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "key" in serializer.errors

    def test_key_too_long_fails(self):
        """Test that key exceeding max length fails validation."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "a" * 101,  # Max is 100
            "display_name": "a" * 101,
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "key" in serializer.errors

    # ==================== Default Values Tests ====================

    def test_defaults_applied_correctly(self):
        """Test that default values are applied correctly."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "test_input",
            "display_name": "test_input",
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["data_schema"] == {}
        assert serializer.validated_data["required"] is True
        assert serializer.validated_data["default_value"] is None
        assert serializer.validated_data["metadata"] == {}

    def test_required_false_accepted(self):
        """Test that required=False is accepted."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "optional_input",
            "display_name": "optional_input",
            "direction": PortDirection.INPUT,
            "required": False,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["required"] is False

    # ==================== Edge Cases ====================

    def test_id_with_uuid_format(self):
        """Test id with UUID format."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "test_input",
            "display_name": "test_input",
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_key_with_underscores_and_numbers(self):
        """Test key with underscores and numbers."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "input_value_123",
            "display_name": "input_value_123",
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_data_schema_empty_object(self):
        """Test empty object as data_schema."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "test_input",
            "display_name": "test_input",
            "direction": PortDirection.INPUT,
            "data_schema": {},
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_metadata_with_nested_objects(self):
        """Test metadata with deeply nested objects."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "test_input",
            "display_name": "test_input",
            "direction": PortDirection.INPUT,
            "metadata": {
                "level1": {
                    "level2": {
                        "level3": {"value": "deep"},
                    },
                },
                "array": [1, 2, {"nested": True}],
            },
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_default_value_various_types(self):
        """Test default_value with various JSON types."""
        test_cases = [
            {"default_value": "string"},
            {"default_value": 123},
            {"default_value": 123.45},
            {"default_value": True},
            {"default_value": False},
            {"default_value": []},
            {"default_value": [1, 2, 3]},
            {"default_value": {}},
            {"default_value": {"nested": {"value": 1}}},
        ]

        for case in test_cases:
            data = {
                "id": str(uuid.uuid4()),
                "key": "test_input",
                "display_name": "test_input",
                "direction": PortDirection.INPUT,
                **case,
            }
            serializer = PortWriteSerializer(data=data)
            assert serializer.is_valid(), f"Failed for {case}: {serializer.errors}"


class TestPortReadSerializerRefPort:
    """Tests for PortReadSerializer ref_port_id field."""

    def test_serializes_ref_port_id_null(self, input_port):
        """ref_port_id is None when ref_port is not set."""
        serializer = PortReadSerializer(input_port)
        assert serializer.data["ref_port_id"] is None

    def test_serializes_ref_port_id_set(
        self, db, subgraph_node, active_referenced_graph_version, node_template
    ):
        """ref_port_id is serialized when ref_port is set."""
        child_node = Node.no_workspace_objects.create(
            graph_version=active_referenced_graph_version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="Child Node",
            config={},
        )
        child_port = Port.no_workspace_objects.create(
            node=child_node,
            key="input1",
            display_name="input1",
            direction=PortDirection.INPUT,
        )
        subgraph_port = Port(
            node=subgraph_node,
            key="custom",
            display_name="My Input",
            direction=PortDirection.INPUT,
            ref_port=child_port,
        )
        subgraph_port.save()

        serializer = PortReadSerializer(subgraph_port)
        assert serializer.data["ref_port_id"] == str(child_port.id)

    def test_ref_port_id_in_fields(self):
        """ref_port_id is listed in serializer fields."""
        serializer = PortReadSerializer()
        assert "ref_port_id" in serializer.fields


class TestPortWriteSerializerRefPort:
    """Tests for PortWriteSerializer ref_port_id field."""

    def test_ref_port_id_optional(self):
        """ref_port_id is optional and defaults to None."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "test_input",
            "display_name": "test_input",
            "direction": PortDirection.INPUT,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["ref_port_id"] is None

    def test_ref_port_id_valid_uuid(self):
        """ref_port_id accepts a valid UUID."""
        ref_id = str(uuid.uuid4())
        data = {
            "id": str(uuid.uuid4()),
            "key": "custom",
            "display_name": "My Input",
            "direction": PortDirection.INPUT,
            "ref_port_id": ref_id,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert str(serializer.validated_data["ref_port_id"]) == ref_id

    def test_ref_port_id_null_accepted(self):
        """ref_port_id accepts null."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "custom",
            "display_name": "My Input",
            "direction": PortDirection.INPUT,
            "ref_port_id": None,
        }
        serializer = PortWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["ref_port_id"] is None

    def test_ref_port_id_invalid_uuid_fails(self):
        """ref_port_id rejects invalid UUID."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "custom",
            "display_name": "My Input",
            "direction": PortDirection.INPUT,
            "ref_port_id": "not-a-uuid",
        }
        serializer = PortWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "ref_port_id" in serializer.errors


@pytest.mark.unit
class TestPortCreateSerializer:
    """Tests for PortCreateSerializer validation."""

    def test_valid(self):
        data = {
            "id": str(uuid.uuid4()),
            "key": "custom",
            "display_name": "input_text",
            "direction": "input",
        }
        s = PortCreateSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_id_required(self):
        data = {"key": "custom", "display_name": "x", "direction": "input"}
        s = PortCreateSerializer(data=data)
        assert not s.is_valid()
        assert "id" in s.errors

    def test_direction_choices(self):
        base = {"id": str(uuid.uuid4()), "key": "k", "display_name": "d"}
        for d in ("input", "output"):
            s = PortCreateSerializer(data={**base, "direction": d})
            assert s.is_valid(), s.errors

        s = PortCreateSerializer(data={**base, "direction": "bidirectional"})
        assert not s.is_valid()
        assert "direction" in s.errors


@pytest.mark.unit
class TestUpdatePortSerializer:
    """Tests for UpdatePortSerializer validation."""

    def test_valid(self):
        s = UpdatePortSerializer(data={"display_name": "new_name"})
        assert s.is_valid(), s.errors

    def test_display_name_required(self):
        s = UpdatePortSerializer(data={})
        assert not s.is_valid()
        assert "display_name" in s.errors


@pytest.mark.unit
class TestPortDisplayNameReservedCharValidation:
    """Tests for reserved character validation in output port display_name."""

    @pytest.mark.parametrize("char", [".", "[", "]", "{", "}"])
    def test_write_serializer_rejects_reserved_chars_on_output(self, char):
        data = {
            "id": str(uuid.uuid4()),
            "key": "custom",
            "display_name": f"bad{char}name",
            "direction": PortDirection.OUTPUT,
        }
        s = PortWriteSerializer(data=data)
        assert not s.is_valid()
        assert "display_name" in s.errors

    @pytest.mark.parametrize("char", [".", "[", "]", "{", "}"])
    def test_create_serializer_rejects_reserved_chars_on_output(self, char):
        data = {
            "id": str(uuid.uuid4()),
            "key": "custom",
            "display_name": f"bad{char}name",
            "direction": PortDirection.OUTPUT,
        }
        s = PortCreateSerializer(data=data)
        assert not s.is_valid()
        assert "display_name" in s.errors

    def test_write_serializer_allows_reserved_chars_on_input(self):
        """Input ports are allowed to have dot-notation display_names."""
        data = {
            "id": str(uuid.uuid4()),
            "key": "custom",
            "display_name": "Node1.response.data",
            "direction": PortDirection.INPUT,
        }
        s = PortWriteSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_create_serializer_allows_reserved_chars_on_input(self):
        data = {
            "id": str(uuid.uuid4()),
            "key": "custom",
            "display_name": "Node1.response[0]",
            "direction": PortDirection.INPUT,
        }
        s = PortCreateSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_write_serializer_allows_clean_output_name(self):
        data = {
            "id": str(uuid.uuid4()),
            "key": "custom",
            "display_name": "good_name",
            "direction": PortDirection.OUTPUT,
        }
        s = PortWriteSerializer(data=data)
        assert s.is_valid(), s.errors
