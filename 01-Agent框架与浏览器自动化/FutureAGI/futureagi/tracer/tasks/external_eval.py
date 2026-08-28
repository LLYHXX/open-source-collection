"""
External Evaluation Tasks

Tasks for processing external evaluation configurations.
"""

import structlog

from tfc.temporal import temporal_activity

logger = structlog.get_logger(__name__)


@temporal_activity(
    max_retries=0,
    time_limit=3600,
    queue="default",
)
def process_external_evals():
    """
    Process pending external evaluation configurations.

    Finds all pending ExternalEvalConfig records and triggers
    their processing asynchronously.
    """
    from tracer.models.external_eval_config import ExternalEvalConfig, StatusChoices
    from tracer.utils.external_eval import run_external_eval_config

    logger.info("Processing external evals")

    pending_configs = list(
        ExternalEvalConfig.objects.filter(status=StatusChoices.PENDING)
    )

    if not pending_configs:
        logger.info("No pending configs to process")
        return

    config_ids = [config.id for config in pending_configs]
    logger.info(f"Found {len(config_ids)} pending configs to process")
    ExternalEvalConfig.objects.filter(id__in=config_ids).update(
        status=StatusChoices.PROCESSING
    )

    for config in pending_configs:
        run_external_eval_config.delay(config.id)
