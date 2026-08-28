"""
Temporal activities for call execution.

Activities are organized by queue size based on resource requirements:
- small.py (tasks_s): Lightweight operations (signals, status updates, phone pool)
- large.py (tasks_l): Standard operations (workflows, provider calls, monitoring)
- xl.py (tasks_xl): Resource-intensive operations (evaluations, LLM calls)

Activities CAN import Django models and other Django-dependent code,
unlike workflows which run in a sandboxed environment.
"""

# Activity implementations will be added in later phases
# from simulate.temporal.activities.small import ...
# from simulate.temporal.activities.large import ...
# from simulate.temporal.activities.xl import ...

__all__: list[str] = []
