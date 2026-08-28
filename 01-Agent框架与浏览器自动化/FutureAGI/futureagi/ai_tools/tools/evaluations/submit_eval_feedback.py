from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field

from ai_tools.base import BaseTool, ToolContext, ToolResult
from ai_tools.formatting import key_value_block, section
from ai_tools.registry import register_tool


class SubmitEvalFeedbackInput(PydanticBaseModel):
    eval_template_id: UUID = Field(
        description="The UUID of the eval template this feedback is for"
    )
    source_id: str = Field(
        description=(
            "The source ID (e.g. row ID, trace ID, or log ID) that the feedback references"
        )
    )
    feedback_value: str = Field(
        description="Feedback value: 'passed' or 'failed'",
    )
    explanation: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Optional explanation for the feedback",
    )
    feedback_improvement: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Optional suggestion for how the evaluation could be improved",
    )
    source: Optional[str] = Field(
        default="eval_playground",
        description=(
            "Source context: 'dataset', 'prompt', 'sdk', 'trace', "
            "'experiment', 'observe', or 'eval_playground'"
        ),
    )
    row_id: Optional[str] = Field(
        default=None,
        description="Optional row ID if feedback is for a dataset row",
    )


@register_tool
class SubmitEvalFeedbackTool(BaseTool):
    name = "submit_eval_feedback"
    description = (
        "Submits feedback on an evaluation result (passed/failed). "
        "Feedback is used to improve evaluation quality over time. "
        "Requires an eval template ID and a source ID referencing the evaluated item."
    )
    category = "evaluations"
    input_model = SubmitEvalFeedbackInput

    def execute(
        self, params: SubmitEvalFeedbackInput, context: ToolContext
    ) -> ToolResult:

        from model_hub.models.choices import FeedbackSourceChoices
        from model_hub.models.evals_metric import EvalTemplate, Feedback

        # Validate eval template
        try:
            template = EvalTemplate.objects.get(
                id=params.eval_template_id, deleted=False
            )
        except EvalTemplate.DoesNotExist:
            return ToolResult.not_found("Eval Template", str(params.eval_template_id))

        # Validate feedback value
        valid_values = ["passed", "failed"]
        if params.feedback_value.lower() not in valid_values:
            return ToolResult.error(
                f"Invalid feedback_value '{params.feedback_value}'. Must be one of: {', '.join(valid_values)}",
                error_code="VALIDATION_ERROR",
            )

        # Validate source
        valid_sources = [choice.value for choice in FeedbackSourceChoices]
        source = params.source or "eval_playground"
        if source not in valid_sources:
            return ToolResult.error(
                f"Invalid source '{source}'. Must be one of: {', '.join(valid_sources)}",
                error_code="VALIDATION_ERROR",
            )

        try:
            feedback = Feedback(
                source=source,
                source_id=params.source_id,
                eval_template=template,
                value=params.feedback_value.lower(),
                explanation=params.explanation or "",
                feedback_improvement=params.feedback_improvement or "",
                user=context.user,
                row_id=params.row_id,
                organization=context.organization,
                workspace=context.workspace,
            )
            feedback.save()
        except Exception as e:
            from ai_tools.error_codes import code_from_exception

            return ToolResult.error(
                f"Failed to submit feedback: {str(e)}",
                error_code=code_from_exception(e),
            )

        info = key_value_block(
            [
                ("Feedback ID", f"`{feedback.id}`"),
                ("Template", template.name),
                ("Value", params.feedback_value),
                ("Source", source),
                ("Source ID", f"`{params.source_id}`"),
                ("Explanation", params.explanation or "—"),
            ]
        )

        content = section("Eval Feedback Submitted", info)

        return ToolResult(
            content=content,
            data={
                "feedback_id": str(feedback.id),
                "eval_template_id": str(template.id),
                "eval_template_name": template.name,
                "value": params.feedback_value.lower(),
                "source": source,
                "source_id": params.source_id,
            },
        )
