# Simulate Temporal Workflows

This module migrates Celery tasks from `simulate/tasks/` to Temporal workflows for better orchestration, observability, and reliability.

## Migration Status

| Celery Task | Temporal Component | Status |
|-------------|-------------------|--------|
| `run_eval_summary_task` | `run_eval_summary_activity` | 🔲 Pending |
| `ingest_call_logs_task` | `ingest_call_logs_activity` | 🔲 Pending |
| `add_scenario_columns_task` | `AddScenarioColumnsWorkflow` | 🔲 Pending |
| `generate_scenario_rows` | `ScenarioGenerationWorkflow` | 🔲 Pending |
| `monitor_test_executions` | **Eliminated** (no polling needed) | 🔲 Pending |
| `monitor_single_test_execution_task` | `TestExecutionWorkflow` | 🔲 Pending |
| `create_call_executions` | `CallExecutionWorkflow` | 🔲 Pending |

## Architecture Overview

### Current Celery Architecture (Problems)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            CELERY BEAT (Schedulers)                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  monitor_test_executions (every 30s)     create_call_executions (every 10s)         │
└─────────────────────┬───────────────────────────────────┬───────────────────────────┘
                      │                                   │
                      ▼                                   ▼
┌─────────────────────────────────────┐   ┌───────────────────────────────────────────┐
│ monitor_single_test_execution_task  │   │     create_call_executions (task)          │
│   - Polls VAPI for call status      │   │   - Handles stuck calls                    │
│   - Updates CallExecution status    │   │   - Creates inbound/outbound calls         │
│   - Triggers eval summary on done   │   │   - Manages phone number allocation        │
└─────────────────┬───────────────────┘   └───────────────────────────────────────────┘
                  │
                  │ (on all calls complete)
                  ▼
┌─────────────────────────────────────┐   ┌───────────────────────────────────────────┐
│ calculate_eval_explanation_summary  │   │         ingest_call_logs_task              │
│   - Generates AI summary of evals   │   │   - Downloads logs from VAPI               │
└─────────────────────────────────────┘   │   - Persists CallLogEntry records          │
                                          └───────────────────────────────────────────┘
```

**Issues:**
- Polling-based (every 10-30s) instead of event-driven
- No parent workflow coordinating the full test execution lifecycle
- Hidden dependencies (eval summary triggered inside TestExecutor)
- No failure recovery - if task fails mid-way, no resume mechanism
- State tracked via DB flags (`picked_up_by_executor`) instead of workflow state
- Monolithic tasks (generate_scenario_rows is ~1200 lines)

---

## New Temporal Architecture

### 1. Test Execution Workflow (Main Orchestrator)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        TestExecutionWorkflow (Parent)                                │
│                                                                                      │
│  Triggered by: API call to start test execution                                      │
│  Input: test_execution_id                                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  1. setup_test_execution_activity                                             │  │
│   │     - Load test execution, validate, set status to RUNNING                    │  │
│   │     - Return list of call_execution_ids to process                            │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  2. For each CallExecution: spawn CallExecutionWorkflow (child)               │  │
│   │     - Fan-out with controlled concurrency (semaphore)                         │  │
│   │     - Each child handles one phone call end-to-end                            │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  3. Wait for all CallExecutionWorkflows to complete                           │  │
│   │     - Collect results, track successes/failures                               │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  4. run_eval_summary_activity                                                 │  │
│   │     - Generate AI summary of test results                                     │  │
│   │     - Update TestExecution.eval_explanation_summary                           │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  5. finalize_test_execution_activity                                          │  │
│   │     - Update final status (COMPLETED/FAILED/PARTIAL)                          │  │
│   │     - Cleanup resources                                                       │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Call Execution Workflow (Child)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        CallExecutionWorkflow (Child)                                 │
│                                                                                      │
│  Input: call_execution_id, is_outbound, test_execution_id                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  1. check_call_limits_activity                                                │  │
│   │     - Verify org/app call limits before proceeding                            │  │
│   │     - Return: can_proceed, reason                                             │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                    ┌─────────────────┴─────────────────┐                            │
│                    ▼                                   ▼                            │
│   ┌────────────────────────────────┐     ┌────────────────────────────────────────┐ │
│   │  IF outbound:                  │     │  IF inbound:                           │ │
│   │  - acquire_phone_activity      │     │  - create_inbound_call_activity        │ │
│   │  - check_balance_activity      │     │    (simpler, no phone acquisition)     │ │
│   │  - create_assistant_activity   │     └────────────────────────────────────────┘ │
│   │  - create_outbound_call_activity                                                │
│   └────────────────────────────────┘                                                │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  2. LOOP: poll_call_status_activity                                           │  │
│   │     - workflow.sleep(20 seconds)  # Temporal timer, not Celery beat           │  │
│   │     - Check VAPI call status                                                  │  │
│   │     - Continue until: ended/completed/failed/cancelled                        │  │
│   │     - Timeout after 3 hours (configurable)                                    │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  3. process_call_completion_activity                                          │  │
│   │     - Fetch final VAPI call data                                              │  │
│   │     - Extract transcript, recording URL, cost                                 │  │
│   │     - Update CallExecution record                                             │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  4. ingest_call_logs_activity                                                 │  │
│   │     - Download logs from VAPI log URL                                         │  │
│   │     - Parse and persist CallLogEntry records                                  │  │
│   │     - Update logs_summary on CallExecution                                    │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  5. release_phone_activity (if outbound)                                      │  │
│   │     - Release phone number back to pool                                       │  │
│   │     - Cleanup simulation assistant                                            │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Scenario Generation Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        ScenarioGenerationWorkflow                                    │
│                                                                                      │
│  Triggered by: API POST /scenarios/{id}/add-rows/                                    │
│  Input: dataset_id, scenario_id, num_rows, description, row_ids                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  1. setup_generation_activity                                                 │  │
│   │     - Load dataset, scenario, agent definition                                │  │
│   │     - Extract conversation branches from ScenarioGraph                        │  │
│   │     - Build generation payload (requirements, constraints, schema)            │  │
│   │     - Return: generation_config, branch_metadata                              │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  2. generate_synthetic_data_activity                                          │  │
│   │     - Call SyntheticDataAgent.generate_and_validate()                         │  │
│   │     - Generate persona, situation, outcome for each row                       │  │
│   │     - Return: DataFrame with generated values                                 │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  3. validate_personas_activity                                                │  │
│   │     - Validate persona fields (name, gender, age_group, etc.)                 │  │
│   │     - Fill missing required fields with defaults                              │  │
│   │     - Return: validated DataFrame                                             │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  4. persist_cells_activity                                                    │  │
│   │     - Bulk create/update Cell records                                         │  │
│   │     - Update Column statuses to COMPLETED                                     │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4. Add Scenario Columns Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        AddScenarioColumnsWorkflow                                    │
│                                                                                      │
│  Triggered by: API POST /scenarios/{id}/add-columns/                                 │
│  Input: dataset_id, scenario_id, columns_info, column_ids                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  1. setup_columns_activity                                                    │  │
│   │     - Load dataset, scenario                                                  │  │
│   │     - Build payload for SyntheticDataAgent                                    │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  2. generate_column_data_activity                                             │  │
│   │     - Call SyntheticDataAgent.generate_column_data()                          │  │
│   │     - Return: DataFrame with column values                                    │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                               │
│                                      ▼                                               │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │  3. persist_column_cells_activity                                             │  │
│   │     - Bulk update Cell records                                                │  │
│   │     - Update Column statuses to COMPLETED                                     │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Task Queues

| Queue | Purpose | Concurrency |
|-------|---------|-------------|
| `tasks_xl` | Long-running workflows (test execution, scenario generation) | 10 |
| `tasks_l` | Medium activities (eval summary, call monitoring) | 50 |
| `tasks_s` | Short activities (status checks, phone release) | 100 |

---

## Retry Policies

```python
# For setup activities (fast, few retries)
SETUP_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=3,
)

# For VAPI/external API calls (longer, more retries)
EXTERNAL_API_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=5),
    maximum_interval=timedelta(minutes=2),
    maximum_attempts=5,
    backoff_coefficient=2.0,
)

# For LLM calls (longest, handles rate limits)
LLM_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=10),
    maximum_interval=timedelta(minutes=5),
    maximum_attempts=3,
    backoff_coefficient=2.0,
    non_retryable_error_types=["ValueError"],
)
```

---

## Migration Order

1. **`run_eval_summary_task`** - Simplest, standalone activity
2. **`ingest_call_logs_task`** - Standalone activity with clear input/output
3. **`add_scenario_columns_task`** - Medium complexity workflow
4. **`generate_scenario_rows`** - Complex workflow (break into activities)
5. **Test Execution Workflows** - Most complex, requires careful orchestration

---

## File Structure

```
tfc/temporal/simulate/
├── __init__.py      # Module exports
├── README.md        # This file
├── types.py         # Data classes (no Django imports - safe for Temporal sandbox)
├── workflows.py     # Workflow definitions
├── activities.py    # Activity definitions (Django imports OK here)
└── client.py        # Workflow starter functions
```

---

## Usage Examples

### Starting a Test Execution Workflow

```python
from tfc.temporal.simulate import start_test_execution_workflow

# From API view
workflow_id = await start_test_execution_workflow(
    test_execution_id=str(test_execution.id),
    max_concurrent_calls=5,
)
```

### Starting a Scenario Generation Workflow

```python
from tfc.temporal.simulate import start_scenario_generation_workflow

# From API view
workflow_id = await start_scenario_generation_workflow(
    dataset_id=str(dataset.id),
    scenario_id=str(scenario.id),
    num_rows=100,
    row_ids=new_row_ids,
)
```

---

## Key Benefits

| Benefit | Description |
|---------|-------------|
| **Event-driven** | No more polling - workflows wait for completion |
| **Full observability** | Temporal UI shows entire execution history |
| **Automatic retries** | Built-in retry policies with exponential backoff |
| **Resumability** | Workflows resume from last checkpoint after failures |
| **Controlled concurrency** | Semaphores limit parallel executions |
| **Clear ownership** | Each workflow owns its state machine |
| **Smaller activities** | Monolithic tasks broken into focused activities |
| **Timeout handling** | Per-activity and per-workflow timeouts |
