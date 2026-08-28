"""
Tests for store_node_inputs() in data_router module.
"""

import pytest

from agent_playground.models import (
    Edge,
    ExecutionData,
    GraphExecution,
    Node,
    NodeExecution,
    Port,
)
from agent_playground.models.choices import (
    GraphExecutionStatus,
    NodeExecutionStatus,
    PortDirection,
)
from agent_playground.models.node_connection import NodeConnection
from agent_playground.services.engine import GraphAnalyzer, store_node_inputs


@pytest.fixture
def graph_execution_for_routing(db, active_graph_version):
    """Create a GraphExecution for data routing tests."""
    return GraphExecution.no_workspace_objects.create(
        graph_version=active_graph_version,
        status=GraphExecutionStatus.RUNNING,
        input_payload={},
    )


@pytest.fixture
def two_node_chain(db, active_graph_version, node_template):
    """
    Create a two-node chain: A --edge--> B

    A has output port "response" (string schema).
    B has input port "text" (string schema) connected to A's output.
    B also has an unconnected input port "extra" (string schema).
    """
    node_a = Node.no_workspace_objects.create(
        graph_version=active_graph_version,
        node_template=node_template,
        name="Node A",
        config={},
        position={"x": 0, "y": 0},
    )
    output_port_a = Port.no_workspace_objects.create(
        node=node_a,
        key="response",
        display_name="response",
        direction=PortDirection.OUTPUT,
        data_schema={"type": "string"},
    )

    node_b = Node.no_workspace_objects.create(
        graph_version=active_graph_version,
        node_template=node_template,
        name="Node B",
        config={},
        position={"x": 200, "y": 0},
    )
    input_port_b = Port.no_workspace_objects.create(
        node=node_b,
        key="text",
        display_name="text",
        direction=PortDirection.INPUT,
        data_schema={"type": "string"},
    )
    unconnected_port_b = Port.no_workspace_objects.create(
        node=node_b,
        key="extra",
        display_name="extra",
        direction=PortDirection.INPUT,
        data_schema={"type": "string"},
    )
    output_port_b = Port.no_workspace_objects.create(
        node=node_b,
        key="result",
        display_name="result",
        direction=PortDirection.OUTPUT,
        data_schema={"type": "string"},
    )

    NodeConnection.no_workspace_objects.create(
        graph_version=active_graph_version,
        source_node=node_a,
        target_node=node_b,
    )

    edge = Edge.no_workspace_objects.create(
        graph_version=active_graph_version,
        source_port=output_port_a,
        target_port=input_port_b,
    )

    return {
        "node_a": node_a,
        "node_b": node_b,
        "output_port_a": output_port_a,
        "input_port_b": input_port_b,
        "unconnected_port_b": unconnected_port_b,
        "output_port_b": output_port_b,
        "edge": edge,
    }


@pytest.fixture
def schema_mismatch_chain(db, active_graph_version, node_template):
    """
    Create a chain where output port has string schema but input port expects integer.

    A (output: string) --edge--> B (input: integer)
    """
    node_a = Node.no_workspace_objects.create(
        graph_version=active_graph_version,
        node_template=node_template,
        name="Node A",
        config={},
        position={"x": 0, "y": 0},
    )
    output_port_a = Port.no_workspace_objects.create(
        node=node_a,
        key="response",
        display_name="response",
        direction=PortDirection.OUTPUT,
        data_schema={"type": "string"},
    )

    node_b = Node.no_workspace_objects.create(
        graph_version=active_graph_version,
        node_template=node_template,
        name="Node B",
        config={},
        position={"x": 200, "y": 0},
    )
    input_port_b = Port.no_workspace_objects.create(
        node=node_b,
        key="number_input",
        display_name="number_input",
        direction=PortDirection.INPUT,
        data_schema={"type": "integer"},
    )
    output_port_b = Port.no_workspace_objects.create(
        node=node_b,
        key="result",
        display_name="result",
        direction=PortDirection.OUTPUT,
        data_schema={"type": "string"},
    )

    NodeConnection.no_workspace_objects.create(
        graph_version=active_graph_version,
        source_node=node_a,
        target_node=node_b,
    )

    Edge.no_workspace_objects.create(
        graph_version=active_graph_version,
        source_port=output_port_a,
        target_port=input_port_b,
    )

    return {
        "node_a": node_a,
        "node_b": node_b,
        "output_port_a": output_port_a,
        "input_port_b": input_port_b,
        "output_port_b": output_port_b,
    }


@pytest.mark.unit
class TestStoreNodeInputs:
    """Tests for store_node_inputs()."""

    def test_creates_execution_data_for_connected_input(
        self, db, two_node_chain, graph_execution_for_routing
    ):
        """Connected input port should get an ExecutionData record."""
        node_b = two_node_chain["node_b"]
        input_port_b = two_node_chain["input_port_b"]

        topology = GraphAnalyzer.analyze(graph_execution_for_routing.graph_version_id)

        node_execution_b = NodeExecution.no_workspace_objects.create(
            graph_execution=graph_execution_for_routing,
            node=node_b,
            status=NodeExecutionStatus.RUNNING,
        )

        inputs = {"text": "hello world"}
        result = store_node_inputs(
            node_id=node_b.id,
            node_execution=node_execution_b,
            topology=topology,
            inputs=inputs,
        )

        assert result.all_valid is True
        assert len(result.routed_ports) == 1
        assert result.routed_ports[0].port_id == input_port_b.id
        assert result.routed_ports[0].port_key == "text"
        assert result.routed_ports[0].is_valid is True

        # Verify ExecutionData was created
        ed = ExecutionData.no_workspace_objects.get(
            node_execution=node_execution_b,
            port=input_port_b,
        )
        assert ed.payload == "hello world"
        assert ed.is_valid is True

    def test_skips_unconnected_input_ports(
        self, db, two_node_chain, graph_execution_for_routing
    ):
        """Unconnected input ports should NOT get ExecutionData from store_node_inputs."""
        node_b = two_node_chain["node_b"]
        unconnected_port_b = two_node_chain["unconnected_port_b"]

        topology = GraphAnalyzer.analyze(graph_execution_for_routing.graph_version_id)

        node_execution_b = NodeExecution.no_workspace_objects.create(
            graph_execution=graph_execution_for_routing,
            node=node_b,
            status=NodeExecutionStatus.RUNNING,
        )

        inputs = {"text": "hello", "extra": "bonus"}
        result = store_node_inputs(
            node_id=node_b.id,
            node_execution=node_execution_b,
            topology=topology,
            inputs=inputs,
        )

        # Only the connected port should be stored
        assert len(result.routed_ports) == 1
        assert result.routed_ports[0].port_key == "text"

        # Unconnected port should have no ExecutionData
        assert not ExecutionData.no_workspace_objects.filter(
            node_execution=node_execution_b,
            port=unconnected_port_b,
        ).exists()

    def test_validates_against_input_port_schema(
        self, db, schema_mismatch_chain, graph_execution_for_routing
    ):
        """String value should fail validation against integer input port schema."""
        node_b = schema_mismatch_chain["node_b"]
        input_port_b = schema_mismatch_chain["input_port_b"]

        topology = GraphAnalyzer.analyze(graph_execution_for_routing.graph_version_id)

        node_execution_b = NodeExecution.no_workspace_objects.create(
            graph_execution=graph_execution_for_routing,
            node=node_b,
            status=NodeExecutionStatus.RUNNING,
        )

        # Pass a string where integer is expected
        inputs = {"number_input": "not a number"}
        result = store_node_inputs(
            node_id=node_b.id,
            node_execution=node_execution_b,
            topology=topology,
            inputs=inputs,
        )

        assert result.all_valid is False
        assert len(result.routed_ports) == 1
        assert result.routed_ports[0].is_valid is False
        assert result.routed_ports[0].validation_errors is not None

        # Data is stored but marked invalid
        ed = ExecutionData.no_workspace_objects.get(
            node_execution=node_execution_b,
            port=input_port_b,
        )
        assert ed.is_valid is False
        assert ed.payload == "not a number"

    def test_no_connected_ports_returns_empty_result(
        self, db, active_graph_version, node_template, graph_execution_for_routing
    ):
        """Node with only unconnected ports returns empty result."""
        node = Node.no_workspace_objects.create(
            graph_version=active_graph_version,
            node_template=node_template,
            name="Isolated Node",
            config={},
            position={"x": 0, "y": 0},
        )
        Port.no_workspace_objects.create(
            node=node,
            key="lonely_input",
            display_name="lonely_input",
            direction=PortDirection.INPUT,
            data_schema={"type": "string"},
        )

        topology = GraphAnalyzer.analyze(active_graph_version.id)

        node_execution = NodeExecution.no_workspace_objects.create(
            graph_execution=graph_execution_for_routing,
            node=node,
            status=NodeExecutionStatus.RUNNING,
        )

        result = store_node_inputs(
            node_id=node.id,
            node_execution=node_execution,
            topology=topology,
            inputs={"lonely_input": "value"},
        )

        assert result.all_valid is True
        assert len(result.routed_ports) == 0

    def test_idempotent_on_repeated_calls(
        self, db, two_node_chain, graph_execution_for_routing
    ):
        """Calling store_node_inputs twice should update, not duplicate."""
        node_b = two_node_chain["node_b"]
        input_port_b = two_node_chain["input_port_b"]

        topology = GraphAnalyzer.analyze(graph_execution_for_routing.graph_version_id)

        node_execution_b = NodeExecution.no_workspace_objects.create(
            graph_execution=graph_execution_for_routing,
            node=node_b,
            status=NodeExecutionStatus.RUNNING,
        )

        inputs = {"text": "first"}
        store_node_inputs(
            node_id=node_b.id,
            node_execution=node_execution_b,
            topology=topology,
            inputs=inputs,
        )

        # Call again with different value
        inputs = {"text": "second"}
        result = store_node_inputs(
            node_id=node_b.id,
            node_execution=node_execution_b,
            topology=topology,
            inputs=inputs,
        )

        assert result.all_valid is True
        assert len(result.routed_ports) == 1

        # Should have exactly one record, not two
        count = ExecutionData.no_workspace_objects.filter(
            node_execution=node_execution_b,
            port=input_port_b,
        ).count()
        assert count == 1

    def test_skips_missing_input_keys(
        self, db, two_node_chain, graph_execution_for_routing
    ):
        """Connected port whose routing_key is not in inputs dict should be skipped."""
        node_b = two_node_chain["node_b"]

        topology = GraphAnalyzer.analyze(graph_execution_for_routing.graph_version_id)

        node_execution_b = NodeExecution.no_workspace_objects.create(
            graph_execution=graph_execution_for_routing,
            node=node_b,
            status=NodeExecutionStatus.RUNNING,
        )

        # Pass empty inputs — connected port "text" is missing
        result = store_node_inputs(
            node_id=node_b.id,
            node_execution=node_execution_b,
            topology=topology,
            inputs={},
        )

        assert result.all_valid is True
        assert len(result.routed_ports) == 0
