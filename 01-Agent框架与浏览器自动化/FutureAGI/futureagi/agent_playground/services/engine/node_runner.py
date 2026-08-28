"""
Node Runner ABC and Registry.

This module defines the abstract base class for pluggable node execution and
provides a registry for managing node runners.

Adding New Node Types:
    1. Create a new file in runners/ (e.g., runners/http_request.py)
    2. Subclass BaseNodeRunner and implement the run() method
    3. Register with register_runner("template_name", RunnerClass())
    4. Import and register in runners/__init__.py

Example:
    from agent_playground.services.engine.node_runner import BaseNodeRunner, register_runner

    class MyRunner(BaseNodeRunner):
        def run(self, config: dict, inputs: dict, execution_context: dict) -> dict:
            # Process inputs using config
            result = do_something(config["setting"], inputs["data"])
            return {"output": result}

    register_runner("my_template", MyRunner())
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from agent_playground.services.engine.exceptions import NodeRunnerNotFoundError


class BaseNodeRunner(ABC):
    """
    Abstract base class for node execution.

    Node runners implement the business logic for executing a specific node type.
    Each node template maps to exactly one runner.

    Methods:
        run: Execute node logic with config and inputs, return outputs
    """

    @abstractmethod
    def run(
        self,
        config: dict[str, Any],
        inputs: dict[str, Any],
        execution_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute node logic.

        Args:
            config: Node.config (validated against template's config_schema).
                    Contains node-specific settings like model name, API keys, etc.
            inputs: Dict mapping input port routing keys to their values.
                    For template ports, routing key = port.key.
                    For custom ports, routing key = port.display_name.
            execution_context: Execution-level context (organization_id, workspace_id, etc.)
                    provided by the engine at runtime.

        Returns:
            Dict mapping output port routing keys to their values.
            These values will be written to output ports and validated
            against each port's data_schema.

        Raises:
            Exception: Any exception will be caught and the node will be
                      marked as FAILED with the error message stored.
        """
        ...


# Backward compatibility alias
NodeRunner = BaseNodeRunner


@dataclass
class RunnerResult:
    """Result of running a node."""

    outputs: dict[str, Any]
    metadata: dict[str, Any] | None = None


# Registry for node runners
_runners: dict[str, BaseNodeRunner] = {}


def register_runner(template_name: str, runner: BaseNodeRunner) -> None:
    """
    Register a runner for a node template.

    Args:
        template_name: The name of the node template (e.g., "llm_prompt")
        runner: An instance of BaseNodeRunner

    Raises:
        TypeError: If runner doesn't subclass BaseNodeRunner
    """
    if not isinstance(runner, BaseNodeRunner):
        raise TypeError(
            f"Runner for '{template_name}' must be a subclass of BaseNodeRunner. "
            f"Got {type(runner).__name__}"
        )
    _runners[template_name] = runner


def get_runner(template_name: str) -> BaseNodeRunner:
    """
    Get the runner for a node template.

    Args:
        template_name: The name of the node template

    Returns:
        The registered BaseNodeRunner instance

    Raises:
        NodeRunnerNotFoundError: If no runner is registered for the template
    """
    runner = _runners.get(template_name)
    if runner is None:
        raise NodeRunnerNotFoundError(template_name)
    return runner


def has_runner(template_name: str) -> bool:
    """
    Check if a runner is registered for a template.

    Args:
        template_name: The name of the node template

    Returns:
        True if a runner is registered, False otherwise
    """
    return template_name in _runners


def list_runners() -> list[str]:
    """
    List all registered runner template names.

    Returns:
        List of template names with registered runners
    """
    return list(_runners.keys())


def clear_runners() -> None:
    """
    Clear all registered runners.

    Primarily used for testing.
    """
    _runners.clear()
