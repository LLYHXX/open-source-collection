"""
ClickHouse Writer for Analytics Backend

Provides async dual-write capability to write spans and evaluations
to ClickHouse alongside PostgreSQL.
"""

import json
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from django.conf import settings

from tracer.services.clickhouse.client import (
    ClickHouseClient,
    get_clickhouse_client,
    is_clickhouse_enabled,
)

logger = structlog.get_logger(__name__)


@dataclass
class WriteBuffer:
    """Buffer for batching writes."""

    spans: List[Dict[str, Any]] = field(default_factory=list)
    evaluations: List[Dict[str, Any]] = field(default_factory=list)
    last_flush: float = field(default_factory=time.time)


class ClickHouseWriter:
    """
    Async writer for ClickHouse with batching and retry support.

    Features:
    - Batches writes for efficiency
    - Background thread for async writes
    - Automatic retry on failures
    - Graceful shutdown with flush

    Usage:
        writer = ClickHouseWriter()
        writer.start()

        # Write spans (non-blocking)
        writer.write_span(span_data)

        # Shutdown gracefully
        writer.stop()
    """

    def __init__(
        self,
        client: Optional[ClickHouseClient] = None,
        batch_size: Optional[int] = None,
        flush_interval: Optional[float] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
    ):
        """
        Initialize the ClickHouse writer.

        Args:
            client: ClickHouse client (uses singleton if not provided)
            batch_size: Number of records before auto-flush
            flush_interval: Seconds between auto-flushes
            max_retries: Maximum retry attempts for failed writes
            retry_delay: Delay between retries in seconds
        """
        ch_settings = getattr(settings, "CLICKHOUSE", {})

        self.client = client or get_clickhouse_client()
        self.batch_size = batch_size or ch_settings.get("CH_BATCH_SIZE", 1000)
        self.flush_interval = flush_interval or ch_settings.get(
            "CH_FLUSH_INTERVAL_SECONDS", 5
        )
        self.max_retries = max_retries or ch_settings.get("CH_MAX_RETRIES", 3)
        self.retry_delay = retry_delay or ch_settings.get("CH_RETRY_DELAY_SECONDS", 1)

        self._buffer = WriteBuffer()
        self._lock = threading.Lock()
        self._queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Metrics
        self._metrics = {
            "spans_written": 0,
            "spans_failed": 0,
            "evaluations_written": 0,
            "evaluations_failed": 0,
            "flushes": 0,
            "retries": 0,
        }

    @property
    def is_enabled(self) -> bool:
        """Check if dual-write is enabled."""
        ch_settings = getattr(settings, "CLICKHOUSE", {})
        return ch_settings.get("CH_DUAL_WRITE", False) and is_clickhouse_enabled()

    def start(self) -> None:
        """Start the background writer thread."""
        if self._running:
            return

        if not self.is_enabled:
            logger.info("ClickHouse dual-write is disabled")
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        logger.info("ClickHouse writer started")

    def stop(self, timeout: float = 10.0) -> None:
        """
        Stop the writer and flush remaining data.

        Args:
            timeout: Maximum seconds to wait for flush
        """
        if not self._running:
            return

        self._running = False

        # Signal worker to stop
        self._queue.put(None)

        # Wait for thread to finish
        if self._thread:
            self._thread.join(timeout=timeout)

        # Final flush
        self._flush_all()

        logger.info(
            "ClickHouse writer stopped",
            metrics=self._metrics,
        )

    def write_span(self, span: Dict[str, Any]) -> None:
        """
        Queue a span for writing to ClickHouse.

        This method is non-blocking and returns immediately.

        Args:
            span: Span data dictionary
        """
        if not self.is_enabled:
            return

        ch_span = self._convert_span(span)
        self._queue.put(("span", ch_span))

    def write_spans(self, spans: List[Dict[str, Any]]) -> None:
        """
        Queue multiple spans for writing.

        Args:
            spans: List of span data dictionaries
        """
        for span in spans:
            self.write_span(span)

    def write_evaluation(self, evaluation: Dict[str, Any]) -> None:
        """
        Queue an evaluation for writing to ClickHouse.

        Args:
            evaluation: Evaluation data dictionary
        """
        if not self.is_enabled:
            return

        ch_eval = self._convert_evaluation(evaluation)
        self._queue.put(("evaluation", ch_eval))

    def flush(self) -> None:
        """Force an immediate flush of buffered data."""
        self._queue.put(("flush", None))

    def get_metrics(self) -> Dict[str, int]:
        """Get writer metrics."""
        return self._metrics.copy()

    def _worker(self) -> None:
        """Background worker thread."""
        while self._running:
            try:
                # Wait for item with timeout for periodic flush
                try:
                    item = self._queue.get(timeout=self.flush_interval)
                except queue.Empty:
                    # Timeout - do periodic flush
                    self._flush_if_needed()
                    continue

                if item is None:
                    # Shutdown signal
                    break

                item_type, data = item

                if item_type == "flush":
                    self._flush_all()
                elif item_type == "span":
                    self._add_to_buffer("spans", data)
                elif item_type == "evaluation":
                    self._add_to_buffer("evaluations", data)

                self._queue.task_done()

            except Exception as e:
                logger.exception("ClickHouse writer error", error=str(e))

    def _add_to_buffer(self, buffer_type: str, data: Dict[str, Any]) -> None:
        """Add data to the appropriate buffer."""
        with self._lock:
            buffer_list = getattr(self._buffer, buffer_type)
            buffer_list.append(data)

            # Check if we should flush
            if len(buffer_list) >= self.batch_size:
                self._flush_buffer(buffer_type)

    def _flush_if_needed(self) -> None:
        """Flush if interval has elapsed."""
        with self._lock:
            elapsed = time.time() - self._buffer.last_flush
            if elapsed >= self.flush_interval:
                self._flush_all_unlocked()

    def _flush_all(self) -> None:
        """Flush all buffers (thread-safe)."""
        with self._lock:
            self._flush_all_unlocked()

    def _flush_all_unlocked(self) -> None:
        """Flush all buffers (must hold lock)."""
        if self._buffer.spans:
            self._flush_buffer("spans")
        if self._buffer.evaluations:
            self._flush_buffer("evaluations")
        self._buffer.last_flush = time.time()

    def _flush_buffer(self, buffer_type: str) -> None:
        """
        Flush a specific buffer to ClickHouse.

        Must be called with lock held.
        """
        buffer_list = getattr(self._buffer, buffer_type)
        if not buffer_list:
            return

        data = buffer_list.copy()
        buffer_list.clear()

        table = "observation_spans" if buffer_type == "spans" else "evaluation_events"
        metric_key = (
            "spans_written" if buffer_type == "spans" else "evaluations_written"
        )
        failed_key = "spans_failed" if buffer_type == "spans" else "evaluations_failed"

        for attempt in range(self.max_retries):
            try:
                self.client.insert(table, data)
                self._metrics[metric_key] += len(data)
                self._metrics["flushes"] += 1

                logger.debug(
                    "Flushed to ClickHouse",
                    table=table,
                    count=len(data),
                )
                return

            except Exception as e:
                self._metrics["retries"] += 1
                logger.warning(
                    "ClickHouse write failed, retrying",
                    table=table,
                    attempt=attempt + 1,
                    error=str(e),
                )

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))

        # All retries failed
        self._metrics[failed_key] += len(data)
        logger.error(
            "ClickHouse write failed after all retries",
            table=table,
            count=len(data),
        )

    def _convert_span(self, span: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a PostgreSQL span to ClickHouse format.

        Args:
            span: Span data from PostgreSQL/ingestion

        Returns:
            Span data formatted for ClickHouse
        """
        now = datetime.utcnow()
        return {
            "id": str(span.get("id", "")),
            "trace_id": str(span.get("trace_id", "")),
            "parent_span_id": span.get("parent_span_id"),
            "org_id": span.get("org_id") or span.get("organization_id"),
            "project_id": span.get("project_id"),
            "project_version_id": span.get("project_version_id"),
            "name": span.get("name", ""),
            "observation_type": span.get("observation_type", "unknown"),
            "operation_name": span.get("operation_name"),
            "status": span.get("status", "UNSET"),
            "start_time": self._to_datetime(span.get("start_time")),
            "end_time": self._to_datetime(span.get("end_time")),
            "latency_ms": span.get("latency_ms"),
            "model": span.get("model", ""),
            "provider": span.get("provider", ""),
            "prompt_tokens": span.get("prompt_tokens"),
            "completion_tokens": span.get("completion_tokens"),
            "total_tokens": span.get("total_tokens"),
            "cost": span.get("cost"),
            "input": json.dumps(span.get("input", {})),
            "output": json.dumps(span.get("output", {})),
            "semconv_source": span.get("semconv_source", ""),
            "schema_version": span.get("schema_version", "1.0"),
            "span_attributes": json.dumps(span.get("span_attributes", {})),
            "resource_attributes": json.dumps(span.get("resource_attributes", {})),
            "metadata": json.dumps(span.get("metadata", {})),
            "tags": (
                json.dumps(span.get("tags", []))
                if isinstance(span.get("tags"), list)
                else span.get("tags", "[]")
            ),
            "span_events": json.dumps(span.get("span_events", [])),
            "end_user_id": span.get("end_user_id"),
            "custom_eval_config_id": span.get("custom_eval_config_id"),
            "eval_id": span.get("eval_id"),
            "eval_input": json.dumps(span.get("eval_input", [])),
            "eval_attributes": json.dumps(span.get("eval_attributes", {})),
            "eval_status": span.get("eval_status"),
            "input_images": json.dumps(span.get("input_images", [])),
            "model_parameters": json.dumps(span.get("model_parameters", {})),
            "response_time": span.get("response_time"),
            "org_user_id": span.get("org_user_id"),
            "prompt_version_id": span.get("prompt_version_id"),
            "prompt_label_id": span.get("prompt_label_id"),
            "created_at": self._to_datetime(span.get("created_at")) or now,
            "updated_at": self._to_datetime(span.get("updated_at")) or now,
        }

    def _convert_evaluation(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a PostgreSQL evaluation to ClickHouse format.

        Args:
            evaluation: Evaluation data from PostgreSQL

        Returns:
            Evaluation data formatted for ClickHouse
        """
        return {
            "id": evaluation.get("id"),
            "trace_id": str(evaluation.get("trace_id", "")),
            "span_id": evaluation.get("span_id"),
            "organization_id": evaluation.get("organization_id"),
            "project_id": evaluation.get("project_id"),
            "eval_name": evaluation.get("eval_name", ""),
            "eval_type": evaluation.get("eval_type", "custom"),
            "evaluator_type": evaluation.get("evaluator_type", "unknown"),
            "score_value": evaluation.get("score_value"),
            "score_min": evaluation.get("score_min"),
            "score_max": evaluation.get("score_max"),
            "label": evaluation.get("label"),
            "passed": (
                1
                if evaluation.get("passed")
                else (0 if evaluation.get("passed") is False else None)
            ),
            "explanation": evaluation.get("explanation"),
            "evaluator_model": evaluation.get("evaluator_model"),
            "evaluator_config": json.dumps(evaluation.get("evaluator_config", {})),
            "attributes": json.dumps(evaluation.get("attributes", {})),
            "evaluated_at": self._to_datetime(evaluation.get("evaluated_at"))
            or datetime.utcnow(),
            "created_at": self._to_datetime(evaluation.get("created_at"))
            or datetime.utcnow(),
        }

    def _to_datetime(self, value) -> Optional[datetime]:
        """Convert various datetime formats to datetime object."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        if isinstance(value, (int, float)):
            # Assume nanoseconds if very large
            if value > 1e15:
                return datetime.fromtimestamp(value / 1e9)
            return datetime.fromtimestamp(value)
        return None


# Singleton instance
_clickhouse_writer: Optional[ClickHouseWriter] = None


def get_clickhouse_writer() -> ClickHouseWriter:
    """Get the singleton ClickHouse writer instance."""
    global _clickhouse_writer

    if _clickhouse_writer is None:
        _clickhouse_writer = ClickHouseWriter()

    return _clickhouse_writer


def start_clickhouse_writer() -> None:
    """Start the global ClickHouse writer."""
    writer = get_clickhouse_writer()
    writer.start()


def stop_clickhouse_writer() -> None:
    """Stop the global ClickHouse writer."""
    global _clickhouse_writer
    if _clickhouse_writer:
        _clickhouse_writer.stop()
