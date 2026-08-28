"""
Graph Execution Engine.

This module provides the core execution engine for running GraphVersions as DAGs.
It integrates with Temporal for workflow orchestration and supports parallel execution
of independent nodes.

Public API:
    - GraphAnalyzer: Analyzes graph structure and builds topology
    - GraphTopology: Dataclass containing derived graph structure lookups
    - DataRouter: Routes data between nodes during execution
    - BaseNodeRunner: Abstract base class for pluggable node execution
    - NodeRunner: Alias for BaseNodeRunner (backward compatibility)
    - register_runner: Register a runner for a node template
    - get_runner: Get a runner for a node template

Exceptions:
    - GraphEngineError: Base exception for all engine errors
    - GraphValidationError: Graph structure validation failed
    - NodeNotReadyError: Node has unsatisfied inputs
    - NodeExecutionError: Node failed during execution
    - NodeRunnerNotFoundError: No runner for template
    - ModuleExecutionError: Child graph execution failed
    - GraphCancelledError: Execution was cancelled

Example:
    from agent_playground.services.engine import (
        GraphAnalyzer,
        register_runner,
        get_runner,
    )

    # Analyze a graph version
    topology = GraphAnalyzer.analyze(graph_version_id)

    # Register a custom runner
    register_runner("my_template", MyCustomRunner())
"""

import agent_playground.services.engine.output_sinks  # noqa: F401

# Import runners and sinks to trigger registration
import agent_playground.services.engine.runners  # noqa: F401
from agent_playground.services.engine.analyzer import GraphAnalyzer, GraphTopology
from agent_playground.services.engine.data_router import (
    GraphInputInjectionResult,
    InjectionResult,
    OutputRoutingResult,
    collect_graph_outputs,
    collect_node_inputs,
    inject_graph_inputs,
    route_module_outputs,
    route_node_outputs,
    store_node_inputs,
)
from agent_playground.services.engine.exceptions import (
    GraphCancelledError,
    GraphEngineError,
    GraphValidationError,
    ModuleExecutionError,
    NodeExecutionError,
    NodeNotReadyError,
    NodeRunnerNotFoundError,
)
from agent_playground.services.engine.node_runner import (
    BaseNodeRunner,
    NodeRunner,
    RunnerResult,
    clear_runners,
    get_runner,
    has_runner,
    list_runners,
    register_runner,
)
from agent_playground.services.engine.output_sink import (
    BaseOutputSink,
    OutputSinkContext,
    call_sinks,
    clear_sinks,
    get_sink,
    has_sink,
    list_sinks,
    register_sink,
)
from agent_playground.services.engine.readiness import (
    NodeReadinessResult,
    PortSatisfactionInfo,
    check_node_readiness,
    get_ready_and_skip_nodes,
    mark_node_skipped,
)

__all__ = [
    # Analyzer
    "GraphAnalyzer",
    "GraphTopology",
    # Data Router
    "InjectionResult",
    "GraphInputInjectionResult",
    "OutputRoutingResult",
    "inject_graph_inputs",
    "collect_node_inputs",
    "route_node_outputs",
    "store_node_inputs",
    "collect_graph_outputs",
    "route_module_outputs",
    # Node Runner
    "BaseNodeRunner",
    "NodeRunner",
    "RunnerResult",
    "register_runner",
    "get_runner",
    "has_runner",
    "list_runners",
    "clear_runners",
    # Output Sinks
    "BaseOutputSink",
    "OutputSinkContext",
    "register_sink",
    "get_sink",
    "has_sink",
    "list_sinks",
    "clear_sinks",
    "call_sinks",
    # Readiness
    "NodeReadinessResult",
    "PortSatisfactionInfo",
    "check_node_readiness",
    "get_ready_and_skip_nodes",
    "mark_node_skipped",
    # Exceptions
    "GraphEngineError",
    "GraphValidationError",
    "NodeNotReadyError",
    "NodeExecutionError",
    "NodeRunnerNotFoundError",
    "ModuleExecutionError",
    "GraphCancelledError",
]
