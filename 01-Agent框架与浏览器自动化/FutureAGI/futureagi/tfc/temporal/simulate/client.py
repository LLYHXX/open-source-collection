"""
Client functions for starting simulate workflows.

These functions provide a simple interface for starting workflows from
Django views or other parts of the application.

Note: Test execution workflows have been removed - using Celery tasks instead.
Only scenario-related workflows remain here.
"""

import uuid
from typing import Any, Dict, List

from tfc.temporal import start_workflow_async, start_workflow_sync
from tfc.temporal.simulate.types import (
    AddColumnsWorkflowInput,
    AddScenarioRowsWorkflowInput,
    CreateDatasetScenarioWorkflowInput,
    CreateGraphScenarioWorkflowInput,
    CreateScriptScenarioWorkflowInput,
    ScenarioGenerationWorkflowInput,
)
from tfc.temporal.simulate.workflows import (
    AddScenarioColumnsWorkflow,
    AddScenarioRowsWorkflow,
    CreateDatasetScenarioWorkflow,
    CreateGraphScenarioWorkflow,
    CreateScriptScenarioWorkflow,
    ScenarioGenerationWorkflow,
)

# =============================================================================
# Scenario Generation
# =============================================================================


async def start_scenario_generation_workflow(
    dataset_id: str,
    scenario_id: str,
    num_rows: int,
    row_ids: List[str],
    *,
    description: str = "",
    organization_id: str | None = None,
    sample_size_reference_data: int = 5,
    task_queue: str = "tasks_xl",
) -> str:
    """
    Start a scenario row generation workflow.

    Args:
        dataset_id: UUID of the Dataset
        scenario_id: UUID of the Scenario
        num_rows: Number of rows to generate
        row_ids: List of pre-created row UUIDs
        description: Description for generation
        sample_size_reference_data: Number of reference rows to sample
        task_queue: Temporal task queue to use

    Returns:
        Workflow ID

    Example:
        workflow_id = await start_scenario_generation_workflow(
            dataset_id=str(dataset.id),
            scenario_id=str(scenario.id),
            num_rows=100,
            row_ids=new_row_ids,
        )
    """
    workflow_id = f"scenario-gen-{dataset_id}-{scenario_id}"

    await start_workflow_async(
        ScenarioGenerationWorkflow,
        ScenarioGenerationWorkflowInput(
            dataset_id=dataset_id,
            scenario_id=scenario_id,
            num_rows=num_rows,
            description=description,
            row_ids=row_ids,
            organization_id=organization_id,
            sample_size_reference_data=sample_size_reference_data,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
    )

    return workflow_id


def start_scenario_generation_workflow_sync(
    dataset_id: str,
    scenario_id: str,
    num_rows: int,
    row_ids: List[str],
    *,
    description: str = "",
    organization_id: str | None = None,
    sample_size_reference_data: int = 5,
    task_queue: str = "tasks_xl",
) -> str:
    """
    Synchronous version of start_scenario_generation_workflow.
    """
    workflow_id = f"scenario-gen-{dataset_id}-{scenario_id}"

    start_workflow_sync(
        ScenarioGenerationWorkflow,
        ScenarioGenerationWorkflowInput(
            dataset_id=dataset_id,
            scenario_id=scenario_id,
            num_rows=num_rows,
            description=description,
            row_ids=row_ids,
            organization_id=organization_id,
            sample_size_reference_data=sample_size_reference_data,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
    )

    return workflow_id


# =============================================================================
# Add Scenario Rows
# =============================================================================


async def start_add_scenario_rows_workflow(
    dataset_id: str,
    scenario_id: str,
    num_rows: int,
    row_ids: List[str],
    *,
    description: str = "",
    sample_size_reference_data: int = 5,
    task_queue: str = "tasks_xl",
) -> str:
    """
    Start a workflow to add rows to a scenario dataset.

    Args:
        dataset_id: UUID of the Dataset
        scenario_id: UUID of the Scenario
        num_rows: Number of rows to generate
        row_ids: List of pre-created row UUIDs
        description: Description for generation
        sample_size_reference_data: Number of reference rows to sample
        task_queue: Temporal task queue to use

    Returns:
        Workflow ID

    Example:
        workflow_id = await start_add_scenario_rows_workflow(
            dataset_id=str(dataset.id),
            scenario_id=str(scenario.id),
            num_rows=100,
            row_ids=new_row_ids,
        )
    """
    workflow_id = f"add-rows-{dataset_id}-{scenario_id}-{uuid.uuid4().hex[:8]}"

    await start_workflow_async(
        AddScenarioRowsWorkflow,
        AddScenarioRowsWorkflowInput(
            dataset_id=dataset_id,
            scenario_id=scenario_id,
            num_rows=num_rows,
            description=description,
            row_ids=row_ids,
            sample_size_reference_data=sample_size_reference_data,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
    )

    return workflow_id


def start_add_scenario_rows_workflow_sync(
    dataset_id: str,
    scenario_id: str,
    num_rows: int,
    row_ids: List[str],
    *,
    description: str = "",
    sample_size_reference_data: int = 5,
    task_queue: str = "tasks_xl",
) -> str:
    """
    Synchronous version of start_add_scenario_rows_workflow.
    """
    workflow_id = f"add-rows-{dataset_id}-{scenario_id}-{uuid.uuid4().hex[:8]}"

    start_workflow_sync(
        AddScenarioRowsWorkflow,
        AddScenarioRowsWorkflowInput(
            dataset_id=dataset_id,
            scenario_id=scenario_id,
            num_rows=num_rows,
            description=description,
            row_ids=row_ids,
            sample_size_reference_data=sample_size_reference_data,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
    )

    return workflow_id


# =============================================================================
# Add Scenario Columns
# =============================================================================


async def start_add_columns_workflow(
    dataset_id: str,
    scenario_id: str,
    columns_info: List[dict],
    column_ids: List[str],
    *,
    task_queue: str = "tasks_xl",
) -> str:
    """
    Start a workflow to add columns to a scenario dataset.

    Args:
        dataset_id: UUID of the Dataset
        scenario_id: UUID of the Scenario
        columns_info: List of column definitions (name, data_type, description)
        column_ids: List of pre-created column UUIDs
        task_queue: Temporal task queue to use

    Returns:
        Workflow ID

    Example:
        workflow_id = await start_add_columns_workflow(
            dataset_id=str(dataset.id),
            scenario_id=str(scenario.id),
            columns_info=[{"name": "new_col", "data_type": "string"}],
            column_ids=[str(col.id) for col in new_columns],
        )
    """
    workflow_id = f"add-cols-{dataset_id}-{scenario_id}"

    await start_workflow_async(
        AddScenarioColumnsWorkflow,
        AddColumnsWorkflowInput(
            dataset_id=dataset_id,
            scenario_id=scenario_id,
            columns_info=columns_info,
            column_ids=column_ids,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
    )

    return workflow_id


def start_add_columns_workflow_sync(
    dataset_id: str,
    scenario_id: str,
    columns_info: List[dict],
    column_ids: List[str],
    *,
    task_queue: str = "tasks_xl",
) -> str:
    """
    Synchronous version of start_add_columns_workflow.
    """
    workflow_id = f"add-cols-{dataset_id}-{scenario_id}"

    start_workflow_sync(
        AddScenarioColumnsWorkflow,
        AddColumnsWorkflowInput(
            dataset_id=dataset_id,
            scenario_id=scenario_id,
            columns_info=columns_info,
            column_ids=column_ids,
            task_queue=task_queue,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
    )

    return workflow_id


# =============================================================================
# Scenario Creation
# =============================================================================


async def start_create_dataset_scenario_workflow(
    user_id: str,
    validated_data: Dict[str, Any],
    scenario_id: str,
    *,
    task_queue: str = "tasks_xl",
) -> str:
    """
    Start a workflow to create a dataset-based scenario.

    Args:
        user_id: ID of the user creating the scenario
        validated_data: Validated data from the serializer
        scenario_id: ID of the scenario to update
        task_queue: Temporal task queue to use

    Returns:
        Workflow ID
    """
    workflow_id = f"create-dataset-scenario-{scenario_id}"

    await start_workflow_async(
        CreateDatasetScenarioWorkflow,
        CreateDatasetScenarioWorkflowInput(
            user_id=user_id,
            validated_data=validated_data,
            scenario_id=scenario_id,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,
    )

    return workflow_id


def start_create_dataset_scenario_workflow_sync(
    user_id: str,
    validated_data: Dict[str, Any],
    scenario_id: str,
    *,
    task_queue: str = "tasks_xl",
) -> str:
    """Synchronous version of start_create_dataset_scenario_workflow."""
    workflow_id = f"create-dataset-scenario-{scenario_id}"

    start_workflow_sync(
        CreateDatasetScenarioWorkflow,
        CreateDatasetScenarioWorkflowInput(
            user_id=user_id,
            validated_data=validated_data,
            scenario_id=scenario_id,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,
    )

    return workflow_id


async def start_create_script_scenario_workflow(
    validated_data: Dict[str, Any],
    scenario_id: str,
    *,
    task_queue: str = "tasks_xl",
) -> str:
    """
    Start a workflow to create a script-based scenario.

    Args:
        validated_data: Validated data from the serializer
        scenario_id: ID of the scenario to update
        task_queue: Temporal task queue to use

    Returns:
        Workflow ID
    """
    workflow_id = f"create-script-scenario-{scenario_id}"

    await start_workflow_async(
        CreateScriptScenarioWorkflow,
        CreateScriptScenarioWorkflowInput(
            validated_data=validated_data,
            scenario_id=scenario_id,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,
    )

    return workflow_id


def start_create_script_scenario_workflow_sync(
    validated_data: Dict[str, Any],
    scenario_id: str,
    *,
    task_queue: str = "tasks_xl",
) -> str:
    """Synchronous version of start_create_script_scenario_workflow."""
    workflow_id = f"create-script-scenario-{scenario_id}"

    start_workflow_sync(
        CreateScriptScenarioWorkflow,
        CreateScriptScenarioWorkflowInput(
            validated_data=validated_data,
            scenario_id=scenario_id,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,
    )

    return workflow_id


async def start_create_graph_scenario_workflow(
    validated_data: Dict[str, Any],
    scenario_id: str,
    *,
    task_queue: str = "tasks_xl",
) -> str:
    """
    Start a workflow to create a graph-based scenario.

    Args:
        validated_data: Validated data from the serializer
        scenario_id: ID of the scenario to update
        task_queue: Temporal task queue to use

    Returns:
        Workflow ID
    """
    workflow_id = f"create-graph-scenario-{scenario_id}"

    await start_workflow_async(
        CreateGraphScenarioWorkflow,
        CreateGraphScenarioWorkflowInput(
            validated_data=validated_data,
            scenario_id=scenario_id,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,
    )

    return workflow_id


def start_create_graph_scenario_workflow_sync(
    validated_data: Dict[str, Any],
    scenario_id: str,
    *,
    task_queue: str = "tasks_xl",
) -> str:
    """Synchronous version of start_create_graph_scenario_workflow."""
    workflow_id = f"create-graph-scenario-{scenario_id}"

    start_workflow_sync(
        CreateGraphScenarioWorkflow,
        CreateGraphScenarioWorkflowInput(
            validated_data=validated_data,
            scenario_id=scenario_id,
        ),
        workflow_id=workflow_id,
        task_queue=task_queue,
        cancel_existing=False,
    )

    return workflow_id


__all__ = [
    # Scenario Generation
    "start_scenario_generation_workflow",
    "start_scenario_generation_workflow_sync",
    # Add Rows
    "start_add_scenario_rows_workflow",
    "start_add_scenario_rows_workflow_sync",
    # Add Columns
    "start_add_columns_workflow",
    "start_add_columns_workflow_sync",
    # Scenario Creation
    "start_create_dataset_scenario_workflow",
    "start_create_dataset_scenario_workflow_sync",
    "start_create_script_scenario_workflow",
    "start_create_script_scenario_workflow_sync",
    "start_create_graph_scenario_workflow",
    "start_create_graph_scenario_workflow_sync",
]
