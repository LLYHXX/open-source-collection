"""Repository for CallTranscript model — encapsulates all ORM access."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from simulate.models.test_execution import CallExecution, CallTranscript


class CallTranscriptRepository:
    """Data access layer for CallTranscript."""

    @staticmethod
    async def create(
        call_id: UUID,
        role: str,
        content: str,
        start_time_ms: int,
        end_time_ms: int = 0,
    ) -> dict[str, Any]:
        """Create a single transcript row.

        ``role`` should be a CallTranscript.SpeakerRole value
        (e.g. "user", "assistant").
        """
        call_execution = await CallExecution.objects.aget(id=call_id)
        transcript = await CallTranscript.objects.acreate(
            call_execution=call_execution,
            speaker_role=role,
            content=content,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
        )
        return {"id": str(transcript.id)}

    @staticmethod
    async def bulk_create(
        call_id: UUID,
        transcripts: list[dict[str, Any]],
    ) -> int:
        """Create multiple transcript rows in a single bulk insert.

        Each item in ``transcripts`` must have keys:
        ``role``, ``content``, ``start_time_ms``.

        Returns the number of rows created.
        """
        call_execution = await CallExecution.objects.aget(id=call_id)
        objects = [
            CallTranscript(
                call_execution=call_execution,
                speaker_role=t["role"],
                content=t["content"],
                start_time_ms=t["start_time_ms"],
                end_time_ms=t.get("end_time_ms", 0),
            )
            for t in transcripts
        ]
        created = await CallTranscript.objects.abulk_create(objects)
        return len(created)
