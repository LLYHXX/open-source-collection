"""
Temporal workflows for simulate app.

This module contains workflows and activities for:
- Scenario data generation
- Scenario column addition
- Scenario creation (dataset, script, graph)

Note: Test execution workflows have been removed - using Celery tasks instead.

Structure:
    simulate/
    ├── __init__.py      # This file - exports
    ├── README.md        # Architecture documentation
    ├── types.py         # Data classes (no Django imports)
    ├── workflows.py     # Workflow definitions
    ├── activities.py    # Activity definitions
    └── client.py        # Workflow starter functions
"""

# Client functions (for starting workflows)
from tfc.temporal.simulate.client import (
    start_add_columns_workflow,
    start_add_columns_workflow_sync,
    start_add_scenario_rows_workflow,
    start_add_scenario_rows_workflow_sync,
    start_create_dataset_scenario_workflow,
    start_create_dataset_scenario_workflow_sync,
    start_create_graph_scenario_workflow,
    start_create_graph_scenario_workflow_sync,
    start_create_script_scenario_workflow,
    start_create_script_scenario_workflow_sync,
    start_scenario_generation_workflow,
    start_scenario_generation_workflow_sync,
)

# Types (for type hints)
from tfc.temporal.simulate.types import (  # Scenario Generation; Scenario Creation
    AddColumnsWorkflowInput,
    AddColumnsWorkflowOutput,
    CreateDatasetScenarioWorkflowInput,
    CreateDatasetScenarioWorkflowOutput,
    CreateGraphScenarioWorkflowInput,
    CreateGraphScenarioWorkflowOutput,
    CreateScriptScenarioWorkflowInput,
    CreateScriptScenarioWorkflowOutput,
    ScenarioGenerationWorkflowInput,
    ScenarioGenerationWorkflowOutput,
)

__all__ = [
    # Client functions (async)
    "start_scenario_generation_workflow",
    "start_add_scenario_rows_workflow",
    "start_add_columns_workflow",
    "start_create_dataset_scenario_workflow",
    "start_create_script_scenario_workflow",
    "start_create_graph_scenario_workflow",
    # Client functions (sync - for Django views)
    "start_scenario_generation_workflow_sync",
    "start_add_scenario_rows_workflow_sync",
    "start_add_columns_workflow_sync",
    "start_create_dataset_scenario_workflow_sync",
    "start_create_script_scenario_workflow_sync",
    "start_create_graph_scenario_workflow_sync",
    # Workflow types
    "ScenarioGenerationWorkflowInput",
    "ScenarioGenerationWorkflowOutput",
    "AddColumnsWorkflowInput",
    "AddColumnsWorkflowOutput",
    "CreateDatasetScenarioWorkflowInput",
    "CreateDatasetScenarioWorkflowOutput",
    "CreateScriptScenarioWorkflowInput",
    "CreateScriptScenarioWorkflowOutput",
    "CreateGraphScenarioWorkflowInput",
    "CreateGraphScenarioWorkflowOutput",
]
