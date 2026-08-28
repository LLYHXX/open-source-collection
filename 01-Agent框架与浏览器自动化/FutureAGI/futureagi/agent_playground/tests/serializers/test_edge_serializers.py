"""Comprehensive tests for edge serializers."""

import pytest

from agent_playground.models.edge import Edge
from agent_playground.models.node_connection import NodeConnection
from agent_playground.serializers.edge import EdgeReadSerializer, EdgeWriteSerializer


class TestEdgeReadSerializer:
    """Tests for EdgeReadSerializer."""

    def test_serializes_edge_fields(self, edge):
        """Test that all edge fields are serialized correctly."""
        serializer = EdgeReadSerializer(edge)
        data = serializer.data

        assert data["id"] == str(edge.id)
        assert data["source_port_id"] == str(edge.source_port.id)
        assert data["target_port_id"] == str(edge.target_port.id)

    def test_serializes_many_edges(
        self,
        edge,
        graph_version,
        second_node,
        third_node,
        second_node_output_port,
        third_node_input_port,
    ):
        """Test serialization of multiple edges."""
        # Create a second edge
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=second_node, target_node=third_node
        )
        edge2 = Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=second_node_output_port,
            target_port=third_node_input_port,
        )

        serializer = EdgeReadSerializer([edge, edge2], many=True)
        data = serializer.data

        assert len(data) == 2
        edge_ids = {e["id"] for e in data}
        assert str(edge.id) in edge_ids
        assert str(edge2.id) in edge_ids

    def test_serializes_empty_list(self):
        """Test serialization of empty edge list."""
        serializer = EdgeReadSerializer([], many=True)
        data = serializer.data
        assert data == []

    def test_all_fields_are_read_only(self):
        """Test that all fields in EdgeReadSerializer are read-only."""
        serializer = EdgeReadSerializer()
        for field_name in serializer.fields:
            assert serializer.fields[field_name].read_only

    def test_edge_with_different_ports(
        self, graph_version, node, second_node, input_port, second_node_output_port
    ):
        """Test edge between different node port combinations."""
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=second_node, target_node=node
        )
        edge = Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=second_node_output_port,
            target_port=input_port,
        )
        serializer = EdgeReadSerializer(edge)
        data = serializer.data

        assert data["source_port_id"] == str(second_node_output_port.id)
        assert data["target_port_id"] == str(input_port.id)

    def test_id_is_string_uuid(self, edge):
        """Test that id is serialized as string UUID."""
        serializer = EdgeReadSerializer(edge)
        data = serializer.data

        # Should be a string
        assert isinstance(data["id"], str)
        # Should be a valid UUID format
        import uuid

        uuid.UUID(data["id"])  # Should not raise


class TestEdgeWriteSerializer:
    """Tests for EdgeWriteSerializer."""

    # ==================== Valid Data Tests ====================

    def test_valid_edge_data(self):
        """Test validation of valid edge data."""
        data = {
            "source_port_temp_id": "port-1",
            "target_port_temp_id": "port-2",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["source_port_temp_id"] == "port-1"
        assert serializer.validated_data["target_port_temp_id"] == "port-2"

    def test_valid_edge_with_uuid_temp_ids(self):
        """Test validation with UUID-formatted temp_ids."""
        import uuid

        data = {
            "source_port_temp_id": str(uuid.uuid4()),
            "target_port_temp_id": str(uuid.uuid4()),
        }
        serializer = EdgeWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_edge_with_descriptive_temp_ids(self):
        """Test validation with descriptive temp_ids."""
        data = {
            "source_port_temp_id": "node-llm-output-response",
            "target_port_temp_id": "node-summarizer-input-text",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_edge_with_special_characters(self):
        """Test validation with special characters in temp_ids."""
        data = {
            "source_port_temp_id": "port:1.output_main",
            "target_port_temp_id": "port:2.input_data",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_edge_with_numeric_temp_ids(self):
        """Test validation with numeric temp_ids."""
        data = {
            "source_port_temp_id": "12345",
            "target_port_temp_id": "67890",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    # ==================== Required Field Validation Tests ====================

    def test_missing_source_port_temp_id_fails(self):
        """Test that missing source_port_temp_id fails validation."""
        data = {
            "target_port_temp_id": "port-2",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "source_port_temp_id" in serializer.errors

    def test_missing_target_port_temp_id_fails(self):
        """Test that missing target_port_temp_id fails validation."""
        data = {
            "source_port_temp_id": "port-1",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "target_port_temp_id" in serializer.errors

    def test_empty_data_fails(self):
        """Test that empty data fails validation."""
        serializer = EdgeWriteSerializer(data={})
        assert not serializer.is_valid()
        assert "source_port_temp_id" in serializer.errors
        assert "target_port_temp_id" in serializer.errors

    # ==================== Invalid Value Tests ====================

    def test_empty_source_port_temp_id_fails(self):
        """Test that empty source_port_temp_id fails validation."""
        data = {
            "source_port_temp_id": "",
            "target_port_temp_id": "port-2",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "source_port_temp_id" in serializer.errors

    def test_empty_target_port_temp_id_fails(self):
        """Test that empty target_port_temp_id fails validation."""
        data = {
            "source_port_temp_id": "port-1",
            "target_port_temp_id": "",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "target_port_temp_id" in serializer.errors

    def test_null_source_port_temp_id_fails(self):
        """Test that null source_port_temp_id fails validation."""
        data = {
            "source_port_temp_id": None,
            "target_port_temp_id": "port-2",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "source_port_temp_id" in serializer.errors

    def test_null_target_port_temp_id_fails(self):
        """Test that null target_port_temp_id fails validation."""
        data = {
            "source_port_temp_id": "port-1",
            "target_port_temp_id": None,
        }
        serializer = EdgeWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "target_port_temp_id" in serializer.errors

    # ==================== Edge Cases ====================

    def test_same_source_and_target_temp_id_allowed(self):
        """Test that same source and target temp_id passes serializer validation.

        Note: Business logic validation (self-loops) is handled at the view level.
        """
        data = {
            "source_port_temp_id": "port-1",
            "target_port_temp_id": "port-1",
        }
        serializer = EdgeWriteSerializer(data=data)
        # Serializer should allow this - business logic validation happens elsewhere
        assert serializer.is_valid(), serializer.errors

    def test_whitespace_only_temp_id_fails(self):
        """Test that whitespace-only temp_ids fail validation."""
        data = {
            "source_port_temp_id": "   ",
            "target_port_temp_id": "port-2",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert not serializer.is_valid()
        assert "source_port_temp_id" in serializer.errors

    def test_very_long_temp_ids_accepted(self):
        """Test that long temp_ids are accepted."""
        data = {
            "source_port_temp_id": "a" * 255,
            "target_port_temp_id": "b" * 255,
        }
        serializer = EdgeWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_unicode_temp_ids_accepted(self):
        """Test that unicode characters in temp_ids are accepted."""
        data = {
            "source_port_temp_id": "port-源端口-1",
            "target_port_temp_id": "port-目标端口-2",
        }
        serializer = EdgeWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    # ==================== Many Serialization Tests ====================

    def test_many_edges_validation(self):
        """Test validation of multiple edges."""
        data = [
            {"source_port_temp_id": "port-1", "target_port_temp_id": "port-2"},
            {"source_port_temp_id": "port-2", "target_port_temp_id": "port-3"},
            {"source_port_temp_id": "port-3", "target_port_temp_id": "port-4"},
        ]
        serializer = EdgeWriteSerializer(data=data, many=True)
        assert serializer.is_valid(), serializer.errors
        assert len(serializer.validated_data) == 3

    def test_many_edges_with_one_invalid(self):
        """Test that one invalid edge in many fails entire validation."""
        data = [
            {"source_port_temp_id": "port-1", "target_port_temp_id": "port-2"},
            {"source_port_temp_id": "", "target_port_temp_id": "port-3"},  # Invalid
            {"source_port_temp_id": "port-3", "target_port_temp_id": "port-4"},
        ]
        serializer = EdgeWriteSerializer(data=data, many=True)
        assert not serializer.is_valid()
        # Error should be at index 1 (second item has the error)
        assert len(serializer.errors) == 3
        assert serializer.errors[1]  # Second item has error (non-empty dict)
        assert "source_port_temp_id" in serializer.errors[1]

    def test_empty_many_edges_valid(self):
        """Test that empty list of edges is valid."""
        serializer = EdgeWriteSerializer(data=[], many=True)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == []

    # ==================== Extra Fields Tests ====================

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored."""
        data = {
            "source_port_temp_id": "port-1",
            "target_port_temp_id": "port-2",
            "extra_field": "should be ignored",
            "another_extra": 123,
        }
        serializer = EdgeWriteSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert "extra_field" not in serializer.validated_data
        assert "another_extra" not in serializer.validated_data
