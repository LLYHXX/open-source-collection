import structlog
from django.db import close_old_connections, transaction
from django.db.models import Count

logger = structlog.get_logger(__name__)
from model_hub.models.choices import StatusType
from model_hub.models.develop_dataset import Column
from model_hub.models.experiments import ExperimentsTable, PendingRowTask
from model_hub.views.experiment_runner import (
    ExperimentRunner,
    check_and_update_experiment_status,
    process_row_task,
)
from tfc.temporal import temporal_activity


@temporal_activity(time_limit=3600, queue="default")
def experiment_runner():
    """
    Periodic task that finds NOT_STARTED experiments and starts Temporal workflows for them.

    This task runs via Celery Beat but delegates actual experiment processing to Temporal workflows.
    Falls back to Celery if Temporal is unavailable.
    """

    experiments = list(
        ExperimentsTable.objects.filter(
            status=StatusType.NOT_STARTED.value, deleted=False
        ).all()
    )

    if not experiments:
        logger.info("No experiments to process")
        return

    experiment_ids = [experiment.id for experiment in experiments]

    # Try to start Temporal workflows for each experiment
    try:
        from tfc.temporal.experiments import start_experiment_workflow

        for experiment in experiments:
            try:
                workflow_id = start_experiment_workflow(
                    experiment_id=str(experiment.id),
                    max_concurrent_rows=10,
                )
                logger.info(
                    f"Started Temporal workflow {workflow_id} for experiment {experiment.id}"
                )
            except Exception as e:
                logger.exception(
                    f"Failed to start Temporal workflow for experiment {experiment.id}: {e}. "
                    "Falling back to Celery."
                )
                # Fall back to Celery for this experiment
                ExperimentsTable.objects.filter(id=experiment.id).update(
                    status=StatusType.RUNNING.value
                )
                process_experiments.apply_async(args=([str(experiment.id)],))
    except ImportError:
        # Temporal not available, fall back to Celery
        logger.warning("Temporal client not available, falling back to Celery")
        ExperimentsTable.objects.filter(id__in=experiment_ids).update(
            status=StatusType.RUNNING.value
        )
        process_experiments.apply_async(args=(experiment_ids,))


@temporal_activity(time_limit=3600, queue="tasks_s")
def check_running_experiments_status():
    """Check and update status for all experiments that are currently running"""

    try:
        close_old_connections()
        running_experiments = list(
            ExperimentsTable.objects.filter(
                status=StatusType.RUNNING.value, deleted=False
            ).values_list("id", flat=True)[:20]
        )

        if not running_experiments:
            logger.info("No running experiments to check")
            return

        logger.info(
            f"Checking status for {len(running_experiments)} running experiments"
        )

        # OPTIMIZATION: Bulk check which experiments have started processing
        experiment_ids_list = list(running_experiments)

        # Bulk check for experiment_datasets
        experiments_with_datasets = set(
            ExperimentsTable.objects.filter(id__in=experiment_ids_list, deleted=False)
            .filter(experiments_datasets__isnull=False)
            .distinct()
            .values_list("id", flat=True)
        )

        # Bulk check for columns
        experiments_with_columns = set(
            ExperimentsTable.objects.filter(id__in=experiment_ids_list, deleted=False)
            .filter(experiments_datasets__columns__deleted=False)
            .distinct()
            .values_list("id", flat=True)
        )

        # Combine sets
        experiments_to_check = experiments_with_datasets | experiments_with_columns

        skipped_count = 0
        for experiment_id in running_experiments:
            try:
                if experiment_id in experiments_to_check:
                    check_and_update_experiment_status(experiment_id)
                else:
                    skipped_count += 1
                    logger.debug(
                        f"Skipping experiment {experiment_id} - not started processing yet (will check on next run)"
                    )
            except Exception as e:
                logger.exception(
                    f"Error checking experiment status for {experiment_id}: {e}"
                )

        if skipped_count > 0:
            logger.info(
                f"Skipped {skipped_count} experiment(s) that haven't started processing yet"
            )

        close_old_connections()
    except Exception as e:
        logger.exception(f"Error in check_running_experiments_status: {e}")
        close_old_connections()


@temporal_activity(time_limit=3600 * 3, queue="tasks_l")
def process_experiments(experiment_ids):
    """Spawn Celery tasks for each experiment"""
    for experiment_id in experiment_ids:
        try:
            # Verify experiment exists and is not deleted
            experiment = ExperimentsTable.objects.get(id=experiment_id, deleted=False)
            # Spawn task for each experiment
            process_single_experiment_task.apply_async(
                args=(str(experiment_id),),
                queue="tasks_l",
            )
        except ExperimentsTable.DoesNotExist:
            logger.error(f"Experiment {experiment_id} not found or deleted")
        except Exception as e:
            logger.error(f"Error spawning task for experiment {experiment_id}: {e}")


@temporal_activity(time_limit=3600 * 3, queue="tasks_l")
def process_single_experiment_task(experiment_id: str):
    """Celery task to process a single experiment"""
    try:
        close_old_connections()
        logger.info(f"Processing experiment {experiment_id}")
        runner = ExperimentRunner(experiment_id=experiment_id)
        runner.run()
        close_old_connections()
    except Exception as e:
        logger.exception(
            f"Error in process_single_experiment_task for {experiment_id}: {e}"
        )
        # Mark experiment as failed
        try:
            experiment = ExperimentsTable.objects.get(id=experiment_id, deleted=False)
            experiment.status = StatusType.FAILED.value
            experiment.save(update_fields=["status"])
        except Exception:
            pass
        close_old_connections()


@temporal_activity(time_limit=3600, queue="tasks_s")
def process_pending_row_tasks():
    """
    Celery task to process pending row tasks with concurrency limit of 10 per experiment.
    Optimized with bulk operations and race condition protection.
    """
    try:
        close_old_connections()

        max_concurrent_per_experiment = 10
        max_tasks_to_process = 100  # Limit initial query to prevent memory issues

        # Get registered tasks with limit and proper ordering
        registered_tasks = (
            PendingRowTask.objects.filter(status=PendingRowTask.TaskStatus.REGISTERED)
            .select_related("row", "column", "dataset", "experiment")
            .order_by("created_at")[:max_tasks_to_process]
        )

        if not registered_tasks.exists():
            logger.info("No registered row tasks to process")
            return

        # OPTIMIZATION: Convert to list to avoid re-evaluating queryset
        tasks_list = list(registered_tasks)

        # Group by experiment_id in memory (single query already done)
        tasks_by_experiment = {}
        for task in tasks_list:
            experiment_id = task.experiment.id
            if experiment_id not in tasks_by_experiment:
                tasks_by_experiment[experiment_id] = []
            tasks_by_experiment[experiment_id].append(task)

        # OPTIMIZATION: Bulk fetch processing counts for all experiments in one query
        experiment_ids = list(tasks_by_experiment.keys())
        processing_counts = dict(
            PendingRowTask.objects.filter(
                experiment_id__in=experiment_ids,
                status=PendingRowTask.TaskStatus.PROCESSING,
            )
            .values("experiment_id")
            .annotate(count=Count("id"))
            .values_list("experiment_id", "count")
        )

        total_spawned = 0

        # Process each experiment's tasks, respecting per-experiment limit
        for experiment_id, tasks in tasks_by_experiment.items():
            # Get initial processing count from bulk query (defaults to 0 if not found)
            # This is just for logging - we'll re-check inside the transaction
            initial_processing_count = processing_counts.get(experiment_id, 0)

            # Use select_for_update to lock rows and prevent race conditions
            # CRITICAL FIX: Re-check processing count inside transaction to prevent race conditions
            with transaction.atomic():
                # Re-check current processing count inside transaction for accurate limit enforcement
                current_processing_count = PendingRowTask.objects.filter(
                    experiment_id=experiment_id,
                    status=PendingRowTask.TaskStatus.PROCESSING,
                ).count()

                # Calculate how many more tasks we can start for this experiment
                available_slots = max(
                    0, max_concurrent_per_experiment - current_processing_count
                )

                if available_slots == 0:
                    logger.debug(
                        f"Maximum concurrent row processing tasks reached for experiment {experiment_id} ({current_processing_count}/{max_concurrent_per_experiment})"
                    )
                    continue

                # Process up to available_slots tasks for this experiment
                tasks_to_process = tasks[:available_slots]
                task_ids = [task.id for task in tasks_to_process]

                # Lock and filter tasks that are still REGISTERED
                locked_tasks = list(
                    PendingRowTask.objects.select_for_update(skip_locked=True)
                    .filter(
                        id__in=task_ids,
                        status=PendingRowTask.TaskStatus.REGISTERED,  # Double-check status
                    )
                    .select_related("row", "column", "dataset", "experiment")
                )

                if not locked_tasks:
                    continue

                # Bulk update status to PROCESSING
                locked_task_ids = [t.id for t in locked_tasks]
                PendingRowTask.objects.filter(id__in=locked_task_ids).update(
                    status=PendingRowTask.TaskStatus.PROCESSING
                )

            logger.info(
                f"Processing {len(locked_tasks)} pending row tasks for experiment {experiment_id} (current processing: {current_processing_count}/{max_concurrent_per_experiment})"
            )

            # Spawn tasks for successfully locked and updated tasks
            for pending_task in locked_tasks:
                try:
                    # Spawn the actual processing task
                    process_row_task.apply_async(
                        args=(
                            str(pending_task.row.id),
                            str(pending_task.column.id),
                            str(pending_task.dataset.id),
                            str(pending_task.experiment.id),
                            pending_task.messages,
                            pending_task.model,
                            pending_task.model_config,
                            pending_task.output_format,
                            pending_task.run_prompt_config,
                        ),
                        queue="tasks_l",
                    )

                    logger.debug(
                        f"Spawned row processing task for row {pending_task.row.id}, column {pending_task.column.id}"
                    )
                    total_spawned += 1

                except Exception as e:
                    logger.exception(
                        f"Error spawning row processing task for pending_task {pending_task.id}: {e}"
                    )
                    # Mark as failed - use update for better performance
                    try:
                        PendingRowTask.objects.filter(id=pending_task.id).update(
                            status=PendingRowTask.TaskStatus.FAILED
                        )
                    except Exception as update_error:
                        logger.exception(
                            f"Error updating pending_task status: {update_error}"
                        )

        logger.info(
            f"Total spawned {total_spawned} row processing tasks across {len(tasks_by_experiment)} experiments"
        )

        close_old_connections()

    except Exception as e:
        logger.exception(f"Error in process_pending_row_tasks: {e}")
        close_old_connections()
