"""
Graph Analyzer for building topology from GraphVersion.

The GraphAnalyzer performs a one-time analysis of a GraphVersion to build
a GraphTopology dataclass containing all the derived lookup structures
needed for execution. This avoids repeated database queries during execution.

Module Node Handling:
    Module nodes have node_template=None and ref_graph_version set.
    At execution time, the executor will recursively execute the child graph.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from uuid import UUID

from agent_playground.models.choices import NodeType, PortDirection
from agent_playground.services.engine.exceptions import GraphValidationError

if TYPE_CHECKING:
    from agent_playground.models import Edge, Node, Port


@dataclass
class GraphTopology:
    """
    Derived topology of a GraphVersion for efficient execution.

    Core attributes (from DB):
        graph_version_id: The ID of the analyzed GraphVersion
        nodes: Mapping of node_id -> Node instance
        ports: Mapping of port_id -> Port instance
        edges: List of all Edge instances

    Port groupings:
        node_input_ports: node_id -> list of input Ports
        node_output_ports: node_id -> list of output Ports

    Adjacency (for readiness/failure propagation):
        adjacency: node_id -> downstream node_ids (for failure propagation)
        reverse_adjacency: node_id -> upstream node_ids (for readiness checks)

    Execution order:
        start_node_ids: Nodes with no connected input ports
        end_node_ids: Nodes with no connected output ports
        topological_order: Valid execution order (respects dependencies)

    Graph boundaries (unconnected ports = graph inputs/outputs):
        unconnected_input_ports: Input ports needing data from input_payload
        unconnected_output_ports: Output ports that become graph outputs

    Edge lookups (for data routing):
        edge_by_target_port: target_port_id -> Edge (to find data source for an input)
    """

    graph_version_id: UUID

    # Django model instances
    nodes: dict[UUID, "Node"] = field(default_factory=dict)
    ports: dict[UUID, "Port"] = field(default_factory=dict)
    edges: list["Edge"] = field(default_factory=list)

    # Port groupings by node
    node_input_ports: dict[UUID, list["Port"]] = field(default_factory=dict)
    node_output_ports: dict[UUID, list["Port"]] = field(default_factory=dict)

    # Adjacency maps for dependency tracking
    adjacency: dict[UUID, set[UUID]] = field(default_factory=dict)
    reverse_adjacency: dict[UUID, set[UUID]] = field(default_factory=dict)

    # Execution order
    start_node_ids: list[UUID] = field(default_factory=list)
    end_node_ids: list[UUID] = field(default_factory=list)
    topological_order: list[UUID] = field(default_factory=list)

    # Graph boundaries
    unconnected_input_ports: list["Port"] = field(default_factory=list)
    unconnected_output_ports: list["Port"] = field(default_factory=list)

    # Edge lookup for data routing
    edge_by_target_port: dict[UUID, "Edge"] = field(default_factory=dict)

    def get_node(self, node_id: UUID) -> "Node":
        """Get a node by ID."""
        return self.nodes[node_id]

    def get_port(self, port_id: UUID) -> "Port":
        """Get a port by ID."""
        return self.ports[port_id]

    def get_upstream_nodes(self, node_id: UUID) -> set[UUID]:
        """Get nodes that must complete before this node can run."""
        return self.reverse_adjacency.get(node_id, set())

    def get_downstream_nodes(self, node_id: UUID) -> set[UUID]:
        """Get nodes that depend on this node's output."""
        return self.adjacency.get(node_id, set())

    def is_module_node(self, node_id: UUID) -> bool:
        """
        Check if node is a module (executes child graph).

        Module nodes have ref_graph_version set and node_template is None.
        """
        node = self.nodes[node_id]
        return node.type == NodeType.SUBGRAPH or (
            node.ref_graph_version_id is not None and node.node_template_id is None
        )

    def get_module_child_graph_version_id(self, node_id: UUID) -> UUID:
        """Get the child graph version ID for a module node."""
        node = self.nodes[node_id]
        if not node.ref_graph_version_id:
            raise ValueError(f"Node {node_id} is not a module node")
        return node.ref_graph_version_id

    def to_dict(self) -> dict:
        """Serialize computed structural data to a JSON-serializable dict.

        Only serializes derived data (adjacency, topological order, etc.)
        that is expensive to recompute. Model instances (nodes, ports, edges)
        are NOT serialized — from_dict() re-fetches them from the DB.
        """
        return {
            "graph_version_id": str(self.graph_version_id),
            "adjacency": {
                str(k): [str(v) for v in vals] for k, vals in self.adjacency.items()
            },
            "reverse_adjacency": {
                str(k): [str(v) for v in vals]
                for k, vals in self.reverse_adjacency.items()
            },
            "start_node_ids": [str(nid) for nid in self.start_node_ids],
            "end_node_ids": [str(nid) for nid in self.end_node_ids],
            "topological_order": [str(nid) for nid in self.topological_order],
            "unconnected_input_port_ids": [
                str(p.id) for p in self.unconnected_input_ports
            ],
            "unconnected_output_port_ids": [
                str(p.id) for p in self.unconnected_output_ports
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GraphTopology":
        """Reconstruct GraphTopology from serialized dict.

        Loads Django model instances from DB (3 queries: nodes, ports, edges)
        and uses pre-computed structural data from the dict. Skips the
        analysis algorithm (adjacency building, topological sort, validation).
        """
        from agent_playground.models import Edge, Node, Port

        graph_version_id = UUID(data["graph_version_id"])

        # Load model instances from DB (3 queries)
        nodes_qs = Node.no_workspace_objects.filter(
            graph_version_id=graph_version_id,
        ).select_related("node_template", "ref_graph_version")
        nodes: dict[UUID, Node] = {node.id: node for node in nodes_qs}

        node_ids = list(nodes.keys())
        ports_qs = Port.no_workspace_objects.filter(node_id__in=node_ids)
        ports: dict[UUID, Port] = {port.id: port for port in ports_qs}

        edges_qs = Edge.no_workspace_objects.filter(
            graph_version_id=graph_version_id,
        )
        edges: list[Edge] = list(edges_qs)

        # Rebuild port groupings from loaded ports
        node_input_ports: dict[UUID, list[Port]] = defaultdict(list)
        node_output_ports: dict[UUID, list[Port]] = defaultdict(list)
        for port in ports.values():
            if port.direction == PortDirection.INPUT:
                node_input_ports[port.node_id].append(port)
            else:
                node_output_ports[port.node_id].append(port)

        # Rebuild edge lookup
        edge_by_target_port: dict[UUID, Edge] = {}
        for edge in edges:
            edge_by_target_port[edge.target_port_id] = edge

        # Restore pre-computed structural data from serialized dict
        adjacency: dict[UUID, set[UUID]] = {
            UUID(k): {UUID(v) for v in vals} for k, vals in data["adjacency"].items()
        }
        reverse_adjacency: dict[UUID, set[UUID]] = {
            UUID(k): {UUID(v) for v in vals}
            for k, vals in data["reverse_adjacency"].items()
        }
        start_node_ids = [UUID(nid) for nid in data["start_node_ids"]]
        end_node_ids = [UUID(nid) for nid in data["end_node_ids"]]
        topological_order = [UUID(nid) for nid in data["topological_order"]]

        # Restore unconnected ports as model instances
        unconnected_input_port_ids = {
            UUID(pid) for pid in data["unconnected_input_port_ids"]
        }
        unconnected_output_port_ids = {
            UUID(pid) for pid in data["unconnected_output_port_ids"]
        }
        unconnected_input_ports = [
            ports[pid] for pid in unconnected_input_port_ids if pid in ports
        ]
        unconnected_output_ports = [
            ports[pid] for pid in unconnected_output_port_ids if pid in ports
        ]

        return cls(
            graph_version_id=graph_version_id,
            nodes=nodes,
            ports=ports,
            edges=edges,
            node_input_ports=dict(node_input_ports),
            node_output_ports=dict(node_output_ports),
            adjacency=adjacency,
            reverse_adjacency=reverse_adjacency,
            start_node_ids=start_node_ids,
            end_node_ids=end_node_ids,
            topological_order=topological_order,
            unconnected_input_ports=unconnected_input_ports,
            unconnected_output_ports=unconnected_output_ports,
            edge_by_target_port=edge_by_target_port,
        )


class GraphAnalyzer:
    """
    Analyzes a GraphVersion and builds a GraphTopology.

    Usage:
        topology = GraphAnalyzer.analyze(graph_version_id)
    """

    @staticmethod
    def analyze(graph_version_id: UUID) -> GraphTopology:
        """
        Analyze a GraphVersion and build its topology.

        Raises:
            GraphValidationError: If graph has no nodes, no start nodes, or cycles
        """
        from agent_playground.models import Edge, GraphVersion, Node, Port

        # Load GraphVersion
        try:
            GraphVersion.no_workspace_objects.get(id=graph_version_id)
        except GraphVersion.DoesNotExist:
            raise GraphValidationError(
                f"GraphVersion not found: {graph_version_id}",
                graph_version_id=graph_version_id,
            )

        # Load nodes with templates and ref_graph_versions
        nodes_qs = Node.no_workspace_objects.filter(
            graph_version_id=graph_version_id,
        ).select_related("node_template", "ref_graph_version")

        nodes: dict[UUID, Node] = {node.id: node for node in nodes_qs}

        if not nodes:
            raise GraphValidationError(
                "Graph has no nodes",
                graph_version_id=graph_version_id,
            )

        # Load ports and group by node/direction
        node_ids = list(nodes.keys())
        ports_qs = Port.no_workspace_objects.filter(node_id__in=node_ids)
        ports: dict[UUID, Port] = {port.id: port for port in ports_qs}

        node_input_ports: dict[UUID, list[Port]] = defaultdict(list)
        node_output_ports: dict[UUID, list[Port]] = defaultdict(list)

        for port in ports.values():
            if port.direction == PortDirection.INPUT:
                node_input_ports[port.node_id].append(port)
            else:
                node_output_ports[port.node_id].append(port)

        # Load edges
        edges_qs = Edge.no_workspace_objects.filter(
            graph_version_id=graph_version_id,
        )
        edges: list[Edge] = list(edges_qs)

        # Build edge lookup and track connected ports
        edge_by_target_port: dict[UUID, Edge] = {}
        connected_input_ports: set[UUID] = set()
        connected_output_ports: set[UUID] = set()

        for edge in edges:
            edge_by_target_port[edge.target_port_id] = edge
            connected_input_ports.add(edge.target_port_id)
            connected_output_ports.add(edge.source_port_id)

        # Build adjacency maps (node-level dependencies)
        adjacency: dict[UUID, set[UUID]] = defaultdict(set)
        reverse_adjacency: dict[UUID, set[UUID]] = defaultdict(set)

        for edge in edges:
            source_port = ports.get(edge.source_port_id)
            target_port = ports.get(edge.target_port_id)

            if source_port and target_port:
                source_node_id = source_port.node_id
                target_node_id = target_port.node_id

                adjacency[source_node_id].add(target_node_id)
                reverse_adjacency[target_node_id].add(source_node_id)

        # Identify start nodes: ALL input ports unconnected (or no input ports)
        start_node_ids: list[UUID] = []
        for node_id in nodes:
            input_ports = node_input_ports.get(node_id, [])
            if not input_ports or all(
                port.id not in connected_input_ports for port in input_ports
            ):
                start_node_ids.append(node_id)

        if not start_node_ids:
            raise GraphValidationError(
                "Graph has no start nodes",
                graph_version_id=graph_version_id,
            )

        # Identify end nodes: ALL output ports unconnected (or no output ports)
        end_node_ids: list[UUID] = []
        for node_id in nodes:
            output_ports = node_output_ports.get(node_id, [])
            if not output_ports or all(
                port.id not in connected_output_ports for port in output_ports
            ):
                end_node_ids.append(node_id)

        # Topological sort
        topological_order = GraphAnalyzer._topological_sort(
            nodes, adjacency, reverse_adjacency, graph_version_id
        )

        # Graph boundary ports
        unconnected_input_ports = [
            port
            for port in ports.values()
            if port.direction == PortDirection.INPUT
            and port.id not in connected_input_ports
        ]
        unconnected_output_ports = [
            port
            for port in ports.values()
            if port.direction == PortDirection.OUTPUT
            and port.id not in connected_output_ports
        ]

        return GraphTopology(
            graph_version_id=graph_version_id,
            nodes=nodes,
            ports=ports,
            edges=edges,
            node_input_ports=dict(node_input_ports),
            node_output_ports=dict(node_output_ports),
            adjacency=dict(adjacency),
            reverse_adjacency=dict(reverse_adjacency),
            start_node_ids=start_node_ids,
            end_node_ids=end_node_ids,
            topological_order=topological_order,
            unconnected_input_ports=unconnected_input_ports,
            unconnected_output_ports=unconnected_output_ports,
            edge_by_target_port=edge_by_target_port,
        )

    @staticmethod
    def _topological_sort(
        nodes: dict[UUID, "Node"],
        adjacency: dict[UUID, set[UUID]],
        reverse_adjacency: dict[UUID, set[UUID]],
        graph_version_id: UUID,
    ) -> list[UUID]:
        """Topological sort using Kahn's algorithm."""
        in_degree: dict[UUID, int] = {
            node_id: len(reverse_adjacency.get(node_id, [])) for node_id in nodes
        }

        queue: list[UUID] = [nid for nid, deg in in_degree.items() if deg == 0]
        result: list[UUID] = []

        while queue:
            queue.sort()  # Deterministic ordering
            node_id = queue.pop(0)
            result.append(node_id)

            for downstream_id in adjacency.get(node_id, []):
                in_degree[downstream_id] -= 1
                if in_degree[downstream_id] == 0:
                    queue.append(downstream_id)

        if len(result) != len(nodes):
            cycle_nodes = [nid for nid, deg in in_degree.items() if deg > 0]
            raise GraphValidationError(
                f"Graph contains a cycle involving {len(cycle_nodes)} nodes",
                graph_version_id=graph_version_id,
                details={"cycle_node_ids": [str(nid) for nid in cycle_nodes]},
            )

        return result
