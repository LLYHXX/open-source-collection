from typing import Any
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator, model_validator

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_datetime,
    key_value_block,
    section,
)
from ai_tools.registry import register_tool

VALID_SCENARIO_TYPES = ("graph", "script", "dataset")
VALID_SOURCE_TYPES = ("agent_definition", "prompt")


class CustomColumnInput(PydanticBaseModel):
    name: str = Field(max_length=50, description="Name of the custom column")
    data_type: str = Field(
        description=(
            "Data type of the column. Valid types: text, boolean, integer, "
            "float, json, array, image, images, datetime, audio, document, "
            "others, persona."
        )
    )
    description: str = Field(
        max_length=200,
        description="Description of the custom column explaining its purpose",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Column name cannot be empty or just whitespace.")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Column description cannot be empty or just whitespace.")
        return v.strip()

    @field_validator("data_type")
    @classmethod
    def validate_data_type(cls, v: str) -> str:
        from model_hub.models.choices import DataTypeChoices

        valid_types = [choice.value for choice in DataTypeChoices]
        if v not in valid_types:
            raise ValueError(
                f"Invalid data_type '{v}'. Valid types are: {', '.join(valid_types)}"
            )
        return v


class CreateScenarioInput(PydanticBaseModel):
    name: str = Field(max_length=255, description="Name of the scenario")
    description: str | None = Field(
        default=None, description="Description of the scenario"
    )
    scenario_type: str = Field(
        default="graph",
        description=(
            "Type of scenario: graph (default, generates conversation flow with branches), "
            "script (text-based), or dataset (data-driven from existing dataset)."
        ),
    )
    agent_id: UUID | None = Field(
        default=None,
        description=(
            "The UUID of the agent definition to associate with. "
            "Required when source_type is agent_definition."
        ),
    )
    source: str | None = Field(
        default=None, description="Source content or reference for the scenario"
    )
    source_type: str | None = Field(
        default="agent_definition",
        description="Source type: agent_definition or prompt",
    )
    dataset_id: UUID | None = Field(
        default=None,
        description=(
            "UUID of an existing dataset to use. "
            "Required for dataset-type scenarios."
        ),
    )
    no_of_rows: int = Field(
        default=20,
        ge=10,
        le=100,
        description=(
            "Number of situations (rows) to generate in the scenario (10-100). "
            "Applies to both graph and dataset scenarios. Default: 20."
        ),
    )
    agent_version_id: UUID | None = Field(
        default=None,
        description=(
            "UUID of a specific agent version to use for scenario generation. "
            "Stored in scenario metadata as agent_definition_version_id. "
            "If not provided, the active/latest version is used."
        ),
    )
    custom_instruction: str | None = Field(
        default=None,
        description=(
            "Custom instruction to guide scenario generation. "
            "For example: 'Focus on edge cases around payment disputes'."
        ),
    )
    personas: list[UUID] | None = Field(
        default=None,
        description="List of persona UUIDs to use in the scenario generation.",
    )
    add_persona_automatically: bool = Field(
        default=False,
        description="Whether to automatically add personas to the scenario.",
    )
    custom_columns: list[CustomColumnInput] | None = Field(
        default=None,
        description="Custom columns to add to the scenario dataset (max 10 columns).",
    )
    generate_graph: bool = Field(
        default=True,
        description=(
            "Whether to auto-generate the conversation graph. "
            "Defaults to True for graph-type scenarios. "
            "Set to False if providing pre-built graph data."
        ),
    )
    graph: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Pre-built graph JSON data. Use this instead of generate_graph=True "
            "to provide a custom conversation flow."
        ),
    )
    script_url: str | None = Field(
        default=None,
        description="URL to a script file. Required for script-type scenarios.",
    )
    # Prompt source type fields
    prompt_template_id: UUID | None = Field(
        default=None,
        description="Prompt template ID. Required when source_type is prompt.",
    )
    prompt_version_id: UUID | None = Field(
        default=None,
        description="Prompt version ID. Required when source_type is prompt.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty or just whitespace.")
        return v.strip()

    @field_validator("scenario_type")
    @classmethod
    def validate_scenario_type(cls, v: str) -> str:
        v = v.lower()
        if v not in VALID_SCENARIO_TYPES:
            raise ValueError(
                f"Invalid scenario_type. Must be one of: {', '.join(VALID_SCENARIO_TYPES)}"
            )
        return v

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_SOURCE_TYPES:
            raise ValueError(
                f"Invalid source_type. Must be one of: {', '.join(VALID_SOURCE_TYPES)}"
            )
        return v

    @field_validator("custom_columns")
    @classmethod
    def validate_custom_columns_length(
        cls,
        v: list[CustomColumnInput] | None,
    ) -> list[CustomColumnInput] | None:
        if v is not None and len(v) > 10:
            raise ValueError("Maximum 10 custom columns are allowed.")
        return v

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "CreateScenarioInput":
        source_type = self.source_type or "agent_definition"
        scenario_type = self.scenario_type

        # For dataset kind, dataset_id is required
        if scenario_type == "dataset" and not self.dataset_id:
            raise ValueError("dataset_id is required for dataset scenario type.")

        # For script kind, script_url is required
        if scenario_type == "script" and not self.script_url:
            raise ValueError("script_url is required for script scenario type.")

        # For graph kind, either generate_graph=True with agent_id or graph data is required
        if scenario_type == "graph":
            if not self.generate_graph and not self.graph:
                raise ValueError(
                    "Either generate_graph=True with agent_id or graph data "
                    "is required for graph scenario type."
                )

        # Validate agent_definition source type requirements
        if source_type == "agent_definition" and not self.agent_id:
            raise ValueError(
                "agent_id is required when source_type is agent_definition."
            )

        # Validate prompt source type requirements
        if source_type == "prompt":
            if not self.prompt_template_id:
                raise ValueError(
                    "prompt_template_id is required for prompt source type."
                )
            if not self.prompt_version_id:
                raise ValueError(
                    "prompt_version_id is required for prompt source type."
                )

        return self


@register_tool
class CreateScenarioTool(BaseTool):
    name = "create_scenario"
    description = (
        "Creates a new test scenario for agent testing. "
        "By default creates a graph-based scenario that auto-generates conversation "
        "flows with branches, personas, situations, and outcomes. "
        "Use no_of_rows to control how many situations are generated (default 20). "
        "Types: graph (default, visual flow with branches), script (text-based), "
        "dataset (data-driven from existing dataset). "
        "Supports both agent_definition and prompt source types."
    )
    category = "simulation"
    input_model = CreateScenarioInput

    def execute(self, params: CreateScenarioInput, context: ToolContext) -> ToolResult:
        source_type = params.source_type or "agent_definition"

        # Validate custom column names for duplicates (script/graph scenarios)
        if params.scenario_type in ("script", "graph") and params.custom_columns:
            column_names = [col.name for col in params.custom_columns]
            duplicate_names = [
                name for name in column_names if column_names.count(name) > 1
            ]
            if duplicate_names:
                return ToolResult.error(
                    f"Duplicate column name(s) in custom columns: {', '.join(set(duplicate_names))}",
                    error_code="VALIDATION_ERROR",
                )

        # Validate persona column data type for dataset scenarios
        if params.scenario_type == "dataset" and params.dataset_id:
            from model_hub.models.choices import DataTypeChoices, SourceChoices
            from model_hub.models.develop_dataset import Column, Dataset

            try:
                source_dataset = Dataset.objects.get(
                    id=params.dataset_id,
                    deleted=False,
                    organization=context.organization,
                )
            except Dataset.DoesNotExist:
                return ToolResult.not_found("Dataset", str(params.dataset_id))

            existing_persona_column = Column.objects.filter(
                dataset=source_dataset, name="persona", deleted=False
            ).first()
            if (
                existing_persona_column
                and existing_persona_column.data_type != DataTypeChoices.PERSONA.value
            ):
                return ToolResult.error(
                    f"Invalid data type for 'persona' column. Expected "
                    f"'{DataTypeChoices.PERSONA.value}' but found "
                    f"'{existing_persona_column.data_type}'.",
                    error_code="VALIDATION_ERROR",
                )

            # Check for duplicate column names in source dataset
            source_columns = Column.objects.filter(
                dataset=source_dataset, deleted=False
            ).exclude(
                source__in=[
                    SourceChoices.EXPERIMENT.value,
                    SourceChoices.EXPERIMENT_EVALUATION.value,
                    SourceChoices.EXPERIMENT_EVALUATION_TAGS.value,
                ]
            )
            col_names = [col.name for col in source_columns]
            dup_names = [name for name in col_names if col_names.count(name) > 1]
            if dup_names:
                return ToolResult.error(
                    f"Source dataset contains duplicate column name(s): {', '.join(set(dup_names))}",
                    error_code="VALIDATION_ERROR",
                )

        # Validate prompt source type references
        if source_type == "prompt":
            from model_hub.models.run_prompt import PromptTemplate, PromptVersion

            try:
                pt_filters = {
                    "id": params.prompt_template_id,
                    "deleted": False,
                    "organization": context.organization,
                }
                if context.workspace:
                    pt_filters["workspace"] = context.workspace
                PromptTemplate.objects.get(**pt_filters)
            except PromptTemplate.DoesNotExist:
                return ToolResult.not_found(
                    "Prompt template", str(params.prompt_template_id)
                )

            try:
                pv_filters = {
                    "id": params.prompt_version_id,
                    "deleted": False,
                    "original_template__organization": context.organization,
                }
                if context.workspace:
                    pv_filters["original_template__workspace"] = context.workspace
                prompt_version = PromptVersion.objects.get(**pv_filters)
                # Validate version belongs to template
                if prompt_version.original_template_id != params.prompt_template_id:
                    return ToolResult.error(
                        "Prompt version does not belong to the specified prompt template.",
                        error_code="VALIDATION_ERROR",
                    )
            except PromptVersion.DoesNotExist:
                return ToolResult.not_found(
                    "Prompt version", str(params.prompt_version_id)
                )

        from simulate.services.scenario_service import ServiceError, create_scenario

        # Prepare custom_columns as list of dicts for the service
        custom_columns_data = None
        if params.custom_columns:
            custom_columns_data = [
                {
                    "name": col.name,
                    "data_type": col.data_type,
                    "description": col.description,
                }
                for col in params.custom_columns
            ]

        result = create_scenario(
            name=params.name,
            description=params.description or "",
            scenario_type=params.scenario_type,
            source_type=source_type,
            agent_definition_id=params.agent_id,
            agent_version_id=params.agent_version_id,
            dataset_id=params.dataset_id,
            organization=context.organization,
            workspace=context.workspace,
            user=context.user,
            source=params.source or "",
            no_of_rows=params.no_of_rows,
            custom_instruction=params.custom_instruction or "",
            personas=params.personas,
            add_persona_automatically=params.add_persona_automatically,
            custom_columns=custom_columns_data,
            generate_graph=params.generate_graph,
            graph=params.graph,
            script_url=params.script_url,
            prompt_template_id=params.prompt_template_id,
            prompt_version_id=params.prompt_version_id,
        )

        if isinstance(result, ServiceError):
            return ToolResult.error(result.message, error_code=result.code)

        scenario = result["scenario"]
        status_label = scenario.status
        if result["workflow_started"]:
            status_label = "processing (workflow started)"

        info = key_value_block(
            [
                ("ID", f"`{scenario.id}`"),
                ("Name", scenario.name),
                ("Type", scenario.scenario_type),
                (
                    "Agent",
                    f"`{params.agent_id}`" if params.agent_id else "—",
                ),
                ("Source Type", scenario.source_type),
                (
                    "Dataset",
                    f"`{params.dataset_id}`" if params.dataset_id else "auto-generated",
                ),
                ("Status", status_label),
                ("Created", format_datetime(scenario.created_at)),
            ]
        )

        content = section("Scenario Created", info)
        if result["workflow_started"]:
            content += "\n\n_Scenario is being generated asynchronously. Use `get_scenario` to check status._"

        return ToolResult(
            content=content,
            data={
                "id": result["id"],
                "name": result["name"],
                "type": result["type"],
                "agent_id": result["agent_id"],
                "status": result["status"],
            },
        )
