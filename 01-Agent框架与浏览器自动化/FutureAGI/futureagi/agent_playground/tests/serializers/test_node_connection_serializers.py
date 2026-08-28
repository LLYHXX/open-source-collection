"""Tests for node connection serializers."""

import uuid

import pytest

from agent_playground.serializers.node_connection import CreateNodeConnectionSerializer


@pytest.mark.unit
class TestCreateNodeConnectionSerializer:
    """Tests for CreateNodeConnectionSerializer validation."""

    def test_valid(self):
        data = {
            "id": str(uuid.uuid4()),
            "source_node_id": str(uuid.uuid4()),
            "target_node_id": str(uuid.uuid4()),
        }
        s = CreateNodeConnectionSerializer(data=data)
        assert s.is_valid(), s.errors

    def test_missing_source_node_id(self):
        data = {
            "id": str(uuid.uuid4()),
            "target_node_id": str(uuid.uuid4()),
        }
        s = CreateNodeConnectionSerializer(data=data)
        assert not s.is_valid()
        assert "source_node_id" in s.errors

    def test_missing_target_node_id(self):
        data = {
            "id": str(uuid.uuid4()),
            "source_node_id": str(uuid.uuid4()),
        }
        s = CreateNodeConnectionSerializer(data=data)
        assert not s.is_valid()
        assert "target_node_id" in s.errors
