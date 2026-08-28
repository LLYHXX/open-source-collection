"""
Data classes for call execution workflows and activities.

IMPORTANT: Do NOT import Django models or any Django-dependent code here.
These types are used in Temporal workflow definitions which run in a sandbox.

Structure:
    types/
    ├── __init__.py           # This file - re-exports all types
    ├── test_execution.py     # TestExecutionWorkflow types
    ├── call_execution.py     # CallExecutionWorkflow types
    ├── dispatcher.py         # CallDispatcherWorkflow types
    └── activities.py         # Activity input/output types
"""

# Activity Types
from simulate.temporal.types.activities import (  # Setup Activities; Call Preparation Activities; Call Execution Activities; Evaluation Activities; Downstream Activities; Signal Activities
    AcquirePhoneInput,
    AcquirePhoneOutput,
    BackgroundSoundInput,
    BackgroundSoundOutput,
    CheckBalanceInput,
    CheckBalanceOutput,
    CreateCallRecordsInput,
    CreateCallRecordsOutput,
    CreateProviderCallInput,
    CreateProviderCallOutput,
    DownstreamTasksInput,
    EvalResult,
    EvalSummaryInput,
    FinalizeInput,
    GetUnlaunchedCallsInput,
    GetUnlaunchedCallsOutput,
    MonitorCallInput,
    MonitorCallOutput,
    PrepareCallInput,
    PrepareCallOutput,
    ReleasePhoneInput,
    ReleaseSlotInput,
    RunCallEvalsInput,
    RunCallEvalsOutput,
    SetupTestInput,
    SetupTestOutput,
    SignalCallAnalyzingInput,
    SignalCallCompleteInput,
    SignalSlotBatchInput,
    StoreCallDataInput,
    StorePendingCallsInput,
    UpdateCallStatusInput,
    UpdateMetricsInput,
)

# Call Execution Types
from simulate.temporal.types.call_execution import (
    CallExecutionInput,
    CallExecutionOutput,
    CallInfo,
    CallResult,
    CallStatus,
)

# Dispatcher Types
from simulate.temporal.types.dispatcher import (
    ActiveCall,
    DispatcherState,
    DispatcherStatus,
    SlotGrant,
    SlotRequest,
)

# Test Execution Types
from simulate.temporal.types.test_execution import (
    CallAnalyzingSignal,
    TestExecutionInput,
    TestExecutionOutput,
    TestExecutionState,
    TestExecutionStatus,
)

__all__ = [
    # Test Execution
    "TestExecutionInput",
    "TestExecutionOutput",
    "TestExecutionState",
    "TestExecutionStatus",
    "CallAnalyzingSignal",
    # Call Execution
    "CallExecutionInput",
    "CallExecutionOutput",
    "CallInfo",
    "CallResult",
    "CallStatus",
    # Dispatcher
    "SlotRequest",
    "SlotGrant",
    "ActiveCall",
    "DispatcherStatus",
    "DispatcherState",
    # Activities - Setup
    "SetupTestInput",
    "SetupTestOutput",
    "CreateCallRecordsInput",
    "CreateCallRecordsOutput",
    "StorePendingCallsInput",
    "GetUnlaunchedCallsInput",
    "GetUnlaunchedCallsOutput",
    "FinalizeInput",
    # Activities - Call Preparation
    "PrepareCallInput",
    "PrepareCallOutput",
    "CheckBalanceInput",
    "CheckBalanceOutput",
    "AcquirePhoneInput",
    "AcquirePhoneOutput",
    "ReleasePhoneInput",
    "BackgroundSoundInput",
    "BackgroundSoundOutput",
    # Activities - Call Execution
    "CreateProviderCallInput",
    "CreateProviderCallOutput",
    "MonitorCallInput",
    "MonitorCallOutput",
    "StoreCallDataInput",
    "UpdateCallStatusInput",
    # Activities - Evaluation
    "RunCallEvalsInput",
    "RunCallEvalsOutput",
    "EvalResult",
    "EvalSummaryInput",
    # Activities - Downstream
    "UpdateMetricsInput",
    "DownstreamTasksInput",
    # Activities - Signals
    "ReleaseSlotInput",
    "SignalCallAnalyzingInput",
    "SignalCallCompleteInput",
    "SignalSlotBatchInput",
]
