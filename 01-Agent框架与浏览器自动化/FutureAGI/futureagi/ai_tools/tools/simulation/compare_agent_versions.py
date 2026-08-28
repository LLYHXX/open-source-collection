from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    format_number,
    format_status,
    markdown_table,
    section,
)
from ai_tools.registry import register_tool


class CompareAgentVersionsInput(PydanticBaseModel):
    agent_id: UUID = Field(description="The UUID of the agent definition")
    version_id_a: UUID = Field(description="The UUID of the first version to compare")
    version_id_b: UUID = Field(description="The UUID of the second version to compare")


@register_tool
class CompareAgentVersionsTool(BaseTool):
    name = "compare_agent_versions"
    description = (
        "Compares two agent versions side by side, showing differences in "
        "metrics (score, pass rate, test count) and configuration."
    )
    category = "simulation"
    input_model = CompareAgentVersionsInput

    def execute(
        self, params: CompareAgentVersionsInput, context: ToolContext
    ) -> ToolResult:

        from simulate.models.agent_definition import AgentDefinition
        from simulate.models.agent_version import AgentVersion

        try:
            agent = AgentDefinition.objects.get(
                id=params.agent_id, organization=context.organization
            )
        except AgentDefinition.DoesNotExist:
            return ToolResult.not_found("Agent", str(params.agent_id))

        try:
            version_a = AgentVersion.objects.get(
                id=params.version_id_a, agent_definition=agent
            )
        except AgentVersion.DoesNotExist:
            return ToolResult.not_found("Agent Version A", str(params.version_id_a))

        try:
            version_b = AgentVersion.objects.get(
                id=params.version_id_b, agent_definition=agent
            )
        except AgentVersion.DoesNotExist:
            return ToolResult.not_found("Agent Version B", str(params.version_id_b))

        # Metrics comparison table
        rows = [
            [
                "Version Name",
                version_a.version_name or f"v{version_a.version_number}",
                version_b.version_name or f"v{version_b.version_number}",
            ],
            [
                "Status",
                format_status(version_a.status),
                format_status(version_b.status),
            ],
            [
                "Score",
                format_number(version_a.score) if version_a.score is not None else "—",
                format_number(version_b.score) if version_b.score is not None else "—",
            ],
            [
                "Test Count",
                str(version_a.test_count),
                str(version_b.test_count),
            ],
            [
                "Pass Rate",
                f"{version_a.pass_rate}%" if version_a.pass_rate is not None else "—",
                f"{version_b.pass_rate}%" if version_b.pass_rate is not None else "—",
            ],
        ]

        table = markdown_table(["Metric", "Version A", "Version B"], rows)

        content = section(
            f"Version Comparison: {agent.agent_name}",
            f"Comparing `{str(version_a.id)}` vs `{str(version_b.id)}`\n\n{table}",
        )

        # Configuration diff
        snap_a = version_a.configuration_snapshot or {}
        snap_b = version_b.configuration_snapshot or {}
        all_keys = sorted(set(list(snap_a.keys()) + list(snap_b.keys())))

        diff_rows = []
        for key in all_keys:
            val_a = snap_a.get(key)
            val_b = snap_b.get(key)
            if val_a != val_b:
                diff_rows.append(
                    [
                        key,
                        str(val_a) if val_a is not None else "—",
                        str(val_b) if val_b is not None else "—",
                    ]
                )

        if diff_rows:
            diff_table = markdown_table(["Field", "Version A", "Version B"], diff_rows)
            content += f"\n\n### Configuration Differences\n\n{diff_table}"
        else:
            content += "\n\n### Configuration Differences\n\n_No configuration differences found._"

        data = {
            "agent_id": str(agent.id),
            "version_a": {
                "id": str(version_a.id),
                "version_number": version_a.version_number,
                "score": (
                    float(version_a.score) if version_a.score is not None else None
                ),
                "test_count": version_a.test_count,
                "pass_rate": (
                    float(version_a.pass_rate)
                    if version_a.pass_rate is not None
                    else None
                ),
            },
            "version_b": {
                "id": str(version_b.id),
                "version_number": version_b.version_number,
                "score": (
                    float(version_b.score) if version_b.score is not None else None
                ),
                "test_count": version_b.test_count,
                "pass_rate": (
                    float(version_b.pass_rate)
                    if version_b.pass_rate is not None
                    else None
                ),
            },
        }

        return ToolResult(content=content, data=data)
