"""
Signal definitions for inter-workflow communication.

Signals are used for:
- Slot allocation (dispatcher <-> call workflows)
- Completion notifications (child -> parent workflows)
- Cancellation requests (parent -> child workflows)
- Dynamic limit updates (external -> dispatcher)

Signal handlers are defined within workflow classes.
This module contains signal-related utilities and constants.
"""

# Signal names (for consistency across workflows)
SIGNAL_SLOT_GRANTED = "slot_granted"
SIGNAL_CALL_COMPLETED = "call_completed"
SIGNAL_CALL_ANALYZING = "call_analyzing"
SIGNAL_CANCEL_EXECUTION = "cancel_execution"
SIGNAL_CANCEL_CALL = "cancel"
SIGNAL_REQUEST_SLOT = "request_slot"
SIGNAL_RELEASE_SLOT = "release_slot"
SIGNAL_UPDATE_LIMITS = "update_limits"

# Phone number dispatcher signals
SIGNAL_REQUEST_PHONE_NUMBER = "request_phone_number"
SIGNAL_RELEASE_PHONE_NUMBER = "release_phone_number_signal"
SIGNAL_PHONE_NUMBER_GRANTED = "phone_number_granted"

__all__ = [
    "SIGNAL_SLOT_GRANTED",
    "SIGNAL_CALL_COMPLETED",
    "SIGNAL_CALL_ANALYZING",
    "SIGNAL_CANCEL_EXECUTION",
    "SIGNAL_CANCEL_CALL",
    "SIGNAL_REQUEST_SLOT",
    "SIGNAL_RELEASE_SLOT",
    "SIGNAL_UPDATE_LIMITS",
    "SIGNAL_REQUEST_PHONE_NUMBER",
    "SIGNAL_RELEASE_PHONE_NUMBER",
    "SIGNAL_PHONE_NUMBER_GRANTED",
]
