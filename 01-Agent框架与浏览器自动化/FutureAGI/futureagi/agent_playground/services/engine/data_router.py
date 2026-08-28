"""
Data Router for Graph Execution.

This module handles the routing of data between nodes during graph execution:
- Injecting input data into unconnected input ports (graph inputs)
- Collecting input data for node execution
- Routing output data to output ports
- Collecting output data from unconnected output ports (graph outputs)

Schema Validation:
    All data written via this module goes through ExecutionData.save() which
    automatically validates the payload against port.data_schema using jsonschema.
    The is_valid and validation_errors fields are set during save().
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

from agent_playground.models import ExecutionData, NodeExecution
from agent_playground.models.choices import NodeExecutionStatus
from agent_playground.services.engine.exceptions import GraphValidationError

if TYPE_CHECKING:
    from agent_playground.services.engine.analyzer import GraphTopology


@dataclass
class InjectionResult:
    """Result of injecting data into a port."""

    port_id: UUID
    port_key: str
    is_valid: bool
    validation_errors: dict[str, Any] | None


@dataclass
class GraphInputInjectionResult:
    """Result of injecting all graph inputs."""

    injected_ports: list[InjectionResult]
    all_valid: bool


def inject_graph_inputs(
    graph_execution_id: UUID,
    topology: "GraphTopology",
    input_payload: dict[str, Any],
) -> GraphInputInjectionResult:
    """
    Inject input data into unconnected input ports of start nodes.

    For each unconnected input port, looks up the data by port.routing_key in input_payload.
    Creates NodeExecution (PENDING) for start nodes and ExecutionData for each port.

    Data validation against port.data_schema happens automatically in
    ExecutionData.save() which sets is_valid and validation_errors.

    Args:
        graph_execution_id: Current execution context
        topology: Pre-analyzed graph topology
        input_payload: Dict mapping port routing keys to their input values

    Returns:
        GraphInputInjectionResult with validation status for each port

    Raises:
        GraphValidationError: If required input is missing from payload
    """
    from agent_playground.models import GraphExecution

    graph_execution = GraphExecution.no_workspace_objects.get(id=graph_execution_id)

    # Create NodeExecution records for start nodes
    node_executions: dict[UUID, NodeExecution] = {}
    for node_id in topology.start_node_ids:
        node_execution, _ = NodeExecution.no_workspace_objects.get_or_create(
            graph_execution_id=graph_execution_id,
            node_id=node_id,
            defaults={"status": NodeExecutionStatus.PENDING},
        )
        node_executions[node_id] = node_execution

    # Track injection results
    injected_ports: list[InjectionResult] = []
    all_valid = True

    # Inject data into unconnected input ports
    for port in topology.unconnected_input_ports:
        port_key = port.routing_key
        has_default = port.default_value is not None

        if port_key in input_payload:
            value = input_payload[port_key]
        elif has_default:
            value = port.default_value
        elif port.required:
            raise GraphValidationError(
                f"Required input '{port_key}' not provided in input_payload",
                graph_version_id=topology.graph_version_id,
                details={"missing_input": port_key, "port_id": str(port.id)},
            )
        else:
            # Optional port with no value and no default - skip
            continue

        # Get or create NodeExecution for this port's node
        node_id = port.node_id
        if node_id not in node_executions:
            node_execution, _ = NodeExecution.no_workspace_objects.get_or_create(
                graph_execution_id=graph_execution_id,
                node_id=node_id,
                defaults={"status": NodeExecutionStatus.PENDING},
            )
            node_executions[node_id] = node_execution
        else:
            node_execution = node_executions[node_id]

        # Create ExecutionData - validation against port.data_schema
        # happens in ExecutionData.save() which sets is_valid and validation_errors
        execution_data, _ = ExecutionData.no_workspace_objects.update_or_create(
            node_execution=node_execution,
            port=port,
            defaults={
                "node_id": node_id,
                "payload": value,
            },
        )

        # After save(), is_valid and validation_errors are populated
        injected_ports.append(
            InjectionResult(
                port_id=port.id,
                port_key=port_key,
                is_valid=execution_data.is_valid,
                validation_errors=execution_data.validation_errors,
            )
        )

        if not execution_data.is_valid:
            all_valid = False

    return GraphInputInjectionResult(
        injected_ports=injected_ports,
        all_valid=all_valid,
    )


def collect_node_inputs(
    node_id: UUID,
    graph_execution_id: UUID,
    topology: "GraphTopology",
) -> dict[str, Any]:
    """
    Collect all input data for a node before execution.

    For each input port:
    - If connected: get data from upstream output port
    - If unconnected: get injected data
    - If no data: use default value

    Only returns data that passed schema validation (is_valid=True).

    Args:
        node_id: The node to collect inputs for
        graph_execution_id: Current execution context
        topology: Pre-analyzed graph topology

    Returns:
        Dict mapping port routing keys to their values
    """
    inputs: dict[str, Any] = {}
    input_ports = topology.node_input_ports.get(node_id, [])

    for port in input_ports:
        edge = topology.edge_by_target_port.get(port.id)

        if edge is None:
            # Unconnected port - get injected data or default
            value = _get_valid_port_data(port.id, graph_execution_id)
            if value is None and port.default_value is not None:
                value = port.default_value
        else:
            # Connected port - get data from upstream source port
            value = _get_valid_port_data(edge.source_port_id, graph_execution_id)
            if value is None and port.default_value is not None:
                value = port.default_value

        if value is not None:
            inputs[port.routing_key] = value

    return inputs


@dataclass
class OutputRoutingResult:
    """Result of routing a node's outputs."""

    routed_ports: list[InjectionResult]
    all_valid: bool


def store_node_inputs(
    node_id: UUID,
    node_execution: NodeExecution,
    topology: "GraphTopology",
    inputs: dict[str, Any],
) -> OutputRoutingResult:
    """
    Store ExecutionData for connected input ports.

    Creates ExecutionData records for each connected input port, enabling
    input-side schema validation and per-port observability. Unconnected
    input ports are skipped since they are already handled by
    inject_graph_inputs().

    Validation against port.data_schema happens automatically in
    ExecutionData.save() which sets is_valid and validation_errors.

    Args:
        node_id: The node whose input ports to store data for
        node_execution: The NodeExecution record for this execution
        topology: Pre-analyzed graph topology
        inputs: Dict mapping port routing keys to their input values
            (as returned by collect_node_inputs)

    Returns:
        OutputRoutingResult with validation status for each stored port
    """
    input_ports = topology.node_input_ports.get(node_id, [])
    stored_ports: list[InjectionResult] = []
    all_valid = True

    for port in input_ports:
        edge = topology.edge_by_target_port.get(port.id)

        # Only store for connected input ports
        if edge is None:
            continue

        if port.routing_key not in inputs:
            continue

        value = inputs[port.routing_key]

        # Create ExecutionData - validation against port.data_schema
        # happens in ExecutionData.save() which sets is_valid and validation_errors
        execution_data, _ = ExecutionData.no_workspace_objects.update_or_create(
            node_execution=node_execution,
            port=port,
            defaults={
                "node_id": node_id,
                "payload": value,
            },
        )

        stored_ports.append(
            InjectionResult(
                port_id=port.id,
                port_key=port.routing_key,
                is_valid=execution_data.is_valid,
                validation_errors=execution_data.validation_errors,
            )
        )

        if not execution_data.is_valid:
            all_valid = False

    return OutputRoutingResult(
        routed_ports=stored_ports,
        all_valid=all_valid,
    )


def route_node_outputs(
    node_id: UUID,
    node_execution: NodeExecution,
    topology: "GraphTopology",
    outputs: dict[str, Any],
) -> OutputRoutingResult:
    """
    Route node outputs to output ports.

    Creates ExecutionData for each output port with the corresponding value
    from the outputs dict. Validation against port.data_schema happens
    automatically in ExecutionData.save().

    Args:
        node_id: The node that produced the outputs
        node_execution: The NodeExecution record for this execution
        topology: Pre-analyzed graph topology
        outputs: Dict mapping port routing keys to their output values

    Returns:
        OutputRoutingResult with validation status for each port
    """
    output_ports = topology.node_output_ports.get(node_id, [])
    routed_ports: list[InjectionResult] = []
    all_valid = True

    for port in output_ports:
        if port.routing_key in outputs:
            value = outputs[port.routing_key]

            # Create ExecutionData - validation against port.data_schema
            # happens in ExecutionData.save() which sets is_valid and validation_errors
            execution_data, _ = ExecutionData.no_workspace_objects.update_or_create(
                node_execution=node_execution,
                port=port,
                defaults={
                    "node_id": node_id,
                    "payload": value,
                },
            )

            # After save(), is_valid and validation_errors are populated
            routed_ports.append(
                InjectionResult(
                    port_id=port.id,
                    port_key=port.routing_key,
                    is_valid=execution_data.is_valid,
                    validation_errors=execution_data.validation_errors,
                )
            )

            if not execution_data.is_valid:
                all_valid = False

    return OutputRoutingResult(
        routed_ports=routed_ports,
        all_valid=all_valid,
    )


def collect_graph_outputs(
    graph_execution_id: UUID,
    topology: "GraphTopology",
) -> dict[str, Any]:
    """
    Collect final output data from unconnected output ports.

    These are the graph's output values that should be returned to the caller.
    Only returns data that passed schema validation (is_valid=True).

    Args:
        graph_execution_id: Current execution context
        topology: Pre-analyzed graph topology

    Returns:
        Dict mapping port routing keys to their output values
    """
    outputs: dict[str, Any] = {}

    for port in topology.unconnected_output_ports:
        value = _get_valid_port_data(port.id, graph_execution_id)
        if value is not None:
            outputs[port.routing_key] = value

    return outputs


def _get_valid_port_data(
    port_id: UUID,
    graph_execution_id: UUID,
) -> Any | None:
    """
    Get the payload value for a port from ExecutionData.

    Only returns data that passed schema validation (is_valid=True).

    Args:
        port_id: The port to get data for
        graph_execution_id: Current execution context

    Returns:
        The payload value if valid, or None if not found/invalid
    """
    try:
        execution_data = ExecutionData.no_workspace_objects.get(
            node_execution__graph_execution_id=graph_execution_id,
            port_id=port_id,
        )
        # Only return data that passed schema validation
        if execution_data.is_valid:
            return execution_data.payload
        return None
    except ExecutionData.DoesNotExist:
        return None


# =============================================================================
# Module Node Data Routing
# =============================================================================


def route_module_outputs(
    parent_graph_execution_id: UUID,
    child_graph_execution_id: UUID,
    module_node_id: UUID,
    parent_topology: "GraphTopology",
    child_topology: "GraphTopology",
) -> OutputRoutingResult:
    """
    Route outputs from a child graph to the module node's output ports.

    For each module output port:
    - If ref_port_id is set: uses it to directly look up the child graph
      port's ExecutionData (avoids routing_key mismatches).
    - Otherwise: falls back to routing_key matching against child graph
      outputs (backward compatibility).

    Args:
        parent_graph_execution_id: Parent execution context
        child_graph_execution_id: Child execution context
        module_node_id: The module node being executed
        parent_topology: Parent graph topology
        child_topology: Child graph topology

    Returns:
        OutputRoutingResult with validation status
    """
    from agent_playground.models import NodeExecution

    # Get the module node's NodeExecution
    node_execution = NodeExecution.no_workspace_objects.get(
        graph_execution_id=parent_graph_execution_id,
        node_id=module_node_id,
    )

    # Collect child outputs by routing_key for fallback matching
    child_outputs = collect_graph_outputs(
        graph_execution_id=child_graph_execution_id,
        topology=child_topology,
    )

    output_ports = parent_topology.node_output_ports.get(module_node_id, [])
    routed_ports: list[InjectionResult] = []
    all_valid = True

    for port in output_ports:
        value = None

        if port.ref_port_id:
            # Use ref_port_id to find the child graph port's data directly
            value = _get_valid_port_data(port.ref_port_id, child_graph_execution_id)
        elif port.routing_key in child_outputs:
            # Fallback: match by routing_key
            value = child_outputs[port.routing_key]

        if value is None:
            continue

        # Create ExecutionData on the module node's output port
        execution_data, _ = ExecutionData.no_workspace_objects.update_or_create(
            node_execution=node_execution,
            port=port,
            defaults={
                "node_id": module_node_id,
                "payload": value,
            },
        )

        routed_ports.append(
            InjectionResult(
                port_id=port.id,
                port_key=port.routing_key,
                is_valid=execution_data.is_valid,
                validation_errors=execution_data.validation_errors,
            )
        )

        if not execution_data.is_valid:
            all_valid = False

    return OutputRoutingResult(
        routed_ports=routed_ports,
        all_valid=all_valid,
    )
