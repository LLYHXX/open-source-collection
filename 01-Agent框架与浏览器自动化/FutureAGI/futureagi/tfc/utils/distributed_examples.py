"""
Integration Examples for Distributed Locks and State Management.

This file shows how to refactor existing code that uses local locks to use
the distributed lock manager and evaluation tracker.

BEFORE APPLYING:
1. Ensure Redis is available (add REDIS_URL to environment)
2. Test with fallback enabled first
3. Deploy gradually with feature flags if needed
"""

# =============================================================================
# EXAMPLE 1: Refactoring user_evaluation.py
# =============================================================================

# BEFORE (model_hub/tasks/user_evaluation.py):
# -------------------------------------------
# from threading import Lock
#
# running_evals: dict[int, bool] = {}
# evals_lock = Lock()
#
# def process_single_evaluation(user_eval_metric):
#     with evals_lock:
#         if user_eval_metric.id in running_evals:
#             old_runner = running_evals[user_eval_metric.id]
#             old_runner.cancel_event = True
#
#     runner = EvaluationRunner(...)
#
#     with evals_lock:
#         running_evals[user_eval_metric.id] = runner
#
#     runner.run_prompt()
#
#     with evals_lock:
#         del running_evals[user_eval_metric.id]
#
#
# AFTER (using distributed state):
# --------------------------------

import structlog

from tfc.utils.distributed_locks import distributed_lock_manager
from tfc.utils.distributed_state import CancellableRunner, evaluation_tracker

logger = structlog.get_logger(__name__)


def process_single_evaluation_distributed(user_eval_metric):
    """
    Distributed version of process_single_evaluation.

    Key changes:
    1. Uses Redis-backed tracker instead of in-memory dict
    2. Supports cancel signals across all instances
    3. Prevents duplicate processing with distributed locking
    """
    eval_id = user_eval_metric.id

    # Check if already running and request cancellation if needed
    if evaluation_tracker.is_running(eval_id):
        running_info = evaluation_tracker.get_running_info(eval_id)
        logger.info(
            f"Evaluation {eval_id} already running on {running_info.instance_id}, "
            "requesting cancellation"
        )
        evaluation_tracker.request_cancel(eval_id, reason="New evaluation requested")
        # Optionally wait for cancellation to complete
        # time.sleep(2)

    # Use distributed lock to prevent race conditions during startup
    with distributed_lock_manager.lock(f"eval_start:{eval_id}", timeout=30):
        # Double-check after acquiring lock
        if evaluation_tracker.is_running(eval_id):
            logger.warning(
                f"Evaluation {eval_id} started by another instance during lock wait"
            )
            return

        # Mark as running (with this instance's info)
        if not evaluation_tracker.mark_running(
            eval_id,
            runner_info={
                "dataset_id": str(user_eval_metric.dataset.id),
                "template": user_eval_metric.template.name,
            },
        ):
            logger.warning(f"Failed to mark evaluation {eval_id} as running")
            return

    try:
        # Create runner (now uses CancellableRunner mixin for distributed cancel)
        runner = DistributedEvaluationRunner(
            eval_id=eval_id,
            user_eval_metric_id=user_eval_metric.id,
            is_only_eval=True,
            source="dataset_evaluation",
        )

        # Run the evaluation
        runner.run_prompt()

    except Exception as e:
        logger.exception(f"Error in evaluation {eval_id}: {e}")
        raise
    finally:
        # Always clean up
        evaluation_tracker.mark_completed(eval_id)


class DistributedEvaluationRunner(CancellableRunner):
    """
    Example of integrating CancellableRunner with existing EvaluationRunner.

    This shows how to make an existing runner support distributed cancellation.
    """

    def __init__(self, eval_id: int, user_eval_metric_id: int, **kwargs):
        # Initialize the cancellation support
        super().__init__(eval_id, evaluation_tracker)

        # Store params for actual runner initialization
        self.user_eval_metric_id = user_eval_metric_id
        self.kwargs = kwargs
        self._actual_runner = None

    def run_prompt(self):
        """Run the evaluation with cancellation checks."""
        from model_hub.views.eval_runner import EvaluationRunner

        # Create the actual runner
        self._actual_runner = EvaluationRunner(
            user_eval_metric_id=self.user_eval_metric_id, **self.kwargs
        )

        # Inject our distributed cancel checking into the runner
        # The runner should periodically call self.check_cancelled()
        self._actual_runner._distributed_cancel_checker = self.check_cancelled

        try:
            self._actual_runner.run_prompt()
        except CancelledException:
            self.handle_cancellation()
            raise


class CancelledException(Exception):
    """Raised when an evaluation is cancelled."""

    pass


# =============================================================================
# EXAMPLE 2: Refactoring ModelLoader with distributed coordination
# =============================================================================

# BEFORE (model_serving/app/utils/load_model.py):
# -----------------------------------------------
# class ModelLoader:
#     _models: dict[str, object] = {}
#     _loading_locks: dict[str, threading.Lock] = {}
#     _global_lock = threading.Lock()
#
#
# AFTER (with distributed locking for coordination):
# --------------------------------------------------
# Note: Models are still loaded per-instance (they can't be shared via Redis),
# but we use distributed locking to coordinate loading and prevent thundering herd.


class DistributedModelLoader:
    """
    Model loader with distributed coordination.

    Each instance still maintains its own model cache (models can't be serialized
    to Redis), but we use distributed locks to:
    1. Prevent multiple instances from loading the same model simultaneously
    2. Coordinate cleanup operations
    3. Share model availability status
    """

    _models: dict = {}
    _model_last_used: dict = {}

    @classmethod
    def get_model(cls, model_name: str, **kwargs) -> object:
        """Get a model with distributed coordination."""
        instance_key = cls._get_instance_key(model_name, kwargs)

        # Fast path: return cached model
        if instance_key in cls._models:
            cls._update_usage(instance_key)
            return cls._models[instance_key]

        # Use distributed lock to prevent thundering herd
        # Multiple instances requesting the same model will queue up
        with distributed_lock_manager.lock(
            f"model_load:{instance_key}",
            timeout=300,  # 5 minutes for model loading
            blocking_timeout=60,
        ):
            # Double-check after acquiring lock
            if instance_key in cls._models:
                cls._update_usage(instance_key)
                return cls._models[instance_key]

            # Load the model
            logger.info(f"Loading model: {instance_key}")
            model_instance = cls._load_model(model_name, kwargs)
            cls._models[instance_key] = model_instance
            cls._update_usage(instance_key)

            # Optionally publish model availability to other instances
            # This could be used for load balancing decisions
            cls._publish_model_available(instance_key)

            return model_instance

    @classmethod
    def _get_instance_key(cls, model_name: str, kwargs: dict) -> str:
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            return f"{model_name}_{'&'.join(f'{k}={v}' for k, v in sorted_kwargs)}"
        return model_name

    @classmethod
    def _load_model(cls, model_name: str, kwargs: dict) -> object:
        # Actual model loading logic
        from app.config.settings import MODEL_NAME_TO_CLASS_MAPPING

        model_class = MODEL_NAME_TO_CLASS_MAPPING.get(model_name)
        return model_class(**kwargs)

    @classmethod
    def _update_usage(cls, instance_key: str):
        import time

        cls._model_last_used[instance_key] = time.time()

    @classmethod
    def _publish_model_available(cls, instance_key: str):
        # Publish to Redis that this model is now available on this instance
        # Other instances could use this for intelligent routing
        pass


# =============================================================================
# EXAMPLE 3: Using the distributed lock decorator
# =============================================================================

from tfc.utils.distributed_locks import DistributedLock


@DistributedLock("experiment_{experiment_id}", timeout=60)
def run_experiment(experiment_id: int):
    """
    This function is protected by a distributed lock.

    Only one instance can run an experiment with the same ID at a time.
    The lock name includes the experiment_id parameter.
    """
    # ... experiment logic ...
    pass


@DistributedLock("error_localizer_{task_id}", timeout=300)
def process_error_localization(task_id: int):
    """
    Distributed lock for error localization tasks.
    """
    # ... localization logic ...
    pass


# =============================================================================
# EXAMPLE 4: Health check and monitoring
# =============================================================================


def check_distributed_system_health() -> dict:
    """
    Health check for the distributed system.

    Call this from your health check endpoint.
    """
    from tfc.utils.distributed_locks import distributed_lock_manager
    from tfc.utils.distributed_state import evaluation_tracker

    return {
        "lock_manager": distributed_lock_manager.health_check(),
        "evaluation_tracker": {
            "available": evaluation_tracker.is_available,
            "instance_id": evaluation_tracker.instance_id,
            "running_locally": len(evaluation_tracker.get_instance_running()),
            "total_running": len(evaluation_tracker.get_all_running()),
        },
    }


def get_running_evaluations_status() -> list:
    """
    Get status of all running evaluations across all instances.

    Useful for debugging and monitoring dashboards.
    """
    from tfc.utils.distributed_state import evaluation_tracker

    running = evaluation_tracker.get_all_running()
    return [
        {
            "eval_id": info.task_id,
            "instance": info.instance_id,
            "started_at": info.started_at,
            "cancel_requested": info.cancel_requested,
            "metadata": info.metadata,
        }
        for info in running
    ]


# =============================================================================
# EXAMPLE 5: Feature flag for gradual rollout
# =============================================================================

import os

USE_DISTRIBUTED_LOCKS = os.getenv("USE_DISTRIBUTED_LOCKS", "false").lower() == "true"


def process_evaluation_with_feature_flag(user_eval_metric):
    """
    Example of gradual rollout using feature flag.
    """
    if USE_DISTRIBUTED_LOCKS:
        return process_single_evaluation_distributed(user_eval_metric)
    else:
        # Fall back to original implementation
        from model_hub.tasks.user_evaluation import process_single_evaluation

        return process_single_evaluation(user_eval_metric)
