"""
Cell Output Sink — writes node outputs to model_hub.Cell model.

Required sink config keys:
    - dataset_id: str (UUID)
    - column_id: str (UUID)
    - row_id: str (UUID)

Optional sink config keys:
    - output_key: str — which output port value to store (defaults to first output key)
"""

import json
from typing import Any

import structlog

from agent_playground.services.engine.output_sink import (
    BaseOutputSink,
    OutputSinkContext,
    register_sink,
)

logger = structlog.get_logger(__name__)

# Map graph execution status to Cell status
_STATUS_MAP = {
    "SUCCESS": "pass",
    "FAILED": "error",
    "SKIPPED": "error",
}


class CellOutputSink(BaseOutputSink):
    """
    Writes node output to a model_hub.Cell.

    On SUCCESS: stores the output value with status=PASS.
    On FAILED: stores error info in value and reason in value_infos with status=ERROR.

    Status cascade (column → experiment_dataset → experiment) is NOT handled here.
    The Temporal workflow calls check_and_update_column_status at the right time
    (after all rows complete), same pattern as ProcessPromptWorkflow.
    """

    def validate_config(self, config: dict[str, Any]) -> None:
        required = ("dataset_id", "column_id", "row_id")
        missing = [k for k in required if k not in config]
        if missing:
            raise ValueError(f"CellOutputSink missing required config keys: {missing}")

    def store(self, context: OutputSinkContext) -> None:
        # Import here to avoid circular imports at module load time
        from model_hub.models.develop_dataset import Cell

        dataset_id = context.config["dataset_id"]
        column_id = context.config["column_id"]
        row_id = context.config["row_id"]
        output_key = context.config.get("output_key")

        # Guard: don't overwrite cleanup state if experiment was cancelled
        # while the graph execution activity's thread was in-flight.
        experiment_id = context.config.get("experiment_id")
        if experiment_id:
            import uuid as _uuid

            from model_hub.services.experiment_utils import is_experiment_cancelled

            if is_experiment_cancelled(_uuid.UUID(str(experiment_id))):
                logger.info(
                    "cell_output_sink_skipped_cancelled",
                    dataset_id=dataset_id,
                    column_id=column_id,
                    row_id=row_id,
                )
                return

        cell_status = _STATUS_MAP.get(context.status, "pass")

        if context.status == "SUCCESS":
            # Extract value from outputs
            if output_key and output_key in context.outputs:
                value = context.outputs[output_key]
            elif context.outputs:
                value = next(iter(context.outputs.values()))
            else:
                value = ""

            # Serialize non-string values
            if value is not None and not isinstance(value, str):
                value = json.dumps(value)

            value_infos = context.metadata if context.metadata else {}
        else:
            # FAILED — store error info
            error_msg = context.metadata.get("error", "") if context.metadata else ""
            if not error_msg and context.outputs:
                error_msg = str(next(iter(context.outputs.values()), ""))
            value = error_msg
            value_infos = {"reason": error_msg}

        Cell.objects.update_or_create(
            column_id=column_id,
            row_id=row_id,
            dataset_id=dataset_id,
            defaults={
                "value": str(value) if value else "",
                "value_infos": json.dumps(value_infos),
                "status": cell_status,
                "deleted": False,
            },
        )

        logger.info(
            "cell_output_sink_stored",
            node_id=context.node_id,
            node_name=context.node_name,
            dataset_id=dataset_id,
            column_id=column_id,
            row_id=row_id,
            status=cell_status,
        )


register_sink("cell", CellOutputSink())
