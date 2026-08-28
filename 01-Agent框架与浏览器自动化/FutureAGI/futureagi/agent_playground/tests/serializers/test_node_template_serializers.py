"""Comprehensive tests for node template serializers."""

import pytest

from agent_playground.models.choices import PortMode
from agent_playground.models.node_template import NodeTemplate
from agent_playground.serializers.node_template import (
    NodeTemplateDetailSerializer,
    NodeTemplateListSerializer,
)


class TestNodeTemplateListSerializer:
    """Tests for NodeTemplateListSerializer."""

    def test_serializes_list_fields(self, node_template):
        """Test that lightweight list fields are serialized correctly."""
        serializer = NodeTemplateListSerializer(node_template)
        data = serializer.data

        assert data["id"] == str(node_template.id)
        assert data["name"] == node_template.name
        assert data["display_name"] == node_template.display_name
        assert data["description"] == node_template.description
        assert data["icon"] == node_template.icon
        assert data["categories"] == node_template.categories

    def test_excludes_detail_fields(self, node_template):
        """Test that detail fields are not included in list serializer."""
        serializer = NodeTemplateListSerializer(node_template)
        data = serializer.data

        assert "input_definition" not in data
        assert "output_definition" not in data
        assert "input_mode" not in data
        assert "output_mode" not in data
        assert "config_schema" not in data

    def test_serializes_many_templates(self, node_template, dynamic_node_template):
        """Test serialization of multiple templates."""
        serializer = NodeTemplateListSerializer(
            [node_template, dynamic_node_template], many=True
        )
        data = serializer.data

        assert len(data) == 2

    def test_serializes_empty_list(self):
        """Test serialization of empty template list."""
        serializer = NodeTemplateListSerializer([], many=True)
        data = serializer.data
        assert data == []

    def test_id_is_string_uuid(self, node_template):
        """Test that id is serialized as string UUID."""
        serializer = NodeTemplateListSerializer(node_template)
        data = serializer.data

        assert isinstance(data["id"], str)
        import uuid

        uuid.UUID(data["id"])  # Should not raise

    def test_all_fields_are_read_only(self):
        """Test that all fields in NodeTemplateListSerializer are read-only."""
        serializer = NodeTemplateListSerializer()
        for field_name in serializer.fields:
            assert serializer.fields[field_name].read_only

    def test_serializes_template_with_icon(self, db):
        """Test serialization of template with icon URL."""
        template = NodeTemplate.no_workspace_objects.create(
            name="with_icon",
            display_name="With Icon",
            icon="https://example.com/icon.png",
            categories=["test"],
        )
        serializer = NodeTemplateListSerializer(template)
        assert serializer.data["icon"] == "https://example.com/icon.png"

    def test_serializes_template_with_null_icon(self, db):
        """Test serialization of template with null icon."""
        template = NodeTemplate.no_workspace_objects.create(
            name="no_icon",
            display_name="No Icon",
            icon=None,
            categories=["test"],
        )
        serializer = NodeTemplateListSerializer(template)
        assert serializer.data["icon"] is None

    def test_serializes_template_with_empty_categories(self, db):
        """Test serialization of template with empty categories."""
        template = NodeTemplate.no_workspace_objects.create(
            name="no_categories",
            display_name="No Categories",
            categories=[],
        )
        serializer = NodeTemplateListSerializer(template)
        assert serializer.data["categories"] == []

    def test_serializes_template_with_multiple_categories(self, db):
        """Test serialization of template with multiple categories."""
        template = NodeTemplate.no_workspace_objects.create(
            name="multi_category",
            display_name="Multi Category",
            categories=["AI", "LLM", "Text Processing", "Utility"],
        )
        serializer = NodeTemplateListSerializer(template)
        assert len(serializer.data["categories"]) == 4
        assert "AI" in serializer.data["categories"]
        assert "Utility" in serializer.data["categories"]

    def test_serializes_template_with_empty_description(self, db):
        """Test serialization of template with empty description."""
        template = NodeTemplate.no_workspace_objects.create(
            name="no_description",
            display_name="No Description",
            description="",
            categories=["test"],
        )
        serializer = NodeTemplateListSerializer(template)
        assert serializer.data["description"] == ""


class TestNodeTemplateDetailSerializer:
    """Tests for NodeTemplateDetailSerializer."""

    def test_serializes_all_fields(self, node_template):
        """Test that all fields are serialized correctly."""
        serializer = NodeTemplateDetailSerializer(node_template)
        data = serializer.data

        assert data["id"] == str(node_template.id)
        assert data["name"] == node_template.name
        assert data["display_name"] == node_template.display_name
        assert data["description"] == node_template.description
        assert data["icon"] == node_template.icon
        assert data["categories"] == node_template.categories
        assert data["input_definition"] == node_template.input_definition
        assert data["output_definition"] == node_template.output_definition
        assert data["input_mode"] == node_template.input_mode
        assert data["output_mode"] == node_template.output_mode
        assert data["config_schema"] == node_template.config_schema

    def test_serializes_dynamic_template(self, dynamic_node_template):
        """Test serialization of dynamic port mode template."""
        serializer = NodeTemplateDetailSerializer(dynamic_node_template)
        data = serializer.data

        assert data["input_mode"] == PortMode.DYNAMIC
        assert data["output_mode"] == PortMode.DYNAMIC
        assert data["input_definition"] == []
        assert data["output_definition"] == []

    def test_serializes_extensible_template(self, extensible_node_template):
        """Test serialization of extensible port mode template."""
        serializer = NodeTemplateDetailSerializer(extensible_node_template)
        data = serializer.data

        assert data["input_mode"] == PortMode.EXTENSIBLE
        assert data["output_mode"] == PortMode.EXTENSIBLE
        assert len(data["input_definition"]) == 1
        assert len(data["output_definition"]) == 1

    def test_all_fields_are_read_only(self):
        """Test that all fields in NodeTemplateDetailSerializer are read-only."""
        serializer = NodeTemplateDetailSerializer()
        for field_name in serializer.fields:
            assert serializer.fields[field_name].read_only

    def test_serializes_complex_config_schema(self, db):
        """Test serialization of template with complex config schema."""
        complex_schema = {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "enum": ["gpt-4", "gpt-3.5-turbo", "claude-3"],
                },
                "temperature": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 2,
                    "default": 0.7,
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 128000,
                },
                "system_prompt": {
                    "type": "string",
                    "maxLength": 10000,
                },
                "stop_sequences": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 4,
                },
            },
            "required": ["model"],
            "additionalProperties": False,
        }
        template = NodeTemplate.no_workspace_objects.create(
            name="complex_config",
            display_name="Complex Config",
            categories=["LLM"],
            config_schema=complex_schema,
        )
        serializer = NodeTemplateDetailSerializer(template)
        assert serializer.data["config_schema"] == complex_schema

    def test_serializes_complex_input_definition(self, db):
        """Test serialization of template with complex input definition."""
        input_def = [
            {
                "key": "messages",
                "data_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {
                                "type": "string",
                                "enum": ["user", "assistant", "system"],
                            },
                            "content": {"type": "string"},
                        },
                        "required": ["role", "content"],
                    },
                },
                "required": True,
            },
            {
                "key": "context",
                "data_schema": {"type": "object"},
                "required": False,
                "default_value": {},
            },
        ]
        template = NodeTemplate.no_workspace_objects.create(
            name="complex_input",
            display_name="Complex Input",
            categories=["LLM"],
            input_definition=input_def,
        )
        serializer = NodeTemplateDetailSerializer(template)
        assert serializer.data["input_definition"] == input_def

    def test_serializes_complex_output_definition(self, db):
        """Test serialization of template with complex output definition."""
        output_def = [
            {
                "key": "response",
                "data_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "finish_reason": {"type": "string"},
                        "usage": {
                            "type": "object",
                            "properties": {
                                "prompt_tokens": {"type": "integer"},
                                "completion_tokens": {"type": "integer"},
                                "total_tokens": {"type": "integer"},
                            },
                        },
                    },
                },
            },
            {"key": "error", "data_schema": {"type": "string"}},
        ]
        template = NodeTemplate.no_workspace_objects.create(
            name="complex_output",
            display_name="Complex Output",
            categories=["LLM"],
            output_definition=output_def,
        )
        serializer = NodeTemplateDetailSerializer(template)
        assert serializer.data["output_definition"] == output_def

    def test_serializes_mixed_port_modes(self, db):
        """Test serialization of template with mixed input/output modes."""
        template = NodeTemplate.no_workspace_objects.create(
            name="mixed_modes",
            display_name="Mixed Modes",
            categories=["hybrid"],
            input_mode=PortMode.STRICT,
            output_mode=PortMode.DYNAMIC,
            input_definition=[{"key": "input1", "data_schema": {"type": "string"}}],
            output_definition=[],
        )
        serializer = NodeTemplateDetailSerializer(template)
        assert serializer.data["input_mode"] == PortMode.STRICT
        assert serializer.data["output_mode"] == PortMode.DYNAMIC

    def test_serializes_empty_config_schema(self, db):
        """Test serialization of template with empty config schema."""
        template = NodeTemplate.no_workspace_objects.create(
            name="no_config",
            display_name="No Config",
            categories=["simple"],
            config_schema={},
        )
        serializer = NodeTemplateDetailSerializer(template)
        assert serializer.data["config_schema"] == {}

    def test_serializes_many_templates(
        self, node_template, dynamic_node_template, extensible_node_template
    ):
        """Test serialization of multiple templates with full details."""
        serializer = NodeTemplateDetailSerializer(
            [node_template, dynamic_node_template, extensible_node_template], many=True
        )
        data = serializer.data

        assert len(data) == 3
        # All should have detail fields
        for template_data in data:
            assert "input_definition" in template_data
            assert "output_definition" in template_data
            assert "input_mode" in template_data
            assert "output_mode" in template_data
            assert "config_schema" in template_data

    def test_detail_includes_all_list_fields(self, node_template):
        """Test that detail serializer includes all fields from list serializer."""
        list_serializer = NodeTemplateListSerializer(node_template)
        detail_serializer = NodeTemplateDetailSerializer(node_template)

        list_data = list_serializer.data
        detail_data = detail_serializer.data

        # All list fields should be in detail
        for field in list_data:
            assert field in detail_data
            assert list_data[field] == detail_data[field]
