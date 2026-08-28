from concurrent.futures import ThreadPoolExecutor, as_completed

import structlog
from django.db import close_old_connections

logger = structlog.get_logger(__name__)
from model_hub.models.choices import StatusType
from model_hub.models.develop_optimisation import OptimizationDataset
from model_hub.views.develop_optimiser import DevelopOptimizer
from tfc.telemetry import wrap_for_thread
from tfc.temporal import temporal_activity


@temporal_activity(time_limit=3600, queue="tasks_l")
def optimization_runner():
    # Get all not started optimization tasks
    optimizations = OptimizationDataset.objects.filter(
        status=StatusType.NOT_STARTED.value
    ).all()

    # Wrap function with OTel context propagation for thread safety
    wrapped_process_optimization = wrap_for_thread(process_optimization)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(wrapped_process_optimization, optimization)
            for optimization in optimizations
        ]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"An error occurred: {e}")


def process_optimization(optimization):
    try:
        close_old_connections()
        optimizer = DevelopOptimizer(optim_obj_id=optimization.id)
        optimizer.run()
    finally:
        close_old_connections()
