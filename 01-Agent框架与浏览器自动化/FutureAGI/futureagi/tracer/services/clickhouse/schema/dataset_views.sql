-- Dataset Analytics: Dictionaries and Denormalized View

-- Fast lookup: column_id → column metadata
CREATE DICTIONARY IF NOT EXISTS column_dict (
    id UUID,
    name String,
    data_type String,
    dataset_id UUID,
    source String,
    source_id Nullable(String)
) PRIMARY KEY id
SOURCE(CLICKHOUSE(
    TABLE 'model_hub_column'
    WHERE '_peerdb_is_deleted = 0'
))
LAYOUT(COMPLEX_KEY_HASHED())
LIFETIME(MIN 30 MAX 60);

-- Fast lookup: dataset_id → dataset metadata
CREATE DICTIONARY IF NOT EXISTS dataset_dict (
    id UUID,
    name String,
    organization_id UUID,
    workspace_id UUID
) PRIMARY KEY id
SOURCE(CLICKHOUSE(
    TABLE 'model_hub_dataset'
    WHERE '_peerdb_is_deleted = 0 AND deleted = 0'
))
LAYOUT(COMPLEX_KEY_HASHED())
LIFETIME(MIN 30 MAX 60);

-- Denormalized dataset cells view with column and dataset info joined via dictionaries
CREATE VIEW IF NOT EXISTS dataset_cells AS
SELECT
    c.id,
    c.dataset_id,
    c.column_id,
    c.row_id,
    c.value,
    c.status,
    c.prompt_tokens,
    c.completion_tokens,
    c.response_time,
    c.created_at,
    c.updated_at,

    -- Column info via dictionary
    dictGet('column_dict', 'name', c.column_id) AS column_name,
    dictGet('column_dict', 'data_type', c.column_id) AS column_data_type,
    dictGet('column_dict', 'source', c.column_id) AS column_source,
    dictGet('column_dict', 'source_id', c.column_id) AS column_source_id,

    -- Dataset info via dictionary
    dictGet('dataset_dict', 'name', c.dataset_id) AS dataset_name,
    dictGet('dataset_dict', 'organization_id', c.dataset_id) AS org_id,
    dictGet('dataset_dict', 'workspace_id', c.dataset_id) AS workspace_id,

    -- Parsed numeric value (for eval scores and numeric columns)
    if(column_data_type IN ('float', 'integer') OR column_source = 'evaluation',
       toFloat64OrNull(c.value), NULL) AS value_float,

    -- Parsed boolean value (for pass/fail evals)
    if(lower(c.value) IN ('true', 'pass', 'passed', '1'), 1,
       if(lower(c.value) IN ('false', 'fail', 'failed', '0'), 0, NULL)) AS value_bool

FROM model_hub_cell AS c FINAL
WHERE c._peerdb_is_deleted = 0;
