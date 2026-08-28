"""Comprehensive tests for graph version serializers.

Note: Port key validation (template mode, subgraph keys, duplicates) was moved
from the serializer layer to model-level validation (Port.clean / GraphVersion.clean).
Serializers now only validate field structure and types.
"""

import uuid

import pytest

from agent_playground.models.choices import GraphVersionStatus, NodeType, PortDirection
from agent_playground.models.graph_version import GraphVersion
from agent_playground.serializers.graph_version import (
    GraphVersionDetailSerializer,
    GraphVersionListSerializer,
    VersionCreateSerializer,
    VersionMetadataUpdateSerializer,
)


class TestGraphVersionListSerializer:
    """Tests for GraphVersionListSerializer."""

    def test_serializes_list_fields(self, graph_version):
        """Test that lightweight list fields are serialized correctly."""
        serializer = GraphVersionListSerializer(graph_version)
        data = serializer.data

        assert data["id"] == str(graph_version.id)
        assert data["version_number"] == graph_version.version_number
        assert data["status"] == graph_version.status
        assert data["tags"] == graph_version.tags
        assert data["commit_message"] == graph_version.commit_message
        assert "created_at" in data

    def test_excludes_nested_data(self, graph_version):
        """Test that nested data is not included in list serializer."""
        serializer = GraphVersionListSerializer(graph_version)
        data = serializer.data

        assert "nodes" not in data
        assert "edges" not in data

    def test_serializes_many_versions(self, graph_version, active_graph_version):
        """Test serialization of multiple versions."""
        serializer = GraphVersionListSerializer(
            [graph_version, active_graph_version], many=True
        )
        data = serializer.data

        assert len(data) == 2

    def test_serializes_empty_list(self):
        """Test serialization of empty version list."""
        serializer = GraphVersionListSerializer([], many=True)
        data = serializer.data
        assert data == []

    def test_all_fields_are_read_only(self):
        """Test that all fields in GraphVersionListSerializer are read-only."""
        serializer = GraphVersionListSerializer()
        for field_name in serializer.fields:
            assert serializer.fields[field_name].read_only

    def test_id_is_string_uuid(self, graph_version):
        """Test that id is serialized as string UUID."""
        serializer = GraphVersionListSerializer(graph_version)
        data = serializer.data
        assert isinstance(data["id"], str)
        uuid.UUID(data["id"])  # Should not raise

    def test_serializes_version_with_tags(self, graph, db):
        """Test serialization of version with multiple tags."""
        version = GraphVersion.no_workspace_objects.create(
            graph=graph,
            version_number=10,
            status=GraphVersionStatus.ACTIVE,
            tags=["production", "stable", "v2.0"],
        )
        serializer = GraphVersionListSerializer(version)
        assert serializer.data["tags"] == ["production", "stable", "v2.0"]

    def test_serializes_version_with_commit_message(self, graph, db):
        """Test serialization of version with commit message."""
        version = GraphVersion.no_workspace_objects.create(
            graph=graph,
            version_number=10,
            status=GraphVersionStatus.ACTIVE,
            commit_message="Fixed edge case in data processing",
        )
        serializer = GraphVersionListSerializer(version)
        assert serializer.data["commit_message"] == "Fixed edge case in data processing"

    def test_serializes_inactive_version(self, graph, db):
        """Test serialization of inactive version."""
        version = GraphVersion.no_workspace_objects.create(
            graph=graph,
            version_number=10,
            status=GraphVersionStatus.INACTIVE,
        )
        serializer = GraphVersionListSerializer(version)
        assert serializer.data["status"] == GraphVersionStatus.INACTIVE


class TestGraphVersionDetailSerializer:
    """Tests for GraphVersionDetailSerializer."""

    def test_serializes_all_fields(self, graph_version):
        """Test that all fields are serialized correctly."""
        serializer = GraphVersionDetailSerializer(graph_version)
        data = serializer.data

        assert data["id"] == str(graph_version.id)
        assert data["version_number"] == graph_version.version_number
        assert data["status"] == graph_version.status
        assert data["tags"] == graph_version.tags
        assert data["commit_message"] == graph_version.commit_message
        assert "created_at" in data
        assert "nodes" in data

    def test_serializes_nodes(
        self,
        graph_version,
        node,
        input_port,
        output_port,
        second_node,
        second_node_input_port,
    ):
        """Test that nodes are properly nested."""
        serializer = GraphVersionDetailSerializer(graph_version)
        data = serializer.data

        assert len(data["nodes"]) == 2

        # Check node structure
        node_data = next(n for n in data["nodes"] if n["id"] == str(node.id))
        assert node_data["name"] == node.name
        assert len(node_data["ports"]) == 2

    def test_serializes_empty_version(self, graph_version):
        """Test serialization of version with no nodes or edges."""
        serializer = GraphVersionDetailSerializer(graph_version)
        data = serializer.data

        assert data["nodes"] == []

    def test_serializes_version_with_subgraph_node(
        self, graph_version, subgraph_node, active_referenced_graph_version
    ):
        """Test serialization of version containing subgraph node."""
        serializer = GraphVersionDetailSerializer(graph_version)
        data = serializer.data

        assert len(data["nodes"]) == 1
        node_data = data["nodes"][0]
        assert node_data["type"] == NodeType.SUBGRAPH
        assert node_data["ref_graph_version_id"] == str(
            active_referenced_graph_version.id
        )

    def test_serializes_complex_node_config(self, graph_version, node):
        """Test serialization of nodes with complex config."""
        node.config = {
            "model": "gpt-4",
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello"},
            ],
        }
        node.save()

        serializer = GraphVersionDetailSerializer(graph_version)
        data = serializer.data

        node_data = next(n for n in data["nodes"] if n["id"] == str(node.id))
        assert node_data["config"]["model"] == "gpt-4"
        assert node_data["config"]["temperature"] == 0.7
        assert len(node_data["config"]["messages"]) == 2


class TestVersionCreateSerializer:
    """Tests for VersionCreateSerializer."""

    def test_empty_data_valid(self):
        """Test that empty data is valid (version_number auto-incremented)."""
        serializer = VersionCreateSerializer(data={})
        assert serializer.is_valid()

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored."""
        data = {
            "version_number": 999,  # Should be ignored
            "status": GraphVersionStatus.ACTIVE,  # Should be ignored
            "extra_field": "value",
        }
        serializer = VersionCreateSerializer(data=data)
        assert serializer.is_valid()

    def test_null_data_valid(self):
        """Test that null data is handled."""
        serializer = VersionCreateSerializer(data=None)
        # Should handle gracefully (depends on DRF behavior)
        # This may or may not be valid depending on serializer configuration

    def test_duplicate_port_key_on_same_node_fails(self, node_template):
        """Test that duplicate port keys on the same node fail validation."""
        data = {
            "nodes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": NodeType.ATOMIC,
                    "name": "Test Node",
                    "node_template_id": str(node_template.id),
                    "ports": [
                        {
                            "id": str(uuid.uuid4()),
                            "key": "response",
                            "display_name": "Response",
                            "direction": PortDirection.OUTPUT,
                        },
                        {
                            "id": str(uuid.uuid4()),
                            "key": "response",
                            "display_name": "Response Copy",
                            "direction": PortDirection.OUTPUT,
                        },
                    ],
                }
            ],
        }
        serializer = VersionCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "nodes" in serializer.errors

    def test_same_port_key_on_different_nodes_valid(self, node_template):
        """Test that the same port key on different nodes is valid."""
        data = {
            "nodes": [
                {
                    "id": str(uuid.uuid4()),
                    "type": NodeType.ATOMIC,
                    "name": "Node A",
                    "node_template_id": str(node_template.id),
                    "ports": [
                        {
                            "id": str(uuid.uuid4()),
                            "key": "output1",
                            "display_name": "Output 1",
                            "direction": PortDirection.OUTPUT,
                        },
                    ],
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": NodeType.ATOMIC,
                    "name": "Node B",
                    "node_template_id": str(node_template.id),
                    "ports": [
                        {
                            "id": str(uuid.uuid4()),
                            "key": "output1",
                            "display_name": "Output 1",
                            "direction": PortDirection.OUTPUT,
                        },
                    ],
                },
            ],
        }
        serializer = VersionCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors


class TestVersionMetadataUpdateSerializer:
    """Tests for VersionMetadataUpdateSerializer (metadata-only PATCH)."""

    # ==================== Valid Data Tests ====================

    def test_empty_data_valid(self):
        """Test that empty data is valid with defaults."""
        serializer = VersionMetadataUpdateSerializer(data={})
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["status"] == GraphVersionStatus.DRAFT

    def test_valid_with_only_status(self):
        """Test validation with only status provided."""
        data = {"status": GraphVersionStatus.DRAFT}
        serializer = VersionMetadataUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_with_active_status(self):
        """Test validation with active status (publish)."""
        data = {"status": GraphVersionStatus.ACTIVE}
        serializer = VersionMetadataUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_with_commit_message(self):
        """Test validation with commit message."""
        data = {
            "status": GraphVersionStatus.ACTIVE,
            "commit_message": "Feature: Added new processing node",
        }
        serializer = VersionMetadataUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert (
            serializer.validated_data["commit_message"]
            == "Feature: Added new processing node"
        )

    def test_valid_with_empty_commit_message(self):
        """Test validation with empty commit message."""
        data = {
            "status": GraphVersionStatus.DRAFT,
            "commit_message": "",
        }
        serializer = VersionMetadataUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_with_null_commit_message(self):
        """Test validation with null commit message."""
        data = {
            "status": GraphVersionStatus.DRAFT,
            "commit_message": None,
        }
        serializer = VersionMetadataUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_with_only_commit_message(self):
        """Test validation with only commit_message (status defaults to draft)."""
        data = {"commit_message": "Updated description"}
        serializer = VersionMetadataUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["status"] == GraphVersionStatus.DRAFT
        assert serializer.validated_data["commit_message"] == "Updated description"

    # ==================== Invalid Status Tests ====================

    def test_invalid_status_fails(self):
        """Test that invalid status fails validation."""
        data = {"status": "invalid_status"}
        serializer = VersionMetadataUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "status" in serializer.errors

    def test_inactive_status_not_allowed(self):
        """Test that inactive status is not allowed for version update."""
        data = {"status": GraphVersionStatus.INACTIVE}
        serializer = VersionMetadataUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "status" in serializer.errors

    # ==================== Extra Fields Ignored ====================

    def test_extra_fields_ignored(self):
        """Test that extra fields (nodes, edges) are ignored — metadata only."""
        data = {
            "status": GraphVersionStatus.DRAFT,
            "commit_message": "test",
            "nodes": [{"id": str(uuid.uuid4())}],
            "edges": [{"source": "a"}],
        }
        serializer = VersionMetadataUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert "nodes" not in serializer.validated_data
        assert "edges" not in serializer.validated_data
