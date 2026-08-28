"""Tests for agent_playground.utils.graph — get_exposed_ports_for_versions."""

import pytest

from agent_playground.models.choices import (
    GraphVersionStatus,
    NodeType,
    PortDirection,
    PortMode,
)
from agent_playground.models.edge import Edge
from agent_playground.models.graph_version import GraphVersion
from agent_playground.models.node import Node
from agent_playground.models.node_connection import NodeConnection
from agent_playground.models.node_template import NodeTemplate
from agent_playground.models.port import Port
from agent_playground.utils.graph import get_exposed_ports_for_versions


@pytest.fixture
def dynamic_template(db):
    """Dynamic template for graph util tests needing arbitrary port keys."""
    return NodeTemplate.no_workspace_objects.create(
        name="graph_utils_test_template",
        display_name="Graph Utils Test Template",
        description="Template for graph utils tests",
        categories=["testing"],
        input_definition=[],
        output_definition=[],
        input_mode=PortMode.DYNAMIC,
        output_mode=PortMode.DYNAMIC,
        config_schema={},
    )


@pytest.mark.unit
class TestGetExposedPortsForVersions:
    """Tests for get_exposed_ports_for_versions utility."""

    def test_empty_version_ids(self):
        """Returns empty dict for empty input."""
        assert get_exposed_ports_for_versions([]) == {}

    def test_returns_unconnected_ports(self, db, graph, dynamic_template):
        """Returns unconnected input and output ports."""
        version = GraphVersion.no_workspace_objects.create(
            graph=graph, version_number=20, status=GraphVersionStatus.DRAFT
        )
        node = Node.no_workspace_objects.create(
            graph_version=version,
            node_template=dynamic_template,
            type=NodeType.ATOMIC,
            name="Solo Node",
            config={},
        )
        Port.no_workspace_objects.create(
            node=node,
            key="custom",
            display_name="Input 1",
            direction=PortDirection.INPUT,
        )
        Port.no_workspace_objects.create(
            node=node,
            key="custom",
            display_name="Output 1",
            direction=PortDirection.OUTPUT,
        )
        result = get_exposed_ports_for_versions([version.id])
        ports = result[version.id]
        assert len(ports) == 2
        names = {p["display_name"] for p in ports}
        assert names == {"Input 1", "Output 1"}

    def test_connected_ports_excluded(self, db, graph, dynamic_template):
        """Connected ports are not returned as exposed."""
        version = GraphVersion.no_workspace_objects.create(
            graph=graph, version_number=21, status=GraphVersionStatus.DRAFT
        )
        node_a = Node.no_workspace_objects.create(
            graph_version=version,
            node_template=dynamic_template,
            type=NodeType.ATOMIC,
            name="A",
            config={},
        )
        node_b = Node.no_workspace_objects.create(
            graph_version=version,
            node_template=dynamic_template,
            type=NodeType.ATOMIC,
            name="B",
            config={},
        )
        out_a = Port.no_workspace_objects.create(
            node=node_a,
            key="custom",
            display_name="Out A",
            direction=PortDirection.OUTPUT,
        )
        in_b = Port.no_workspace_objects.create(
            node=node_b,
            key="custom",
            display_name="In B",
            direction=PortDirection.INPUT,
        )
        # Unconnected ports that should appear
        Port.no_workspace_objects.create(
            node=node_a,
            key="custom",
            display_name="In A",
            direction=PortDirection.INPUT,
        )
        Port.no_workspace_objects.create(
            node=node_b,
            key="custom",
            display_name="Out B",
            direction=PortDirection.OUTPUT,
        )
        # Connect out_a -> in_b
        NodeConnection.no_workspace_objects.create(
            graph_version=version, source_node=node_a, target_node=node_b
        )
        Edge.no_workspace_objects.create(
            graph_version=version,
            source_port=out_a,
            target_port=in_b,
        )
        result = get_exposed_ports_for_versions([version.id])
        ports = result[version.id]
        names = {p["display_name"] for p in ports}
        # Only unconnected ports should appear
        assert "In A" in names
        assert "Out B" in names
        assert "Out A" not in names
        assert "In B" not in names

    def test_deduplicates_by_display_name(self, db, graph, dynamic_template):
        """Ports with the same display_name are deduplicated."""
        version = GraphVersion.no_workspace_objects.create(
            graph=graph, version_number=22, status=GraphVersionStatus.DRAFT
        )
        node_a = Node.no_workspace_objects.create(
            graph_version=version,
            node_template=dynamic_template,
            type=NodeType.ATOMIC,
            name="LLM 1",
            config={},
        )
        node_b = Node.no_workspace_objects.create(
            graph_version=version,
            node_template=dynamic_template,
            type=NodeType.ATOMIC,
            name="LLM 2",
            config={},
        )
        Port.no_workspace_objects.create(
            node=node_a,
            key="custom",
            display_name="response",
            direction=PortDirection.OUTPUT,
        )
        Port.no_workspace_objects.create(
            node=node_b,
            key="custom",
            display_name="response",  # Same display_name
            direction=PortDirection.OUTPUT,
        )
        result = get_exposed_ports_for_versions([version.id])
        ports = result[version.id]
        # Should be deduplicated to 1
        response_ports = [p for p in ports if p["display_name"] == "response"]
        assert len(response_ports) == 1

    def test_different_display_names_not_deduplicated(
        self, db, graph, dynamic_template
    ):
        """Ports with different display_names are not deduplicated."""
        version = GraphVersion.no_workspace_objects.create(
            graph=graph, version_number=23, status=GraphVersionStatus.DRAFT
        )
        node_a = Node.no_workspace_objects.create(
            graph_version=version,
            node_template=dynamic_template,
            type=NodeType.ATOMIC,
            name="LLM 1",
            config={},
        )
        node_b = Node.no_workspace_objects.create(
            graph_version=version,
            node_template=dynamic_template,
            type=NodeType.ATOMIC,
            name="LLM 2",
            config={},
        )
        Port.no_workspace_objects.create(
            node=node_a,
            key="custom",
            display_name="LLM 1 Response",
            direction=PortDirection.OUTPUT,
        )
        Port.no_workspace_objects.create(
            node=node_b,
            key="custom",
            display_name="LLM 2 Response",
            direction=PortDirection.OUTPUT,
        )
        result = get_exposed_ports_for_versions([version.id])
        ports = result[version.id]
        names = {p["display_name"] for p in ports}
        assert names == {"LLM 1 Response", "LLM 2 Response"}

    def test_display_name_included_in_output(self, db, graph, dynamic_template):
        """Each returned port dict includes both key and display_name."""
        version = GraphVersion.no_workspace_objects.create(
            graph=graph, version_number=24, status=GraphVersionStatus.DRAFT
        )
        node = Node.no_workspace_objects.create(
            graph_version=version,
            node_template=dynamic_template,
            type=NodeType.ATOMIC,
            name="Test",
            config={},
        )
        port = Port.no_workspace_objects.create(
            node=node,
            key="custom",
            display_name="My Custom Name",
            direction=PortDirection.OUTPUT,
        )
        result = get_exposed_ports_for_versions([version.id])
        port_dict = result[version.id][0]
        assert port_dict["display_name"] == "My Custom Name"
        assert "direction" in port_dict
        assert "data_schema" in port_dict

    def test_version_with_no_ports(self, db, graph, node_template):
        """Version with no ports returns empty list."""
        version = GraphVersion.no_workspace_objects.create(
            graph=graph, version_number=25, status=GraphVersionStatus.DRAFT
        )
        Node.no_workspace_objects.create(
            graph_version=version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="Empty",
            config={},
        )
        result = get_exposed_ports_for_versions([version.id])
        # Version may not be in result or may have empty list
        assert result.get(version.id, []) == []
