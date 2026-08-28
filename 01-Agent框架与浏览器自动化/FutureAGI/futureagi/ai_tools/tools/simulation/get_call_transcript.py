from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import (
    key_value_block,
    section,
    truncate,
)
from ai_tools.registry import register_tool


class GetCallTranscriptInput(PydanticBaseModel):
    call_execution_id: UUID = Field(description="The UUID of the call execution")


@register_tool
class GetCallTranscriptTool(BaseTool):
    name = "get_call_transcript"
    description = (
        "Returns the conversation transcript for a call execution. "
        "Shows speaker role, content, and timestamps in chronological order."
    )
    category = "simulation"
    input_model = GetCallTranscriptInput

    def execute(
        self, params: GetCallTranscriptInput, context: ToolContext
    ) -> ToolResult:

        from simulate.models.test_execution import CallExecution, CallTranscript

        try:
            call = CallExecution.objects.select_related("scenario").get(
                id=params.call_execution_id,
                test_execution__run_test__organization=context.organization,
            )
        except CallExecution.DoesNotExist:
            return ToolResult.not_found("Call Execution", str(params.call_execution_id))

        scenario_name = call.scenario.name if call.scenario else "—"

        transcripts = CallTranscript.objects.filter(call_execution=call).order_by(
            "start_time_ms"
        )

        info = key_value_block(
            [
                ("Call ID", f"`{call.id}`"),
                ("Scenario", scenario_name),
                ("Messages", str(transcripts.count())),
            ]
        )

        content = section(f"Transcript: {scenario_name}", info)

        if not transcripts.exists():
            content += "\n\n_No transcript entries found for this call._"
            return ToolResult(
                content=content,
                data={"call_id": str(call.id), "transcript": []},
            )

        content += "\n\n---\n\n"

        transcript_data = []
        for t in transcripts[:100]:  # Limit to 100 entries
            role = t.speaker_role.upper()
            time_str = ""
            if t.start_time_ms:
                seconds = t.start_time_ms / 1000
                minutes = int(seconds // 60)
                secs = int(seconds % 60)
                time_str = f"[{minutes:02d}:{secs:02d}] "

            content += f"**{role}:** {time_str}{truncate(t.content, 500)}\n\n"

            transcript_data.append(
                {
                    "speaker_role": t.speaker_role,
                    "content": t.content,
                    "start_time_ms": t.start_time_ms,
                    "end_time_ms": t.end_time_ms,
                }
            )

        if transcripts.count() > 100:
            content += f"\n\n_Showing 100 of {transcripts.count()} transcript entries._"

        return ToolResult(
            content=content,
            data={"call_id": str(call.id), "transcript": transcript_data},
        )
