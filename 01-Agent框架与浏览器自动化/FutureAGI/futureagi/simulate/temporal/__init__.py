"""
Temporal workflows and activities for call execution in the simulate app.

This module contains the business logic for:
- Test execution orchestration (TestExecutionWorkflow)
- Call execution lifecycle (CallExecutionWorkflow)
- Rate limiting / slot dispatch (CallDispatcherWorkflow)

Structure:
    simulate/temporal/
    ├── __init__.py          # This file - package exports
    ├── constants.py         # Queue names, limits, thresholds
    ├── retry_policies.py    # Retry configurations
    ├── types/               # Data classes (no Django imports)
    │   ├── test_execution.py
    │   ├── call_execution.py
    │   ├── dispatcher.py
    │   └── activities.py
    ├── activities/          # Activity implementations
    │   ├── small.py         # tasks_s queue activities
    │   ├── large.py         # tasks_l queue activities
    │   └── xl.py            # tasks_xl queue activities
    ├── workflows/           # Workflow definitions
    │   ├── test_execution.py
    │   ├── call_execution.py
    │   └── call_dispatcher.py
    └── signals/             # Signal definitions

Registration and client code lives in tfc/temporal/simulate/.

IMPORTANT: Do NOT import Django models or any Django-dependent code
in types/ or workflows/ modules. Activities can import Django.
"""

from simulate.temporal.constants import (
    CONTINUE_AS_NEW_THRESHOLD,
    DEFAULT_APP_LIMIT,
    DEFAULT_ORG_LIMIT,
    DISPATCHER_CONTINUE_AS_NEW_THRESHOLD,
    LAUNCH_BATCH_SIZE,
    MAX_CALLS_PER_ORCHESTRATOR,
    QUEUE_L,
    QUEUE_S,
    QUEUE_XL,
)
from simulate.temporal.retry_policies import (
    DB_RETRY_POLICY,
    PROVIDER_RETRY_POLICY,
    SIGNAL_RETRY_POLICY,
)

__all__ = [
    # Constants
    "QUEUE_S",
    "QUEUE_L",
    "QUEUE_XL",
    "LAUNCH_BATCH_SIZE",
    "CONTINUE_AS_NEW_THRESHOLD",
    "DISPATCHER_CONTINUE_AS_NEW_THRESHOLD",
    "MAX_CALLS_PER_ORCHESTRATOR",
    "DEFAULT_APP_LIMIT",
    "DEFAULT_ORG_LIMIT",
    # Retry Policies
    "DB_RETRY_POLICY",
    "PROVIDER_RETRY_POLICY",
    "SIGNAL_RETRY_POLICY",
]
