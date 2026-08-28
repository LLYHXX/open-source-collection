"""
Data classes for simulate workflows and activities.

This file is separate from activities.py to avoid Django imports
when Temporal validates workflows in its sandbox.

IMPORTANT: Do NOT import Django models or any Django-dependent code here.

Note: Test execution workflows have been removed - using Celery tasks instead.
Only scenario-related types remain.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# =============================================================================
# Scenario Generation Workflow Types
# =============================================================================


@dataclass
class ScenarioGenerationWorkflowInput:
    """Input for ScenarioGenerationWorkflow."""

    dataset_id: str
    scenario_id: str
    num_rows: int
    description: str
    row_ids: List[str]
    organization_id: Optional[str] = None
    sample_size_reference_data: int = 5
    task_queue: str = "tasks_xl"


@dataclass
class ScenarioGenerationWorkflowOutput:
    """Output from ScenarioGenerationWorkflow."""

    dataset_id: str
    scenario_id: str
    status: str  # "COMPLETED", "FAILED"
    rows_generated: int = 0
    error: Optional[str] = None


@dataclass
class SetupGenerationInput:
    """Input for setup_generation_activity."""

    dataset_id: str
    scenario_id: str
    num_rows: int


@dataclass
class SetupGenerationOutput:
    """Output from setup_generation_activity."""

    dataset_id: str
    scenario_id: str
    status: str  # "READY" or "FAILED"
    generation_payload: Optional[Dict[str, Any]] = None
    branch_metadata: Optional[List[Dict[str, Any]]] = None
    column_names: Optional[List[str]] = None
    error: Optional[str] = None


@dataclass
class GenerateSyntheticDataInput:
    """Input for generate_synthetic_data_activity."""

    generation_payload: Dict[str, Any]
    branch_metadata: List[Dict[str, Any]]
    organization_id: Optional[str] = None


@dataclass
class GenerateSyntheticDataOutput:
    """Output from generate_synthetic_data_activity."""

    status: str  # "COMPLETED" or "FAILED"
    # Data is a list of dicts (rows), each with column name -> value
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@dataclass
class ValidatePersonasInput:
    """Input for validate_personas_activity."""

    personas: List[Dict[str, Any]]
    required_fields: List[str]


@dataclass
class ValidatePersonasOutput:
    """Output from validate_personas_activity."""

    status: str  # "COMPLETED" or "FAILED"
    validated_personas: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@dataclass
class PersistCellsInput:
    """Input for persist_cells_activity."""

    dataset_id: str
    row_ids: List[str]
    column_names: List[str]
    data: List[Dict[str, Any]]  # List of row dicts


@dataclass
class PersistCellsOutput:
    """Output from persist_cells_activity."""

    status: str  # "COMPLETED" or "FAILED"
    cells_created: int = 0
    cells_updated: int = 0
    error: Optional[str] = None


@dataclass
class GenerateScenarioRowsInput:
    """Input for generate_scenario_rows_activity."""

    dataset_id: str
    scenario_id: str
    num_rows: int
    description: str
    row_ids: List[str]
    sample_size_reference_data: int = 5


# =============================================================================
# Add Scenario Columns Workflow Types
# =============================================================================


@dataclass
class AddColumnsWorkflowInput:
    """Input for AddScenarioColumnsWorkflow."""

    dataset_id: str
    scenario_id: str
    columns_info: List[Dict[str, Any]]  # List of column definitions
    column_ids: List[str]  # Pre-created column IDs
    task_queue: str = "tasks_xl"


@dataclass
class AddColumnsWorkflowOutput:
    """Output from AddScenarioColumnsWorkflow."""

    dataset_id: str
    status: str  # "COMPLETED" or "FAILED"
    columns_added: int = 0
    rows_updated: int = 0
    error: Optional[str] = None


@dataclass
class SetupColumnsInput:
    """Input for setup_columns_activity."""

    dataset_id: str
    scenario_id: str
    columns_info: List[Dict[str, Any]]


@dataclass
class SetupColumnsOutput:
    """Output from setup_columns_activity."""

    status: str  # "READY" or "FAILED"
    generation_payload: Optional[Dict[str, Any]] = None
    row_ids: Optional[List[str]] = None
    error: Optional[str] = None


@dataclass
class GenerateColumnDataInput:
    """Input for generate_column_data_activity."""

    generation_payload: Dict[str, Any]
    organization_id: Optional[str] = None


@dataclass
class GenerateColumnDataOutput:
    """Output from generate_column_data_activity."""

    status: str  # "COMPLETED" or "FAILED"
    # Data is a dict mapping row_id -> column_name -> value
    data: Optional[Dict[str, Dict[str, Any]]] = None
    error: Optional[str] = None


@dataclass
class PersistColumnCellsInput:
    """Input for persist_column_cells_activity."""

    dataset_id: str
    column_ids: List[str]
    data: Dict[str, Dict[str, Any]]  # row_id -> column_name -> value


@dataclass
class PersistColumnCellsOutput:
    """Output from persist_column_cells_activity."""

    status: str  # "COMPLETED" or "FAILED"
    cells_updated: int = 0
    error: Optional[str] = None


@dataclass
class AddScenarioColumnsInput:
    """Input for add_scenario_columns_activity (complete single-step activity)."""

    dataset_id: str
    scenario_id: str
    columns_info: List[Dict[str, Any]]  # List of column definitions
    column_ids: List[str]  # Pre-created column IDs


# =============================================================================
# Graph Scenario Sub-Activity Types (v2 - multi-activity workflow)
# =============================================================================


@dataclass
class SetupGraphScenarioInput:
    """Input for setup_graph_scenario_activity."""

    scenario_id: str
    validated_data: Dict[str, Any]


@dataclass
class SetupGraphScenarioOutput:
    """Output from setup_graph_scenario_activity."""

    scenario_id: str
    status: str  # "COMPLETED" or "FAILED"
    graph_id: Optional[str] = None
    agent_definition_data: Optional[Dict[str, Any]] = None  # Serialized agent def
    no_of_rows: int = 20
    custom_columns: Optional[List[Dict[str, Any]]] = None
    property_list: Optional[List[Dict[str, Any]]] = None
    transcripts: Optional[Any] = None  # Can be Dict or List depending on input
    custom_instruction: Optional[str] = None
    mode: str = "voice"
    error: Optional[str] = None
    # v3 additions (optional — v2 ignores these)
    agent_context: Optional[Dict[str, Any]] = None
    configuration_snapshot: Optional[Dict[str, Any]] = None


@dataclass
class ExtractIntentsInput:
    """Input for extract_intents_activity."""

    scenario_id: str
    graph_id: str
    agent_definition_data: Dict[str, Any]
    transcripts: Optional[Any] = None  # Can be Dict or List depending on input
    no_of_rows: int = 20


@dataclass
class ExtractIntentsOutput:
    """Output from extract_intents_activity."""

    status: str  # "COMPLETED" or "FAILED"
    intent_dict: Optional[Dict[str, str]] = None
    error: Optional[str] = None


@dataclass
class ProcessBranchesInput:
    """Input for process_branches_activity."""

    graph_id: str
    agent_definition_data: Dict[str, Any]
    custom_instruction: Optional[str] = None
    no_of_rows: int = 20
    mode: str = "voice"


@dataclass
class ProcessBranchesOutput:
    """Output from process_branches_activity."""

    status: str  # "COMPLETED" or "FAILED"
    branches_metadata: Optional[List[Dict[str, Any]]] = None
    branch_metadata_lookup: Optional[Dict[str, Dict[str, Any]]] = None
    error: Optional[str] = None


@dataclass
class GenerateCasesForIntentInput:
    """Input for generate_cases_for_intent_activity."""

    intent_id: str
    intent_value: str
    branches_metadata: List[Dict[str, Any]]
    agent_definition_data: Dict[str, Any]
    batch_size: int
    property_list: Optional[List[Dict[str, Any]]] = None
    custom_columns: Optional[List[Dict[str, Any]]] = None
    mode: str = "voice"
    graph_id: Optional[str] = None
    # v3 additions (optional — v2 uses agent_definition_data instead)
    agent_context: Optional[Dict[str, Any]] = None
    custom_instruction: Optional[str] = None
    configuration_snapshot: Optional[Dict[str, Any]] = None
    # v3 claim-check: load branches_metadata from Redis instead of inline
    selected_metadata_redis_key: Optional[str] = None
    # Branch subsetting for diversity: when set, the activity slices the
    # loaded branches to branches[start_index : start_index + max_branches]
    branch_start_index: int = 0
    max_branches: int = 0  # 0 = use all branches


@dataclass
class GenerateCasesForIntentOutput:
    """Output from generate_cases_for_intent_activity."""

    status: str  # "COMPLETED" or "FAILED"
    intent_id: str = ""
    cases: Optional[List[Dict[str, Any]]] = None
    categorized_branches: Optional[Dict[str, str]] = None  # branch_name -> category
    error: Optional[str] = None
    # v3 claim-check: Redis key for cases (when too large for Temporal payload)
    cases_redis_key: Optional[str] = None


@dataclass
class CategorizeAndValidateInput:
    """Input for categorize_and_validate_activity."""

    cases: List[Dict[str, Any]]
    branch_metadata_lookup: Dict[str, Dict[str, Any]]
    mode: str = "voice"
    custom_columns: Optional[List[Dict[str, Any]]] = None


@dataclass
class CategorizeAndValidateOutput:
    """Output from categorize_and_validate_activity."""

    status: str  # "COMPLETED" or "FAILED"
    validated_cases: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@dataclass
class CreateScenarioDatasetInput:
    """Input for create_scenario_dataset_activity."""

    scenario_id: str
    cases: List[Dict[str, Any]]
    name: str
    description: str
    custom_columns: Optional[List[Dict[str, Any]]] = None
    agent_definition_data: Optional[Dict[str, Any]] = None
    # v3 addition (optional — v2 uses agent_definition_data instead)
    agent_context: Optional[Dict[str, Any]] = None
    # v3 claim-check: Redis key for cases (alternative to inline cases)
    cases_redis_key: Optional[str] = None


@dataclass
class CreateScenarioDatasetOutput:
    """Output from create_scenario_dataset_activity."""

    status: str  # "COMPLETED" or "FAILED"
    dataset_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class FinalizeGraphScenarioInput:
    """Input for finalize_graph_scenario_activity."""

    scenario_id: str
    dataset_id: str
    persona_ids: Optional[List[str]] = None
    # v3 claim-check: Redis keys to clean up on finalize
    redis_keys_to_cleanup: Optional[List[str]] = None


@dataclass
class FinalizeGraphScenarioOutput:
    """Output from finalize_graph_scenario_activity."""

    scenario_id: str
    dataset_id: Optional[str] = None
    status: str = "COMPLETED"  # "COMPLETED" or "FAILED"
    error: Optional[str] = None


# =============================================================================
# Graph Scenario Sub-Activity Types (v3 - chunky pipeline)
# =============================================================================


@dataclass
class PrepareScenarioInput:
    """Input for prepare_scenario_activity.

    Merges old steps 1-5: setup + extract_intents + get_branches +
    process_branch_metadata + select_branches into one activity.
    """

    scenario_id: str
    validated_data: Dict[str, Any]


@dataclass
class PrepareScenarioOutput:
    """Output from prepare_scenario_activity."""

    scenario_id: str
    status: str  # "COMPLETED" or "FAILED"
    graph_id: Optional[str] = None
    agent_context: Optional[Dict[str, Any]] = None
    agent_definition_data: Optional[Dict[str, Any]] = None
    configuration_snapshot: Optional[Dict[str, Any]] = None
    no_of_rows: int = 20
    custom_columns: Optional[List[Dict[str, Any]]] = None
    property_list: Optional[List[Dict[str, Any]]] = None
    custom_instruction: Optional[str] = None
    mode: str = "voice"
    # Merged outputs from intent extraction + branch processing + selection
    intent_dict: Optional[Dict[str, str]] = None
    selected_metadata: Optional[List[Dict[str, Any]]] = None
    branch_metadata_lookup: Optional[Dict[str, Dict[str, Any]]] = None
    error: Optional[str] = None
    # v3 claim-check: Redis keys for large data (replaces inline metadata)
    selected_metadata_redis_key: Optional[str] = None
    branch_metadata_lookup_redis_key: Optional[str] = None
    # Total number of selected branches (for round-robin distribution)
    num_branches: int = 0


@dataclass
class ValidateAndEnrichCasesInput:
    """Input for validate_and_enrich_cases_activity."""

    cases: List[Dict[str, Any]]
    categorized_branches: Dict[str, str]  # branch_name -> category
    branch_metadata_lookup: Dict[str, Dict[str, Any]]
    mode: str = "voice"
    custom_columns: Optional[List[Dict[str, Any]]] = None
    # v3 claim-check: Redis keys for large data (replaces inline cases/metadata)
    case_redis_keys: Optional[List[str]] = None
    branch_metadata_lookup_redis_key: Optional[str] = None


@dataclass
class ValidateAndEnrichCasesOutput:
    """Output from validate_and_enrich_cases_activity."""

    status: str  # "COMPLETED" or "FAILED"
    validated_cases: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    # v3 claim-check: Redis key for validated cases
    validated_cases_redis_key: Optional[str] = None


# Legacy v3 types — kept for backward compatibility with in-flight workflows
@dataclass
class GetBranchesInput:
    """Input for get_branches_activity (legacy v3)."""

    graph_id: str
    agent_context: Dict[str, Any]


@dataclass
class GetBranchesOutput:
    """Output from get_branches_activity (legacy v3)."""

    status: str
    branches: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


@dataclass
class ProcessSingleBranchInput:
    """Input for process_single_branch_activity (legacy v3)."""

    branch: Dict[str, Any]
    graph_id: str
    agent_context: Dict[str, Any]
    mode: str = "voice"


@dataclass
class ProcessSingleBranchOutput:
    """Output from process_single_branch_activity (legacy v3)."""

    status: str
    branch_metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class SelectBranchesInput:
    """Input for select_branches_activity (legacy v3)."""

    branches_metadata: List[Dict[str, Any]]
    needed: int
    custom_instruction: Optional[str] = None


@dataclass
class SelectBranchesOutput:
    """Output from select_branches_activity (legacy v3)."""

    status: str
    selected_metadata: Optional[List[Dict[str, Any]]] = None
    branch_metadata_lookup: Optional[Dict[str, Dict[str, Any]]] = None
    error: Optional[str] = None


@dataclass
class CategorizeBranchInput:
    """Input for categorize_branch_activity (legacy v3)."""

    branch_name: str
    situations: List[str]


@dataclass
class CategorizeBranchOutput:
    """Output from categorize_branch_activity (legacy v3)."""

    status: str
    branch_name: str = ""
    category: str = ""
    error: Optional[str] = None


# =============================================================================
# Scenario Creation Workflow Types
# =============================================================================


@dataclass
class CreateDatasetScenarioWorkflowInput:
    """Input for creating a dataset-based scenario."""

    # Use str to support UUID primary keys
    user_id: str
    validated_data: Dict[str, Any]  # Serializer validated data
    scenario_id: str


@dataclass
class CreateDatasetScenarioWorkflowOutput:
    """Output from dataset scenario creation."""

    scenario_id: str
    dataset_id: Optional[str] = None
    status: str = "COMPLETED"  # "COMPLETED" or "FAILED"
    error: Optional[str] = None


@dataclass
class CreateScriptScenarioWorkflowInput:
    """Input for creating a script-based scenario."""

    validated_data: Dict[str, Any]  # Serializer validated data
    scenario_id: str


@dataclass
class CreateScriptScenarioWorkflowOutput:
    """Output from script scenario creation."""

    scenario_id: str
    dataset_id: Optional[str] = None
    status: str = "COMPLETED"  # "COMPLETED" or "FAILED"
    error: Optional[str] = None


@dataclass
class CreateGraphScenarioWorkflowInput:
    """Input for creating a graph-based scenario."""

    validated_data: Dict[str, Any]  # Serializer validated data
    scenario_id: str


@dataclass
class CreateGraphScenarioWorkflowOutput:
    """Output from graph scenario creation."""

    scenario_id: str
    dataset_id: Optional[str] = None
    status: str = "COMPLETED"  # "COMPLETED" or "FAILED"
    error: Optional[str] = None


# =============================================================================
# Add Scenario Rows Workflow Types
# =============================================================================


@dataclass
class AddScenarioRowsWorkflowInput:
    """Input for AddScenarioRowsWorkflow."""

    dataset_id: str
    scenario_id: str
    num_rows: int
    description: str
    row_ids: List[str]
    sample_size_reference_data: int = 5
    task_queue: str = "tasks_xl"


@dataclass
class AddScenarioRowsWorkflowOutput:
    """Output from AddScenarioRowsWorkflow."""

    dataset_id: str
    scenario_id: str
    status: str  # "COMPLETED", "FAILED"
    rows_generated: int = 0
    error: Optional[str] = None


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Scenario Generation
    "ScenarioGenerationWorkflowInput",
    "ScenarioGenerationWorkflowOutput",
    "SetupGenerationInput",
    "SetupGenerationOutput",
    "GenerateSyntheticDataInput",
    "GenerateSyntheticDataOutput",
    "ValidatePersonasInput",
    "ValidatePersonasOutput",
    "PersistCellsInput",
    "PersistCellsOutput",
    "GenerateScenarioRowsInput",
    # Add Scenario Columns
    "AddColumnsWorkflowInput",
    "AddColumnsWorkflowOutput",
    "SetupColumnsInput",
    "SetupColumnsOutput",
    "GenerateColumnDataInput",
    "GenerateColumnDataOutput",
    "PersistColumnCellsInput",
    "PersistColumnCellsOutput",
    # Add Scenario Rows
    "AddScenarioRowsWorkflowInput",
    "AddScenarioRowsWorkflowOutput",
    # Graph Scenario Sub-Activity Types (v2)
    "SetupGraphScenarioInput",
    "SetupGraphScenarioOutput",
    "ExtractIntentsInput",
    "ExtractIntentsOutput",
    "ProcessBranchesInput",
    "ProcessBranchesOutput",
    "GenerateCasesForIntentInput",
    "GenerateCasesForIntentOutput",
    "CategorizeAndValidateInput",
    "CategorizeAndValidateOutput",
    "CreateScenarioDatasetInput",
    "CreateScenarioDatasetOutput",
    "FinalizeGraphScenarioInput",
    "FinalizeGraphScenarioOutput",
    # Graph Scenario Sub-Activity Types (v3 - chunky pipeline)
    "PrepareScenarioInput",
    "PrepareScenarioOutput",
    "ValidateAndEnrichCasesInput",
    "ValidateAndEnrichCasesOutput",
    # Legacy v3 types (kept for backward compat)
    "GetBranchesInput",
    "GetBranchesOutput",
    "ProcessSingleBranchInput",
    "ProcessSingleBranchOutput",
    "SelectBranchesInput",
    "SelectBranchesOutput",
    "CategorizeBranchInput",
    "CategorizeBranchOutput",
    # Scenario Creation Workflows
    "CreateDatasetScenarioWorkflowInput",
    "CreateDatasetScenarioWorkflowOutput",
    "CreateScriptScenarioWorkflowInput",
    "CreateScriptScenarioWorkflowOutput",
    "CreateGraphScenarioWorkflowInput",
    "CreateGraphScenarioWorkflowOutput",
]
