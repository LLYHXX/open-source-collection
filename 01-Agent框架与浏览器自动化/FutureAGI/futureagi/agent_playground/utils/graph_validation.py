from collections import defaultdict
from typing import Optional
from uuid import UUID

from django.core.exceptions import ValidationError


def validate_version_for_activation(version) -> None:
    """
    Holistic validation of all nodes and ports in a graph version.

    Called before activation (draft/inactive → active) to ensure the
    entire version is consistent. Collects all errors into a single
    ValidationError instead of failing fast.

    Args:
        version: The GraphVersion being activated.

    Raises:
        ValidationError: With a list of all validation errors found.
    """
    from agent_playground.models.node import Node
    from agent_playground.models.port import Port

    errors: list[str] = []

    # Batch-fetch all nodes with related objects needed by _validate_* methods
    nodes = list(
        Node.no_workspace_objects.filter(graph_version=version).select_related(
            "node_template",
            "ref_graph_version",
            "ref_graph_version__graph",
            "graph_version",
            "graph_version__graph",
        )
    )

    # Batch-fetch all ports with related objects needed by _validate_* methods
    ports = list(
        Port.no_workspace_objects.filter(node__graph_version=version).select_related(
            "node",
            "node__node_template",
            "node__ref_graph_version",
            "ref_port",
            "ref_port__node",
        )
    )

    # Validate each node via clean()
    for node in nodes:
        try:
            node.clean()
        except ValidationError as e:
            for msg in e.messages:
                errors.append(f"Node '{node.name}': {msg}")

    # Validate each port via clean()
    for port in ports:
        try:
            port.clean()
        except ValidationError as e:
            for msg in e.messages:
                errors.append(
                    f"Port '{port.node.name}.{port.key}' ({port.direction}): {msg}"
                )

    if errors:
        raise ValidationError(errors)


def would_create_graph_reference_cycle(
    source_graph_id: UUID,
    target_graph_id: UUID,
) -> bool:
    """
    Check whether adding a reference from source_graph to target_graph
    would create a cycle in the cross-graph reference DAG.

    Considers ALL non-deleted subgraph nodes across ALL graph versions
    (draft, active, inactive) because a draft could be promoted to active.

    Args:
        source_graph_id: The graph that would contain the new subgraph node.
        target_graph_id: The graph being referenced by the new subgraph node.

    Returns:
        True if the reference would create a cycle, False otherwise.
    """
    if source_graph_id == target_graph_id:
        return True

    from agent_playground.models.node import Node

    refs = Node.no_workspace_objects.filter(
        type="subgraph",
        ref_graph_version__isnull=False,
    ).values_list(
        "graph_version__graph_id",
        "ref_graph_version__graph_id",
    )

    adjacency: dict[UUID, list[UUID]] = defaultdict(list)
    for src, tgt in refs:
        adjacency[src].append(tgt)

    # DFS from target_graph looking for source_graph
    visited: set[UUID] = set()
    stack: list[UUID] = [target_graph_id]
    while stack:
        current = stack.pop()
        if current == source_graph_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        stack.extend(adjacency.get(current, []))

    return False


def would_create_cycle(
    source_node_id: UUID,
    target_node_id: UUID,
    graph_version_id: UUID,
    exclude_edge_id: Optional[UUID] = None,
) -> bool:
    """
    Check whether adding an edge from source_node to target_node would
    create a cycle in the graph.

    Uses DFS reachability: if source_node is reachable from target_node
    via existing edges, then the new edge would close a cycle.

    Args:
        source_node_id: The node the edge originates from.
        target_node_id: The node the edge points to.
        graph_version_id: The GraphVersion to scope the check to.
        exclude_edge_id: Optional edge ID to exclude (for update case).

    Returns:
        True if the edge would create a cycle, False otherwise.
    """
    if source_node_id == target_node_id:
        return True

    from agent_playground.models.edge import Edge

    edges_qs = Edge.no_workspace_objects.filter(graph_version_id=graph_version_id)
    if exclude_edge_id is not None:
        edges_qs = edges_qs.exclude(id=exclude_edge_id)

    adjacency: dict[UUID, list[UUID]] = defaultdict(list)
    for src, tgt in edges_qs.values_list(
        "source_port__node_id", "target_port__node_id"
    ):
        adjacency[src].append(tgt)

    # DFS from target_node looking for source_node
    visited: set[UUID] = set()
    stack: list[UUID] = [target_node_id]
    while stack:
        current = stack.pop()
        if current == source_node_id:
            return True

        # path already visited
        if current in visited:
            continue

        visited.add(current)
        stack.extend(adjacency.get(current, []))

    return False
