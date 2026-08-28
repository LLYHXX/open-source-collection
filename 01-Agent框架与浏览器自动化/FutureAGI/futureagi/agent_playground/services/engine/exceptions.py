"""
Custom exception hierarchy for the Graph Execution Engine.

All exceptions inherit from GraphEngineError, which is the base exception
for the engine. This allows callers to catch all engine-related errors
with a single except clause if desired.
"""

from typing import Any, Optional
from uuid import UUID


class GraphEngineError(Exception):
    """
    Base exception for all graph execution engine errors.

    All other engine exceptions inherit from this class.
    """

    pass


class GraphValidationError(GraphEngineError):
    """
    Raised when graph validation fails.

    This can happen when:
    - Graph has no nodes
    - Graph has no start nodes (all nodes have incoming edges)
    - Graph contains cycles (not a valid DAG)
    - GraphVersion is not in ACTIVE status
    - Required input is missing from input_payload
    """

    def __init__(
        self,
        message: str,
        graph_version_id: Optional[UUID] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.graph_version_id = graph_version_id
        self.details = details or {}


class NodeNotReadyError(GraphEngineError):
    """
    Raised when attempting to execute a node that has unsatisfied inputs.

    This error indicates a programming error in the readiness checking logic,
    as nodes should only be executed when all their inputs are satisfied.
    """

    def __init__(
        self,
        message: str,
        node_id: UUID,
        missing_ports: Optional[list[str]] = None,
    ):
        super().__init__(message)
        self.node_id = node_id
        self.missing_ports = missing_ports or []


class NodeExecutionError(GraphEngineError):
    """
    Raised when a node fails during execution.

    This wraps the original error that occurred during node execution,
    preserving context about which node failed.
    """

    def __init__(
        self,
        message: str,
        node_id: UUID,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.node_id = node_id
        self.original_error = original_error

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.original_error:
            return f"{base_msg}: {self.original_error}"
        return base_msg


class NodeRunnerNotFoundError(GraphEngineError):
    """
    Raised when no runner is registered for a node template.

    This indicates that the node template exists but no corresponding
    runner has been registered to execute it.

    To fix this error, register a runner using:
        register_runner("template_name", MyRunner())
    """

    def __init__(self, template_name: str):
        super().__init__(f"No runner registered for template: {template_name}")
        self.template_name = template_name


class ModuleExecutionError(GraphEngineError):
    """
    Raised when a module node's child graph execution fails.

    This can happen during:
    - Input injection into the child graph
    - Child graph execution
    - Output extraction from the child graph
    """

    def __init__(
        self,
        message: str,
        module_node_id: UUID,
        child_graph_version_id: Optional[UUID] = None,
        child_graph_execution_id: Optional[UUID] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.module_node_id = module_node_id
        self.child_graph_version_id = child_graph_version_id
        self.child_graph_execution_id = child_graph_execution_id
        self.original_error = original_error


class GraphCancelledError(GraphEngineError):
    """
    Raised when a graph execution is cancelled externally.

    This can happen when:
    - User requests cancellation via API
    - Temporal workflow is cancelled
    - System shutdown during execution
    """

    def __init__(
        self,
        message: str = "Graph execution was cancelled",
        graph_execution_id: Optional[UUID] = None,
    ):
        super().__init__(message)
        self.graph_execution_id = graph_execution_id
