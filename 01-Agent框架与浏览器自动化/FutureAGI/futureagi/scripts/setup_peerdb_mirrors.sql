-- =============================================================================
-- DEPRECATED: Use scripts/peerdb-setup-mirrors.sh instead.
-- This SQL file is kept for reference only. The shell script supports
-- environment-variable configuration, initial snapshots, and differentiated
-- sync intervals for dimension vs fact tables.
-- =============================================================================
--
-- =============================================================================
-- PeerDB Mirror Setup for CDC Replication (PostgreSQL -> ClickHouse)
-- =============================================================================
--
-- PeerDB provides Change Data Capture (CDC) from PostgreSQL to ClickHouse.
-- It reads the PostgreSQL WAL (Write-Ahead Log) via logical replication and
-- streams changes to ClickHouse in near real-time.
--
-- Prerequisites:
--   1. PostgreSQL configured with wal_level=logical
--   2. Publication created (see setup_pg_replication.sql)
--   3. PeerDB running and accessible (default SQL interface on port 9900)
--   4. ClickHouse instance running and accessible
--
-- Connect to PeerDB's SQL interface to run these commands:
--   psql -h <peerdb-host> -p 9900 -U peerdb
--
-- =============================================================================

-- Step 1: Create the PostgreSQL peer (source)
-- Replace placeholders with actual connection details.
CREATE PEER pg_source FROM POSTGRES WITH (
    host = '{{PG_HOST}}',
    port = '{{PG_PORT}}',
    user = '{{PG_USER}}',
    password = '{{PG_PASSWORD}}',
    database = '{{PG_DATABASE}}'
);

-- Step 2: Create the ClickHouse peer (destination)
-- Replace placeholders with actual connection details.
CREATE PEER ch_destination FROM CLICKHOUSE WITH (
    host = '{{CH_HOST}}',
    port = '{{CH_PORT}}',
    user = '{{CH_USER}}',
    password = '{{CH_PASSWORD}}',
    database = '{{CH_DATABASE}}'
);

-- Step 3: Create CDC mirrors for each table
-- Each mirror replicates a single PostgreSQL table to ClickHouse.
-- PeerDB adds metadata columns:
--   _peerdb_synced_at  - timestamp when the row was last synced
--   _peerdb_is_deleted - soft-delete flag (0=active, 1=deleted)
--   _peerdb_version    - version counter for deduplication

-- Mirror: tracer_observation_span
CREATE MIRROR mirror_observation_span
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.tracer_observation_span : tracer_observation_span
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 10
);

-- Mirror: tracer_trace
CREATE MIRROR mirror_trace
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.tracer_trace : tracer_trace
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 10
);

-- Mirror: trace_session
CREATE MIRROR mirror_trace_session
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.trace_session : trace_session
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 10
);

-- Mirror: tracer_eval_logger
CREATE MIRROR mirror_eval_logger
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.tracer_eval_logger : tracer_eval_logger
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 10
);

-- =============================================================================
-- Simulation CDC Mirrors
-- =============================================================================

-- Mirror: simulate_test_execution
CREATE MIRROR mirror_simulate_test_execution
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.simulate_test_execution : simulate_test_execution
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 10
);

-- Mirror: simulate_call_execution
CREATE MIRROR mirror_simulate_call_execution
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.simulate_call_execution : simulate_call_execution
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 10
);

-- Mirror: simulate_scenarios (dimension table for dictionaries)
CREATE MIRROR mirror_simulate_scenarios
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.simulate_scenarios : simulate_scenarios
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 30
);

-- Mirror: simulate_agent_definition (dimension table for dictionaries)
CREATE MIRROR mirror_simulate_agent_definition
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.simulate_agent_definition : simulate_agent_definition
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 30
);

-- Mirror: simulate_agent_version (dimension table for dictionaries)
CREATE MIRROR mirror_simulate_agent_version
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.simulate_agent_version : simulate_agent_version
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 30
);

-- Mirror: simulate_run_test (dimension table for dictionaries)
CREATE MIRROR mirror_simulate_run_test
FROM pg_source TO ch_destination
WITH TABLE MAPPING (
    public.simulate_run_test : simulate_run_test
)
WITH (
    publication_name = 'peerdb_publication',
    do_initial_snapshot = true,
    snapshot_num_rows_per_partition = 500000,
    snapshot_max_parallel_workers = 4,
    snapshot_num_tables_in_parallel = 1,
    soft_delete = true,
    sync_interval = 30
);

-- =============================================================================
-- Verification Commands (run after mirrors are created)
-- =============================================================================
--
-- Check mirror status:
--   SELECT * FROM peerdb.mirrors;
--
-- Check mirror activity:
--   SELECT * FROM peerdb.mirror_stats;
--
-- Pause a mirror:
--   ALTER MIRROR mirror_observation_span PAUSE;
--
-- Resume a mirror:
--   ALTER MIRROR mirror_observation_span RESUME;
--
-- Drop a mirror (stops replication):
--   DROP MIRROR mirror_observation_span;
-- =============================================================================
