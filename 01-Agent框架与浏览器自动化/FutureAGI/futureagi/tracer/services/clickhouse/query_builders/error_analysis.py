"""
Error Analysis Query Builder for ClickHouse.

Provides error count time series, error rate computation, and breakdown
by model or other dimensions.  Queries the denormalized ``spans`` table
filtered to ``status = 'ERROR'``.

Error analysis is infrequent enough that no pre-aggregation table is used.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from tracer.services.clickhouse.query_builders.base import BaseQueryBuilder
from tracer.services.clickhouse.query_builders.filters import ClickHouseFilterBuilder


class ErrorAnalysisQueryBuilder(BaseQueryBuilder):
    """Build error analysis queries.

    Supports three query modes:

    1. **Time series** (``mode="time_series"``): Error count and error rate
       per time bucket.
    2. **Breakdown** (``mode="breakdown"``): Error count grouped by a
       dimension (model, observation_type, status_message).
    3. **Summary** (``mode="summary"``): Total error count, error rate,
       and top error models for the time range.

    Args:
        project_id: Project UUID string.
        start_date: Start of the time range.
        end_date: End of the time range.
        interval: Time bucket interval (for time-series mode).
        group_by: Dimension to group by in breakdown mode.  One of
            ``"model"``, ``"observation_type"``, or ``"status_message"``.
        mode: Query mode: ``"time_series"``, ``"breakdown"``, or
            ``"summary"``.
        filters: Optional frontend filter list for additional filtering.
    """

    TABLE = "spans"

    VALID_GROUP_BY = {"model", "observation_type", "status_message", "provider", "name"}

    def __init__(
        self,
        project_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "hour",
        group_by: str = "model",
        mode: str = "time_series",
        filters: Optional[List[Dict]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(project_id, **kwargs)
        self.interval = interval
        self.group_by = group_by if group_by in self.VALID_GROUP_BY else "model"
        self.mode = mode
        self.filters = filters or []

        # Default time range
        self.end_date = end_date or datetime.utcnow()
        self.start_date = start_date or (self.end_date - timedelta(days=7))

        self.params["start_date"] = self.start_date
        self.params["end_date"] = self.end_date

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> Tuple[str, Dict[str, Any]]:
        """Build the error analysis query based on the configured mode.

        Returns:
            A ``(query_string, params)`` tuple.
        """
        # Apply any additional filters
        fb = ClickHouseFilterBuilder(table=self.TABLE)
        extra_where, extra_params = fb.translate(self.filters)
        self.params.update(extra_params)
        filter_fragment = f"AND {extra_where}" if extra_where else ""

        if self.mode == "breakdown":
            return self._build_breakdown(filter_fragment)
        elif self.mode == "summary":
            return self._build_summary(filter_fragment)
        else:
            return self._build_time_series(filter_fragment)

    def format_time_series_result(
        self,
        rows: List[Tuple],
        columns: List[str],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Format time-series query results.

        Args:
            rows: Raw rows from ClickHouse.
            columns: Column names.

        Returns:
            Dict with ``error_count`` and ``error_rate`` time-series lists.
        """

        def _get(r, key, idx, default=0):
            if isinstance(r, dict):
                return r.get(key, default)
            return r[idx] if len(r) > idx else default

        error_count_data = self.format_time_series(
            rows=[(_get(r, "time_bucket", 0), _get(r, "error_count", 1)) for r in rows],
            columns=["time_bucket", "error_count"],
            interval=self.interval,
            start_date=self.start_date,
            end_date=self.end_date,
            value_keys=["error_count"],
        )

        error_rate_data = self.format_time_series(
            rows=[(_get(r, "time_bucket", 0), _get(r, "error_rate", 3)) for r in rows],
            columns=["time_bucket", "error_rate"],
            interval=self.interval,
            start_date=self.start_date,
            end_date=self.end_date,
            value_keys=["error_rate"],
        )

        return {
            "error_count": error_count_data,
            "error_rate": error_rate_data,
        }

    @staticmethod
    def format_breakdown_result(
        rows: List[Tuple],
        columns: List[str],
    ) -> List[Dict[str, Any]]:
        """Format breakdown query results.

        Args:
            rows: Raw rows from ClickHouse.
            columns: Column names.

        Returns:
            List of dicts with the group-by dimension and counts.
        """
        col_idx = {name: i for i, name in enumerate(columns)}
        results: List[Dict[str, Any]] = []

        for row in rows:
            entry: Dict[str, Any] = {}
            for col_name, idx in col_idx.items():
                if isinstance(row, dict):
                    val = row.get(col_name, None)
                else:
                    val = row[idx]
                if isinstance(val, float):
                    val = round(val, 4)
                entry[col_name] = val
            results.append(entry)

        return results

    @staticmethod
    def format_summary_result(
        rows: List[Tuple],
        columns: List[str],
    ) -> Dict[str, Any]:
        """Format summary query results.

        Args:
            rows: Raw rows (single row expected).
            columns: Column names.

        Returns:
            Summary dict with total_errors, total_spans, and error_rate.
        """
        if not rows:
            return {
                "total_errors": 0,
                "total_spans": 0,
                "error_rate": 0.0,
            }

        col_idx = {name: i for i, name in enumerate(columns)}
        row = rows[0]
        if isinstance(row, dict):
            total_errors = row.get("total_errors", 0) or 0
            total_spans = row.get("total_spans", 0) or 0
            error_rate = row.get("error_rate", 0.0) or 0.0
        else:
            total_errors_idx = col_idx.get("total_errors")
            total_spans_idx = col_idx.get("total_spans")
            error_rate_idx = col_idx.get("error_rate")
            if (
                total_errors_idx is None
                or total_spans_idx is None
                or error_rate_idx is None
            ):
                return {
                    "total_errors": 0,
                    "total_spans": 0,
                    "error_rate": 0.0,
                }
            total_errors = row[total_errors_idx] or 0
            total_spans = row[total_spans_idx] or 0
            error_rate = row[error_rate_idx] or 0.0

        return {
            "total_errors": int(total_errors),
            "total_spans": int(total_spans),
            "error_rate": round(float(error_rate), 4),
        }

    # ------------------------------------------------------------------
    # Private query builders
    # ------------------------------------------------------------------

    def _build_time_series(self, filter_fragment: str) -> Tuple[str, Dict[str, Any]]:
        """Error count and error rate per time bucket."""
        bucket_fn = self.time_bucket_expr(self.interval)

        query = f"""
        SELECT
            {bucket_fn}(start_time) AS time_bucket,
            countIf(status = 'ERROR') AS error_count,
            count() AS total_count,
            countIf(status = 'ERROR') * 100.0 / greatest(count(), 1)
                AS error_rate
        FROM {self.TABLE}
        {self.project_where()}
          AND start_time >= %(start_date)s
          AND start_time < %(end_date)s
          {filter_fragment}
        GROUP BY time_bucket
        ORDER BY time_bucket
        """
        return query, self.params

    def _build_breakdown(self, filter_fragment: str) -> Tuple[str, Dict[str, Any]]:
        """Error count grouped by a dimension, only for error spans."""
        query = f"""
        SELECT
            {self.group_by} AS dimension,
            count() AS error_count,
            uniqExact(trace_id) AS affected_traces
        FROM {self.TABLE}
        {self.project_where()}
          AND status = 'ERROR'
          AND start_time >= %(start_date)s
          AND start_time < %(end_date)s
          {filter_fragment}
        GROUP BY {self.group_by}
        ORDER BY error_count DESC
        LIMIT 50
        """
        return query, self.params

    def _build_summary(self, filter_fragment: str) -> Tuple[str, Dict[str, Any]]:
        """Total error count, total span count, and error rate."""
        query = f"""
        SELECT
            countIf(status = 'ERROR') AS total_errors,
            count() AS total_spans,
            countIf(status = 'ERROR') * 100.0 / greatest(count(), 1)
                AS error_rate
        FROM {self.TABLE}
        {self.project_where()}
          AND start_time >= %(start_date)s
          AND start_time < %(end_date)s
          {filter_fragment}
        """
        return query, self.params
