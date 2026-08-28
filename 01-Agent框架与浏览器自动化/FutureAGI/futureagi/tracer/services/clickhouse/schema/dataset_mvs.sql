-- Dataset Analytics: Pre-aggregated Materialized Views

-- Hourly aggregates per dataset + column
CREATE MATERIALIZED VIEW IF NOT EXISTS dataset_cell_metrics_hourly
ENGINE = SummingMergeTree
ORDER BY (org_id, workspace_id, dataset_id, column_id, hour)
POPULATE
AS SELECT
    dictGet('dataset_dict', 'organization_id', dataset_id) AS org_id,
    dictGet('dataset_dict', 'workspace_id', dataset_id) AS workspace_id,
    dataset_id,
    column_id,
    toStartOfHour(created_at) AS hour,
    count() AS cell_count,
    sumOrNull(prompt_tokens) AS total_prompt_tokens,
    sumOrNull(completion_tokens) AS total_completion_tokens,
    avgOrNull(response_time) AS avg_response_time,
    countIf(status = 'error') AS error_count,
    countIf(status = 'pass') AS pass_count
FROM model_hub_cell FINAL
WHERE _peerdb_is_deleted = 0
GROUP BY org_id, workspace_id, dataset_id, column_id, hour;

-- Hourly eval score aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS dataset_eval_metrics_hourly
ENGINE = SummingMergeTree
ORDER BY (org_id, workspace_id, dataset_id, column_source_id, hour)
POPULATE
AS SELECT
    dictGet('dataset_dict', 'organization_id', c.dataset_id) AS org_id,
    dictGet('dataset_dict', 'workspace_id', c.dataset_id) AS workspace_id,
    c.dataset_id,
    dictGet('column_dict', 'source_id', c.column_id) AS column_source_id,
    dictGet('column_dict', 'name', c.column_id) AS eval_name,
    toStartOfHour(c.created_at) AS hour,
    count() AS eval_count,
    avgOrNull(toFloat64OrNull(c.value)) AS avg_score,
    minOrNull(toFloat64OrNull(c.value)) AS min_score,
    maxOrNull(toFloat64OrNull(c.value)) AS max_score,
    countIf(lower(c.value) IN ('true', 'pass', 'passed', '1')) AS pass_count,
    countIf(lower(c.value) IN ('false', 'fail', 'failed', '0')) AS fail_count
FROM model_hub_cell AS c FINAL
WHERE c._peerdb_is_deleted = 0
  AND dictGet('column_dict', 'source', c.column_id) = 'evaluation'
GROUP BY org_id, workspace_id, c.dataset_id, column_source_id, eval_name, hour;
