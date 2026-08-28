"""
Tests for the graph validation utility functions.
"""

import pytest

from agent_playground.models.choices import (
    GraphVersionStatus,
    NodeType,
    PortDirection,
)
from agent_playground.models.edge import Edge
from agent_playground.models.graph import Graph
from agent_playground.models.graph_version import GraphVersion
from agent_playground.models.node import Node
from agent_playground.models.node_connection import NodeConnection
from agent_playground.models.port import Port
from agent_playground.utils.graph_validation import (
    would_create_cycle,
    would_create_graph_reference_cycle,
)


@pytest.mark.unit
class TestWouldCreateCycle:
    """Tests for would_create_cycle utility function."""

    def test_self_loop_detected(self, db, graph_version, node):
        """Same source and target node returns True immediately."""
        assert would_create_cycle(node.id, node.id, graph_version.id) is True

    def test_two_node_cycle_detected(
        self,
        db,
        graph_version,
        node,
        output_port,
        second_node,
        second_node_input_port,
    ):
        """A→B exists, B→A would create cycle."""
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=node, target_node=second_node
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=output_port,
            target_port=second_node_input_port,
        )
        assert would_create_cycle(second_node.id, node.id, graph_version.id) is True

    def test_three_node_cycle_detected(
        self,
        db,
        graph_version,
        node,
        output_port,
        second_node,
        second_node_input_port,
        second_node_output_port,
        third_node,
        third_node_input_port,
    ):
        """A→B→C exists, C→A would create cycle."""
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=node, target_node=second_node
        )
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=second_node, target_node=third_node
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=output_port,
            target_port=second_node_input_port,
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=second_node_output_port,
            target_port=third_node_input_port,
        )
        assert would_create_cycle(third_node.id, node.id, graph_version.id) is True

    def test_valid_chain_no_cycle(
        self,
        db,
        graph_version,
        node,
        output_port,
        second_node,
        second_node_input_port,
        third_node,
    ):
        """A→B exists, B→C does not create a cycle."""
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=node, target_node=second_node
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=output_port,
            target_port=second_node_input_port,
        )
        assert (
            would_create_cycle(second_node.id, third_node.id, graph_version.id) is False
        )

    def test_fan_out_no_cycle(
        self,
        db,
        graph_version,
        node,
        output_port,
        second_node,
        second_node_input_port,
        third_node,
    ):
        """A→B exists, A→C does not create a cycle."""
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=node, target_node=second_node
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=output_port,
            target_port=second_node_input_port,
        )
        assert would_create_cycle(node.id, third_node.id, graph_version.id) is False

    def test_diamond_dag_no_cycle(
        self,
        db,
        graph_version,
        node,
        output_port,
        second_node,
        second_node_input_port,
        second_node_output_port,
        third_node,
        third_node_input_port,
        third_node_output_port,
        node_template,
    ):
        """Diamond A→B, A→C, B→D; C→D does not create a cycle."""
        fourth_node = Node.no_workspace_objects.create(
            graph_version=graph_version,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="Fourth Node",
            config={},
            position={"x": 700, "y": 100},
        )
        fourth_input_1 = Port.no_workspace_objects.create(
            node=fourth_node,
            key="input1",
            display_name="input1",
            direction=PortDirection.INPUT,
            data_schema={"type": "string"},
        )

        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=node, target_node=second_node
        )
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=node, target_node=third_node
        )
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version,
            source_node=second_node,
            target_node=fourth_node,
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=output_port,
            target_port=second_node_input_port,
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=output_port,
            target_port=third_node_input_port,
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=second_node_output_port,
            target_port=fourth_input_1,
        )
        assert (
            would_create_cycle(third_node.id, fourth_node.id, graph_version.id) is False
        )

    def test_soft_deleted_edge_ignored(
        self,
        db,
        graph_version,
        node,
        output_port,
        second_node,
        second_node_input_port,
    ):
        """Soft-deleted A→B should not cause B→A to be detected as cycle."""
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=node, target_node=second_node
        )
        edge_ab = Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=output_port,
            target_port=second_node_input_port,
        )
        edge_ab.delete()  # Soft delete

        assert would_create_cycle(second_node.id, node.id, graph_version.id) is False

    def test_other_graph_version_ignored(
        self,
        db,
        graph,
        graph_version,
        node,
        output_port,
        second_node,
        second_node_input_port,
        node_template,
    ):
        """Edges in a different graph version are not considered."""
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=node, target_node=second_node
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=output_port,
            target_port=second_node_input_port,
        )

        version2 = GraphVersion.no_workspace_objects.create(
            graph=graph,
            version_number=10,
            status=GraphVersionStatus.DRAFT,
        )
        node_b2 = Node.no_workspace_objects.create(
            graph_version=version2,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="Node B v2",
            config={},
        )
        node_a2 = Node.no_workspace_objects.create(
            graph_version=version2,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="Node A v2",
            config={},
        )
        # B→A in version 2 should not detect cycle from version 1
        assert would_create_cycle(node_b2.id, node_a2.id, version2.id) is False

    def test_exclude_edge_id(
        self,
        db,
        graph_version,
        node,
        output_port,
        second_node,
        second_node_input_port,
        second_node_output_port,
        input_port,
    ):
        """Excluding an edge by ID prevents it from being considered."""
        # Create A→B
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version, source_node=node, target_node=second_node
        )
        edge_ab = Edge.no_workspace_objects.create(
            graph_version=graph_version,
            source_port=output_port,
            target_port=second_node_input_port,
        )
        # B→A would normally be a cycle, but excluding A→B means no cycle
        assert (
            would_create_cycle(
                second_node.id,
                node.id,
                graph_version.id,
                exclude_edge_id=edge_ab.id,
            )
            is False
        )


@pytest.mark.unit
class TestWouldCreateCycleNullWorkspace:
    """Tests for would_create_cycle when graph has workspace=None."""

    def test_self_loop_null_workspace(self, db, graph_version_no_ws, node_a_no_ws):
        """Same node as source/target returns True (null workspace)."""
        assert (
            would_create_cycle(node_a_no_ws.id, node_a_no_ws.id, graph_version_no_ws.id)
            is True
        )

    def test_cycle_detected_null_workspace(
        self,
        db,
        graph_version_no_ws,
        node_a_no_ws,
        node_a_no_ws_output,
        node_b_no_ws,
        node_b_no_ws_input,
    ):
        """A->B exists, B->A would create cycle (null workspace)."""
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version_no_ws,
            source_node=node_a_no_ws,
            target_node=node_b_no_ws,
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version_no_ws,
            source_port=node_a_no_ws_output,
            target_port=node_b_no_ws_input,
        )
        assert (
            would_create_cycle(node_b_no_ws.id, node_a_no_ws.id, graph_version_no_ws.id)
            is True
        )

    def test_no_cycle_null_workspace(
        self,
        db,
        graph_version_no_ws,
        node_a_no_ws,
        node_a_no_ws_output,
        node_b_no_ws,
        node_b_no_ws_input,
        node_template,
    ):
        """A->B exists, B->C does not create a cycle (null workspace)."""
        NodeConnection.no_workspace_objects.create(
            graph_version=graph_version_no_ws,
            source_node=node_a_no_ws,
            target_node=node_b_no_ws,
        )
        Edge.no_workspace_objects.create(
            graph_version=graph_version_no_ws,
            source_port=node_a_no_ws_output,
            target_port=node_b_no_ws_input,
        )
        node_c = Node.no_workspace_objects.create(
            graph_version=graph_version_no_ws,
            node_template=node_template,
            type=NodeType.ATOMIC,
            name="Node C (no ws)",
            config={},
            position={"x": 500, "y": 100},
        )
        assert (
            would_create_cycle(node_b_no_ws.id, node_c.id, graph_version_no_ws.id)
            is False
        )


@pytest.mark.unit
class TestWouldCreateGraphReferenceCycle:
    """Tests for would_create_graph_reference_cycle utility function."""

    def test_self_reference_detected(self, db, organization, workspace, user):
        """Same graph as source and target returns True."""
        graph = Graph.no_workspace_objects.create(
            organization=organization,
            workspace=workspace,
            name="Self",
            created_by=user,
        )
        assert would_create_graph_reference_cycle(graph.id, graph.id) is True

    def test_direct_cycle_detected(self, db, organization, workspace, user):
        """A->B exists, B->A returns True."""
        graph_a = Graph.no_workspace_objects.create(
            organization=organization,
            workspace=workspace,
            name="A",
            created_by=user,
        )
        graph_b = Graph.no_workspace_objects.create(
            organization=organization,
            workspace=workspace,
            name="B",
            created_by=user,
        )
        ver_a = GraphVersion.no_workspace_objects.create(
            graph=graph_a,
            version_number=1,
            status=GraphVersionStatus.DRAFT,
        )
        active_b = GraphVersion.no_workspace_objects.create(
            graph=graph_b,
            version_number=1,
            status=GraphVersionStatus.ACTIVE,
        )
        # A -> B
        Node.no_workspace_objects.create(
            graph_version=ver_a,
            ref_graph_version=active_b,
            type=NodeType.SUBGRAPH,
            name="A->B",
            config={},
        )
        # B -> A would create cycle
        assert would_create_graph_reference_cycle(graph_b.id, graph_a.id) is True

    def test_transitive_cycle_detected(self, db, organization, workspace, user):
        """A->B->C exists, C->A returns True."""
        graphs = {}
        versions = {}
        active_versions = {}
        for name in ["A", "B", "C"]:
            g = Graph.no_workspace_objects.create(
                organization=organization,
                workspace=workspace,
                name=name,
                created_by=user,
            )
            graphs[name] = g
            versions[name] = GraphVersion.no_workspace_objects.create(
                graph=g,
                version_number=1,
                status=GraphVersionStatus.DRAFT,
            )
            active_versions[name] = GraphVersion.no_workspace_objects.create(
                graph=g,
                version_number=2,
                status=GraphVersionStatus.ACTIVE,
            )

        # A->B, B->C
        Node.no_workspace_objects.create(
            graph_version=versions["A"],
            ref_graph_version=active_versions["B"],
            type=NodeType.SUBGRAPH,
            name="A->B",
            config={},
        )
        Node.no_workspace_objects.create(
            graph_version=versions["B"],
            ref_graph_version=active_versions["C"],
            type=NodeType.SUBGRAPH,
            name="B->C",
            config={},
        )
        # C->A would create cycle
        assert (
            would_create_graph_reference_cycle(graphs["C"].id, graphs["A"].id) is True
        )

    def test_no_cycle(self, db, organization, workspace, user):
        """A->B exists, B->C returns False (no cycle)."""
        graph_a = Graph.no_workspace_objects.create(
            organization=organization,
            workspace=workspace,
            name="A",
            created_by=user,
        )
        graph_b = Graph.no_workspace_objects.create(
            organization=organization,
            workspace=workspace,
            name="B",
            created_by=user,
        )
        graph_c = Graph.no_workspace_objects.create(
            organization=organization,
            workspace=workspace,
            name="C",
            created_by=user,
        )
        ver_a = GraphVersion.no_workspace_objects.create(
            graph=graph_a,
            version_number=1,
            status=GraphVersionStatus.DRAFT,
        )
        active_b = GraphVersion.no_workspace_objects.create(
            graph=graph_b,
            version_number=1,
            status=GraphVersionStatus.ACTIVE,
        )
        # A -> B
        Node.no_workspace_objects.create(
            graph_version=ver_a,
            ref_graph_version=active_b,
            type=NodeType.SUBGRAPH,
            name="A->B",
            config={},
        )
        # B -> C should be fine
        assert would_create_graph_reference_cycle(graph_b.id, graph_c.id) is False

    def test_diamond_no_cycle(self, db, organization, workspace, user):
        """Diamond pattern: A->B, A->C, B->D, C->D returns False."""
        graphs = {}
        versions = {}
        active_versions = {}
        for name in ["A", "B", "C", "D"]:
            g = Graph.no_workspace_objects.create(
                organization=organization,
                workspace=workspace,
                name=name,
                created_by=user,
            )
            graphs[name] = g
            versions[name] = GraphVersion.no_workspace_objects.create(
                graph=g,
                version_number=1,
                status=GraphVersionStatus.DRAFT,
            )
            active_versions[name] = GraphVersion.no_workspace_objects.create(
                graph=g,
                version_number=2,
                status=GraphVersionStatus.ACTIVE,
            )

        Node.no_workspace_objects.create(
            graph_version=versions["A"],
            ref_graph_version=active_versions["B"],
            type=NodeType.SUBGRAPH,
            name="A->B",
            config={},
        )
        Node.no_workspace_objects.create(
            graph_version=versions["A"],
            ref_graph_version=active_versions["C"],
            type=NodeType.SUBGRAPH,
            name="A->C",
            config={},
        )
        Node.no_workspace_objects.create(
            graph_version=versions["B"],
            ref_graph_version=active_versions["D"],
            type=NodeType.SUBGRAPH,
            name="B->D",
            config={},
        )
        # C->D is fine (diamond, no cycle)
        assert (
            would_create_graph_reference_cycle(graphs["C"].id, graphs["D"].id) is False
        )

    def test_isolated_graphs_no_cycle(self, db, organization, workspace, user):
        """Two isolated graphs: A->B returns False."""
        graph_a = Graph.no_workspace_objects.create(
            organization=organization,
            workspace=workspace,
            name="Isolated A",
            created_by=user,
        )
        graph_b = Graph.no_workspace_objects.create(
            organization=organization,
            workspace=workspace,
            name="Isolated B",
            created_by=user,
        )
        assert would_create_graph_reference_cycle(graph_a.id, graph_b.id) is False
