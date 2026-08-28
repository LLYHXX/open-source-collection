"""
Temporal activity heartbeat utilities.

Provides:
- Heartbeater: Auto-heartbeats at regular intervals
- HeartbeatDetails: Base class for serializing progress state
"""

import abc
import asyncio
import collections.abc
import dataclasses
import typing

import structlog
from temporalio import activity

logger = structlog.get_logger(__name__)


class Heartbeater:
    """Regular heartbeating during Temporal activity execution.

    This class manages two heartbeat tasks via a context manager:
    * A task that heartbeats regularly every 'heartbeat_timeout' / 'factor'.
    * A task that heartbeats after worker shutdown is detected.

    Usage:
        async with Heartbeater() as heartbeater:
            for batch in batches:
                process(batch)
                heartbeater.details = (batch_num, total_batches)

    Attributes:
        details: Set this attribute to a tuple to send as heartbeat details.
        factor: Used to determine interval between regular heartbeating.
            Higher = more frequent heartbeats. Default 120 means heartbeat
            every heartbeat_timeout/120 seconds (e.g., 2.5s for 5min timeout).
    """

    def __init__(self, details: tuple[typing.Any, ...] = (), factor: int = 120):
        self._details: tuple[typing.Any, ...] = details
        self.factor = factor
        self.heartbeat_task: asyncio.Task | None = None
        self.heartbeat_on_shutdown_task: asyncio.Task | None = None

    @property
    def details(self) -> tuple[typing.Any, ...]:
        """Return details if available, otherwise an empty tuple."""
        return self._details

    @details.setter
    def details(self, details: tuple[typing.Any, ...]) -> None:
        """Set tuple to be passed as heartbeat details."""
        self._details = details

    def set_from_heartbeat_details(self, details: "HeartbeatDetails") -> None:
        """Set `HeartbeatDetails` to be passed as heartbeat details."""
        self._details = tuple(details.serialize_details())

    async def __aenter__(self):
        """Enter managed heartbeating context."""

        # Send immediate heartbeat on entry to signal activity has started
        try:
            activity.heartbeat(*self.details)
            activity.logger.debug("Sent initial heartbeat on context entry")
        except Exception as e:
            activity.logger.warning(f"Initial heartbeat failed: {e}")

        async def heartbeat_forever(delay: float) -> None:
            """Heartbeat forever every delay seconds."""
            while True:
                await asyncio.sleep(delay)
                try:
                    activity.heartbeat(*self.details)
                except Exception as e:
                    activity.logger.warning(f"Heartbeat failed: {e}")

        heartbeat_timeout = activity.info().heartbeat_timeout

        if heartbeat_timeout:
            interval = heartbeat_timeout.total_seconds() / self.factor
            activity.logger.debug(f"Starting heartbeat task with interval {interval}s")
            self.heartbeat_task = asyncio.create_task(heartbeat_forever(interval))

        async def heartbeat_on_shutdown() -> None:
            """Handle the Worker shutting down by heartbeating our latest status."""
            try:
                await activity.wait_for_worker_shutdown()
            except Exception:
                return

            activity.logger.debug("Detected Worker shutdown, sending final heartbeat")

            if not self.details:
                return

            activity.heartbeat(*self.details)
            if heartbeat_timeout:
                heartbeat_timeout_seconds = heartbeat_timeout.total_seconds()
                activity.logger.debug(
                    f"Waiting {heartbeat_timeout_seconds}s for heartbeat to flush"
                )
                await asyncio.sleep(heartbeat_timeout_seconds)

        self.heartbeat_on_shutdown_task = asyncio.create_task(heartbeat_on_shutdown())

        return self

    async def __aexit__(self, *args, **kwargs):
        """Cancel heartbeating tasks on exit."""
        tasks_to_wait = []
        if self.heartbeat_task is not None:
            self.heartbeat_task.cancel()
            tasks_to_wait.append(self.heartbeat_task)

        if self.heartbeat_on_shutdown_task is not None:
            self.heartbeat_on_shutdown_task.cancel()
            tasks_to_wait.append(self.heartbeat_on_shutdown_task)

        if tasks_to_wait:
            await asyncio.wait(tasks_to_wait)

        # Send final heartbeat on exit
        try:
            activity.heartbeat(*self.details)
        except Exception:
            pass

        self.heartbeat_task = None
        self.heartbeat_on_shutdown_task = None


class EmptyHeartbeatError(Exception):
    """Raised when an activity heartbeat is empty."""

    def __init__(self):
        super().__init__("Heartbeat details sequence is empty")


class NotEnoughHeartbeatValuesError(Exception):
    """Raised when heartbeat doesn't contain expected number of values."""

    def __init__(self, details_len: int, expected: int):
        super().__init__(
            f"Not enough values in heartbeat details (expected {expected}, got {details_len})"
        )


class HeartbeatParseError(Exception):
    """Raised when heartbeat cannot be parsed into expected types."""

    def __init__(self, field: str):
        super().__init__(f"Parsing {field} from heartbeat details encountered an error")


@dataclasses.dataclass
class HeartbeatDetails(metaclass=abc.ABCMeta):
    """Base class for activity heartbeat details.

    Subclass this to define domain-specific progress tracking.
    Implement `deserialize_details` and `serialize_details` for your use case.

    Attributes:
        _remaining: Any remaining values in the heartbeat_details tuple.
    """

    _remaining: collections.abc.Sequence[typing.Any]

    @property
    def total_details(self) -> int:
        """The total number of parsed details + remaining."""
        return (len(dataclasses.fields(self.__class__)) - 1) + len(self._remaining)

    @classmethod
    @abc.abstractmethod
    def deserialize_details(
        cls, details: collections.abc.Sequence[typing.Any]
    ) -> dict[str, typing.Any]:
        """Deserialize HeartbeatDetails from a sequence."""
        return {"_remaining": details}

    @abc.abstractmethod
    def serialize_details(self) -> tuple[typing.Any, ...]:
        """Serialize HeartbeatDetails to a tuple."""
        return (self._remaining,)

    @classmethod
    def from_activity(cls, activity_module=None):
        """Instantiate from current activity context."""
        if activity_module is None:
            activity_module = activity
        details = activity_module.info().heartbeat_details
        return cls.from_activity_details(details)

    @classmethod
    def from_activity_details(cls, details):
        parsed = cls.deserialize_details(details)
        return cls(**parsed)


@dataclasses.dataclass
class BatchProgressDetails(HeartbeatDetails):
    """Heartbeat details for batch processing progress.

    Usage:
        # Resume from previous heartbeat
        try:
            details = BatchProgressDetails.from_activity(activity)
            start_batch = details.current_batch
        except EmptyHeartbeatError:
            start_batch = 0

        # Update progress
        heartbeater.set_from_heartbeat_details(
            BatchProgressDetails(current_batch=i, total_batches=total)
        )
    """

    current_batch: int
    total_batches: int

    @classmethod
    def deserialize_details(
        cls, details: collections.abc.Sequence[typing.Any]
    ) -> dict[str, typing.Any]:
        if len(details) == 0:
            raise EmptyHeartbeatError()

        if len(details) < 2:
            raise NotEnoughHeartbeatValuesError(len(details), 2)

        try:
            return {
                "current_batch": int(details[0]),
                "total_batches": int(details[1]),
                "_remaining": details[2:],
            }
        except (TypeError, ValueError) as e:
            raise HeartbeatParseError("batch progress") from e

    def serialize_details(self) -> tuple[typing.Any, ...]:
        return (self.current_batch, self.total_batches, *self._remaining)


@dataclasses.dataclass
class ItemProgressDetails(HeartbeatDetails):
    """Heartbeat details for item-by-item progress tracking.

    Usage:
        heartbeater.set_from_heartbeat_details(
            ItemProgressDetails(
                processed_count=100,
                total_count=1000,
                last_item_id="abc123"
            )
        )
    """

    processed_count: int
    total_count: int
    last_item_id: str = ""

    @classmethod
    def deserialize_details(
        cls, details: collections.abc.Sequence[typing.Any]
    ) -> dict[str, typing.Any]:
        if len(details) == 0:
            raise EmptyHeartbeatError()

        if len(details) < 2:
            raise NotEnoughHeartbeatValuesError(len(details), 2)

        try:
            return {
                "processed_count": int(details[0]),
                "total_count": int(details[1]),
                "last_item_id": str(details[2]) if len(details) > 2 else "",
                "_remaining": details[3:] if len(details) > 3 else [],
            }
        except (TypeError, ValueError) as e:
            raise HeartbeatParseError("item progress") from e

    def serialize_details(self) -> tuple[typing.Any, ...]:
        return (
            self.processed_count,
            self.total_count,
            self.last_item_id,
            *self._remaining,
        )


__all__ = [
    "Heartbeater",
    "HeartbeatDetails",
    "BatchProgressDetails",
    "ItemProgressDetails",
    "EmptyHeartbeatError",
    "NotEnoughHeartbeatValuesError",
    "HeartbeatParseError",
]
