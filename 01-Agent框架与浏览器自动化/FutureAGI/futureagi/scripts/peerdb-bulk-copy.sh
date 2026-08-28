#!/bin/bash
# =============================================================================
# PeerDB Hybrid Initial Copy — Bulk copy PG → CH with progressive fallback
#
# Replaces PeerDB's unreliable snapshot with a direct, chunked bulk copy.
# Designed to run AFTER PeerDB mirrors are created (CDC-only mode) so the
# replication slot captures all WAL changes during the copy.
#
# Works in three modes:
#   Docker Compose (local dev):
#     CH_MODE=docker ./scripts/peerdb-bulk-copy.sh
#
#   Kubernetes (production):
#     CH_MODE=k8s \
#     K8S_NAMESPACE=application \
#     K8S_CH_POD=chi-futureagi-clickhouse-cluster-cluster-0-0-0 \
#     ./scripts/peerdb-bulk-copy.sh
#
#   Direct (standalone — clickhouse-client and psql available locally):
#     CH_MODE=direct \
#     CH_HOST=localhost CH_PORT=9000 \
#     PG_HOST=db.example.com PG_PORT=5432 PG_USER=user PG_PASSWORD=pass PG_DB=mydb \
#     ./scripts/peerdb-bulk-copy.sh
#
# Copy strategy (progressive fallback):
#   1. INSERT INTO ... SELECT FROM postgresql() — fastest, but buffers entire
#      result via libpq. Works for chunks that fit in CH memory.
#   2. On OOM (exit code 241): automatically falls back to pipe mode —
#      psql COPY TO STDOUT | clickhouse-client INSERT FORMAT CSV
#      This streams data without buffering, never OOMs, handles any data size.
#   3. For tables with large JSON columns (e.g. tracer_observation_span):
#      Uses daily chunking, auto-escalates to hourly if daily OOMs,
#      then falls back to pipe mode for individual hours that still fail.
#
# The script:
#   1. Queries PG information_schema for each table's column list
#   2. Detaches heavy materialized views (if configured) to save memory
#   3. Copies data with progressive fallback (postgresql() → pipe)
#   4. Sets _peerdb_version=0 so CDC updates (version>=1) always win
#   5. Kills zombie CH queries on OOM to free memory before retry
#   6. Reattaches materialized views and backfills them
#   7. Verifies row counts with uniqExact(id) after each table
# =============================================================================

set -euo pipefail

# ─── Configuration ───────────────────────────────────────────────────────────

CH_MODE="${CH_MODE:-docker}"  # "docker", "k8s", or "direct"

# PostgreSQL source (for psql — runs on the host machine)
PG_HOST="${PG_HOST:-db}"
PG_PORT="${PG_PORT:-5432}"
PG_USER="${PG_USER:-user}"
PG_PASSWORD="${PG_PASSWORD:-password}"
PG_DB="${PG_DB:-tfc}"

# PostgreSQL as seen from CH pod (for CH's postgresql() function).
# In k8s mode, CH pod uses k8s-internal DNS (e.g. pgbouncer-service:6432)
# while psql on the host uses port-forward (e.g. localhost:16432).
PG_HOST_CH="${PG_HOST_CH:-$PG_HOST}"
PG_PORT_CH="${PG_PORT_CH:-$PG_PORT}"

# ClickHouse destination
CH_HOST="${CH_HOST:-clickhouse}"
CH_PORT="${CH_PORT:-9000}"
CH_USER="${CH_USER:-default}"
CH_PASSWORD="${CH_PASSWORD:-}"

# Docker mode
CH_CONTAINER="${CH_CONTAINER:-}"
PG_CONTAINER="${PG_CONTAINER:-}"

# K8s mode
K8S_NAMESPACE="${K8S_NAMESPACE:-application}"
K8S_CH_POD="${K8S_CH_POD:-}"

# Chunking: tables with more than this many rows get chunked
CHUNK_THRESHOLD="${CHUNK_THRESHOLD:-200000}"

# Tables with large JSON columns that need daily (not monthly) chunking
# to avoid ClickHouse OOM on big INSERT blocks
DAILY_CHUNK_TABLES="tracer_observation_span"

# Timeouts for large copies (seconds)
CH_SEND_TIMEOUT="${CH_SEND_TIMEOUT:-7200}"
CH_RECEIVE_TIMEOUT="${CH_RECEIVE_TIMEOUT:-7200}"

# PG statement_timeout for bulk reads (default 2h, prevents PG from killing long queries)
PG_STATEMENT_TIMEOUT="${PG_STATEMENT_TIMEOUT:-7200000}"

# Retry settings per chunk
MAX_CHUNK_RETRIES="${MAX_CHUNK_RETRIES:-3}"

# Skip tables (comma-separated, for resuming partial runs)
SKIP_TABLES="${SKIP_TABLES:-}"

# Pipe mode batch size (rows per psql COPY batch)
# Smaller = less memory, slower. 500 is safe for tables with large JSON columns.
PIPE_BATCH_SIZE="${PIPE_BATCH_SIZE:-500}"

# Materialized views to detach during bulk copy (comma-separated "db.mv_name" entries)
# These heavy MVs consume significant memory processing JSON during inserts.
# They are detached before copy and reattached + backfilled after.
DETACH_MVS="${DETACH_MVS:-}"

# Whether CH uses replicated database engine (requires DETACH TABLE ... PERMANENTLY)
CH_REPLICATED="${CH_REPLICATED:-true}"

# ─── Table definitions ──────────────────────────────────────────────────────
# Format: "pg_table:ch_table:type"
# type = "fact" (10s sync) or "dim" (30s sync)

ALL_TABLES=(
    # Fact tables
    "tracer_observation_span:tracer_observation_span:fact"
    "tracer_trace:tracer_trace:fact"
    "tracer_eval_logger:tracer_eval_logger:fact"
    "trace_annotation:trace_annotation:fact"
    "model_hub_score:model_hub_score:fact"
    "trace_session:trace_session:fact"
    "model_hub_dataset:model_hub_dataset:fact"
    "model_hub_column:model_hub_column:fact"
    "model_hub_row:model_hub_row:fact"
    "model_hub_cell:model_hub_cell:fact"
    "simulate_test_execution:simulate_test_execution:fact"
    "simulate_call_execution:simulate_call_execution:fact"
    "usage_apicalllog:usage_apicalllog:fact"
    # Dimension tables
    "simulate_scenarios:simulate_scenarios:dim"
    "simulate_agent_definition:simulate_agent_definition:dim"
    "simulate_agent_version:simulate_agent_version:dim"
    "simulate_run_test:simulate_run_test:dim"
    "model_hub_promptversion:model_hub_promptversion:dim"
    "model_hub_prompttemplate:model_hub_prompttemplate:dim"
    "model_hub_promptlabel:model_hub_promptlabel:dim"
    "tracer_enduser:tracer_enduser:dim"
)

# Track failed chunks for pipe-mode retry
PIPE_RETRY_QUEUE=()

# ─── Logging ─────────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; }
step() { echo -e "\n${CYAN}==>${NC} $1"; }

# ─── Helpers ─────────────────────────────────────────────────────────────────

run_ch_query() {
    local query="$1"
    local timeout="${2:-$CH_SEND_TIMEOUT}"

    if [ "$CH_MODE" = "direct" ]; then
        clickhouse-client --host "$CH_HOST" --port "$CH_PORT" \
            --user "$CH_USER" --password "$CH_PASSWORD" \
            --send_timeout "$timeout" --receive_timeout "$timeout" \
            --max_insert_block_size 50000 \
            --query "$query"
    elif [ "$CH_MODE" = "k8s" ]; then
        kubectl -n "$K8S_NAMESPACE" exec "$K8S_CH_POD" -- \
            clickhouse-client --user "$CH_USER" --password "$CH_PASSWORD" \
            --send_timeout "$timeout" --receive_timeout "$timeout" \
            --max_insert_block_size 50000 \
            --query "$query"
    else
        docker exec "$CH_CONTAINER" clickhouse-client \
            --user "$CH_USER" --password "$CH_PASSWORD" \
            --send_timeout "$timeout" --receive_timeout "$timeout" \
            --max_insert_block_size 50000 \
            --query "$query"
    fi
}

# Build psql connection URI with URL-encoded special characters
_pg_connstr() {
    local encoded_pass
    encoded_pass=$(python3 -c "import urllib.parse; print(urllib.parse.quote('${PG_PASSWORD}', safe=''))" 2>/dev/null || echo "$PG_PASSWORD")
    echo "postgresql://${PG_USER}:${encoded_pass}@${PG_HOST}:${PG_PORT}/${PG_DB}"
}

# Run a query directly against PG via psql (no libpq buffering).
# Falls back to CH's postgresql() function if psql is not available.
run_pg_query() {
    local query="$1"

    if [ "$CH_MODE" = "docker" ]; then
        docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -t -A -c "$query"
        return
    fi

    # For k8s/direct: prefer psql if available (avoids libpq memory buffering)
    if command -v psql &>/dev/null; then
        psql "$(_pg_connstr)" -t -A -c "$query"
    else
        # Fallback: query PG through CH's postgresql() table function
        run_ch_query "$query" 60
    fi
}

pg_conn_string() {
    echo "'${PG_HOST_CH}:${PG_PORT_CH}', '${PG_DB}', '${1}', '${PG_USER}', '${PG_PASSWORD}'"
}

# Kill zombie CH queries for a table that may be consuming memory after OOM.
# Failed postgresql() queries can leave libpq connections open, eating GBs of RAM.
kill_zombie_queries() {
    local table="$1"
    warn "Killing zombie CH queries for ${table}..."
    run_ch_query "KILL QUERY WHERE query LIKE '%${table}%' AND query NOT LIKE '%system.processes%' AND elapsed > 10 SYNC" 30 2>/dev/null || true
    sleep 2
}

# Set PG statement_timeout for the bulk copy user (prevents PG from killing long queries).
# Uses ALTER ROLE so the timeout persists across connections (the postgresql() table function
# creates its own PG connection, so session-level SET would have no effect).
set_pg_timeout() {
    step "Setting PG statement_timeout to ${PG_STATEMENT_TIMEOUT}ms for user ${PG_USER}..."
    if [ "$CH_MODE" = "docker" ]; then
        docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -c \
            "ALTER ROLE ${PG_USER} SET statement_timeout = '${PG_STATEMENT_TIMEOUT}ms'" 2>/dev/null || {
            warn "Could not ALTER ROLE — ensure PG user has sufficient privileges"
            warn "Falling back: bulk copy may fail if PG kills long-running queries"
        }
        log "PG statement_timeout set via ALTER ROLE"
    elif command -v psql &>/dev/null; then
        psql "$(_pg_connstr)" -c \
            "ALTER ROLE ${PG_USER} SET statement_timeout = '${PG_STATEMENT_TIMEOUT}ms'" 2>/dev/null || {
            warn "Could not ALTER ROLE — ensure PG user has sufficient privileges"
        }
        log "PG statement_timeout set via psql"
    else
        warn "Non-docker mode without psql: ensure PG user has statement_timeout >= ${PG_STATEMENT_TIMEOUT}ms"
        warn "Run: ALTER ROLE ${PG_USER} SET statement_timeout = '${PG_STATEMENT_TIMEOUT}ms'"
    fi
}

# Reset PG statement_timeout back to default after copy
reset_pg_timeout() {
    step "Resetting PG statement_timeout to default for user ${PG_USER}..."
    if [ "$CH_MODE" = "docker" ]; then
        docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -c \
            "ALTER ROLE ${PG_USER} RESET statement_timeout" 2>/dev/null || true
        log "PG statement_timeout reset to default"
    elif command -v psql &>/dev/null; then
        psql "$(_pg_connstr)" -c \
            "ALTER ROLE ${PG_USER} RESET statement_timeout" 2>/dev/null || true
        log "PG statement_timeout reset via psql"
    else
        warn "Non-docker mode: remember to reset PG timeout manually:"
        warn "Run: ALTER ROLE ${PG_USER} RESET statement_timeout"
    fi
}

# Get PG column list for a table (excludes CH-only columns)
get_pg_columns() {
    local table="$1"

    if [ "$CH_MODE" = "docker" ]; then
        run_pg_query "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '${table}' ORDER BY ordinal_position"
    elif command -v psql &>/dev/null; then
        psql "$(_pg_connstr)" -t -A -c "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '${table}' ORDER BY ordinal_position"
    else
        # Fallback: query via CH's postgresql() against information_schema
        run_ch_query "SELECT name FROM postgresql($(pg_conn_string 'information_schema.columns')) WHERE table_schema = 'public' AND table_name = '${table}' ORDER BY ordinal_position" 30
    fi
}

# Get PG row count — prefers psql to avoid libpq buffering via postgresql()
get_pg_count() {
    local table="$1"
    run_pg_query "SELECT count(*) FROM ${table}"
}

# Get PG row count for a time range
get_pg_count_range() {
    local table="$1"
    local ts_start="$2"
    local ts_end="$3"
    run_pg_query "SELECT count(*) FROM ${table} WHERE created_at >= '${ts_start}' AND created_at < '${ts_end}'"
}

# Get CH unique row count
get_ch_unique_count() {
    local table="$1"
    run_ch_query "SELECT uniqExact(id) FROM ${table}" 120
}

# Get date range for chunking
get_date_range() {
    local table="$1"
    run_pg_query "SELECT min(created_at)::text || '|' || max(created_at)::text FROM ${table}"
}

# Check if table should be skipped
should_skip() {
    local table="$1"
    if [ -n "$SKIP_TABLES" ]; then
        echo "$SKIP_TABLES" | tr ',' '\n' | grep -qx "$table" && return 0
    fi
    return 1
}

# ─── Materialized View Management ───────────────────────────────────────────
# Heavy MVs (e.g. spans_mv with JSON parsing: arrayFilter/arrayMap/JSONExtractFloat)
# consume massive memory during inserts. Detach them before bulk copy, reattach after.

detach_materialized_views() {
    if [ -z "$DETACH_MVS" ]; then
        return
    fi

    step "Detaching materialized views to save memory during bulk copy..."
    local IFS=','
    for mv in $DETACH_MVS; do
        mv=$(echo "$mv" | tr -d ' ')
        if [ "$CH_REPLICATED" = "true" ]; then
            # Replicated databases require PERMANENTLY keyword
            if run_ch_query "DETACH TABLE ${mv} PERMANENTLY" 2>/dev/null; then
                log "Detached ${mv} (permanently)"
            else
                warn "Could not detach ${mv} — it may not exist or is already detached"
            fi
        else
            if run_ch_query "DETACH TABLE ${mv}" 2>/dev/null; then
                log "Detached ${mv}"
            else
                warn "Could not detach ${mv}"
            fi
        fi
    done
}

reattach_materialized_views() {
    if [ -z "$DETACH_MVS" ]; then
        return
    fi

    step "Reattaching materialized views..."
    local IFS=','
    for mv in $DETACH_MVS; do
        mv=$(echo "$mv" | tr -d ' ')
        if run_ch_query "ATTACH TABLE ${mv}" 2>/dev/null; then
            log "Reattached ${mv}"
        else
            warn "Could not reattach ${mv} — run manually: ATTACH TABLE ${mv}"
        fi
    done
}

# ─── Copy Functions ──────────────────────────────────────────────────────────

# Generate monthly date boundaries between two years
generate_month_boundaries() {
    local start_year="$1"
    local start_month="$2"
    local end_year="$3"
    local end_month="$4"

    local y=$start_year
    local m=$start_month

    while [ "$y" -lt "$end_year" ] || ([ "$y" -eq "$end_year" ] && [ "$m" -le "$end_month" ]); do
        printf "%04d-%02d-01\n" "$y" "$m"
        m=$((m + 1))
        if [ "$m" -gt 12 ]; then
            m=1
            y=$((y + 1))
        fi
    done

    # Add one month past the end for the final boundary
    m=$((end_month + 1))
    y=$end_year
    if [ "$m" -gt 12 ]; then
        m=1
        y=$((y + 1))
    fi
    printf "%04d-%02d-01\n" "$y" "$m"
}

# Generate daily date boundaries between two dates
generate_day_boundaries() {
    local min_date="$1"
    local max_date="$2"

    local current="$min_date"
    while [[ "$current" < "$max_date" ]] || [[ "$current" == "$max_date" ]]; do
        echo "$current"
        current=$(date -d "$current + 1 day" +%Y-%m-%d 2>/dev/null || \
                  date -j -v+1d -f "%Y-%m-%d" "$current" +%Y-%m-%d)
    done

    # Add one day past the end for the final boundary
    echo "$(date -d "$max_date + 2 days" +%Y-%m-%d 2>/dev/null || \
            date -j -v+2d -f "%Y-%m-%d" "$max_date" +%Y-%m-%d)"
}

# Generate hourly boundaries for a single day
generate_hour_boundaries() {
    local day="$1"
    local next_day
    next_day=$(date -d "$day + 1 day" +%Y-%m-%d 2>/dev/null || \
               date -j -v+1d -f "%Y-%m-%d" "$day" +%Y-%m-%d)

    for hour in $(seq 0 23); do
        printf "%s %02d:00:00\n" "$day" "$hour"
    done
    echo "${next_day} 00:00:00"
}

needs_daily_chunking() {
    local table="$1"
    echo "$DAILY_CHUNK_TABLES" | tr ',' '\n' | grep -qx "$table"
}

# Build PG SELECT columns with boolean casting for pipe mode.
# PG booleans (true/false, t/f) must become integers (1/0) for CH UInt8 columns.
build_pg_select_cols() {
    local columns="$1"
    local result=""
    while IFS= read -r col; do
        [ -z "$col" ] && continue
        case "$col" in
            deleted|_peerdb_is_deleted)
                result="${result}${col}::int, "
                ;;
            *)
                result="${result}${col}, "
                ;;
        esac
    done <<< "$columns"
    # Append peerdb meta columns
    result="${result}now(), 0, 0"
    echo "$result"
}

# ─── Pipe-based copy (psql COPY | clickhouse-client) ────────────────────────
# Streams data from PG → CH without buffering. Never OOMs regardless of data size.
# Uses LIMIT/OFFSET on the PG side (pushed down by PG, unlike CH's postgresql()).
# Handles boolean casting and NULL representation for CH compatibility.

copy_chunk_pipe() {
    local pg_table="$1"
    local ch_table="$2"
    local columns="$3"
    local ts_start="$4"
    local ts_end="$5"
    local label="$6"

    if ! command -v psql &>/dev/null; then
        err "Pipe mode requires psql — install postgresql-client"
        return 1
    fi

    local insert_cols
    insert_cols=$(echo "$columns" | tr '\n' ', ' | sed 's/,$//')
    insert_cols="${insert_cols}, _peerdb_synced_at, _peerdb_is_deleted, _peerdb_version"

    local select_cols
    select_cols=$(build_pg_select_cols "$columns")

    # Get PG count for this range
    local pg_count
    pg_count=$(get_pg_count_range "$pg_table" "$ts_start" "$ts_end" 2>/dev/null | tr -d '[:space:]')

    if [ -z "$pg_count" ] || [ "$pg_count" = "0" ]; then
        echo "    ${label}: 0 rows, skip"
        return 0
    fi

    echo "    ${label}: ${pg_count} PG rows (pipe mode, batch=${PIPE_BATCH_SIZE})"

    local offset=0
    local batch_num=0
    local consec_fail=0
    local connstr
    connstr=$(_pg_connstr)

    while [ "$offset" -lt "$pg_count" ]; do
        batch_num=$((batch_num + 1))
        local batch_ok=false

        for retry in 1 2 3; do
            # psql COPY streams from PG; pipe to clickhouse-client INSERT
            if [ "$CH_MODE" = "k8s" ]; then
                psql "$connstr" -c "COPY (SELECT ${select_cols} FROM ${pg_table} WHERE created_at >= '${ts_start}' AND created_at < '${ts_end}' ORDER BY id LIMIT ${PIPE_BATCH_SIZE} OFFSET ${offset}) TO STDOUT WITH (FORMAT csv, NULL '\N')" 2>/dev/null | \
                kubectl -n "$K8S_NAMESPACE" exec -i "$K8S_CH_POD" -- clickhouse-client \
                    --user "$CH_USER" --password "$CH_PASSWORD" \
                    --input_format_csv_empty_as_default 1 \
                    --date_time_input_format best_effort \
                    --input_format_null_as_default 1 \
                    --input_format_csv_use_default_on_bad_values 1 \
                    --query "INSERT INTO ${ch_table} (${insert_cols}) FORMAT CSV" 2>/dev/null
            elif [ "$CH_MODE" = "direct" ]; then
                psql "$connstr" -c "COPY (SELECT ${select_cols} FROM ${pg_table} WHERE created_at >= '${ts_start}' AND created_at < '${ts_end}' ORDER BY id LIMIT ${PIPE_BATCH_SIZE} OFFSET ${offset}) TO STDOUT WITH (FORMAT csv, NULL '\N')" 2>/dev/null | \
                clickhouse-client --host "$CH_HOST" --port "$CH_PORT" \
                    --user "$CH_USER" --password "$CH_PASSWORD" \
                    --input_format_csv_empty_as_default 1 \
                    --date_time_input_format best_effort \
                    --input_format_null_as_default 1 \
                    --input_format_csv_use_default_on_bad_values 1 \
                    --query "INSERT INTO ${ch_table} (${insert_cols}) FORMAT CSV" 2>/dev/null
            else
                # Docker mode: pipe through docker exec
                docker exec "$PG_CONTAINER" psql -U "$PG_USER" -d "$PG_DB" -c "COPY (SELECT ${select_cols} FROM ${pg_table} WHERE created_at >= '${ts_start}' AND created_at < '${ts_end}' ORDER BY id LIMIT ${PIPE_BATCH_SIZE} OFFSET ${offset}) TO STDOUT WITH (FORMAT csv, NULL '\N')" 2>/dev/null | \
                docker exec -i "$CH_CONTAINER" clickhouse-client \
                    --user "$CH_USER" --password "$CH_PASSWORD" \
                    --input_format_csv_empty_as_default 1 \
                    --date_time_input_format best_effort \
                    --input_format_null_as_default 1 \
                    --input_format_csv_use_default_on_bad_values 1 \
                    --query "INSERT INTO ${ch_table} (${insert_cols}) FORMAT CSV" 2>/dev/null
            fi

            # Check the clickhouse-client exit code (second in pipe)
            if [ "${PIPESTATUS[1]:-1}" -eq 0 ]; then
                batch_ok=true
                break
            else
                echo "      B${batch_num} fail attempt ${retry}"
                sleep 5
            fi
        done

        if [ "$batch_ok" = "false" ]; then
            consec_fail=$((consec_fail + 1))
            echo "      SKIP B${batch_num} (offset ${offset})"
            if [ "$consec_fail" -ge 5 ]; then
                err "    ${label}: too many consecutive failures, aborting"
                return 1
            fi
            offset=$((offset + PIPE_BATCH_SIZE))
            continue
        fi

        consec_fail=0
        offset=$((offset + PIPE_BATCH_SIZE))

        # Progress every 20 batches
        if [ $((batch_num % 20)) -eq 0 ]; then
            echo "      B${batch_num}: ${offset}/${pg_count} ($(date '+%H:%M:%S'))"
        fi
    done

    log "    ${label}: ~${pg_count} rows piped ($(date '+%H:%M:%S'))"
}

copy_table_single() {
    local pg_table="$1"
    local ch_table="$2"
    local columns="$3"

    step "Copying ${pg_table} (single batch)..."

    local insert_cols
    insert_cols=$(echo "$columns" | tr '\n' ', ' | sed 's/,$//')
    insert_cols="${insert_cols}, _peerdb_synced_at, _peerdb_is_deleted, _peerdb_version"

    local select_cols
    select_cols=$(echo "$columns" | tr '\n' ', ' | sed 's/,$//')
    select_cols="${select_cols}, now64(), false, 0"

    if run_ch_query "INSERT INTO ${ch_table} (${insert_cols}) SELECT ${select_cols} FROM postgresql($(pg_conn_string "${pg_table}"))" 2>&1; then
        log "${pg_table} copy complete"
        return 0
    fi

    # OOM fallback: try pipe mode for the entire table
    warn "${pg_table}: postgresql() failed, falling back to pipe mode..."
    kill_zombie_queries "$pg_table"

    local min_date max_date
    local date_info
    date_info=$(get_date_range "$pg_table" 2>/dev/null)
    min_date=$(echo "$date_info" | cut -d'|' -f1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    max_date=$(echo "$date_info" | cut -d'|' -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    if [ -n "$min_date" ] && [ -n "$max_date" ]; then
        copy_chunk_pipe "$pg_table" "$ch_table" "$columns" "$min_date" "$max_date" "full-table"
    else
        # No date range — pipe the whole table with a wide range
        copy_chunk_pipe "$pg_table" "$ch_table" "$columns" "1970-01-01" "2100-01-01" "full-table"
    fi
}

copy_table_chunked() {
    local pg_table="$1"
    local ch_table="$2"
    local columns="$3"

    local chunk_mode="monthly"
    if needs_daily_chunking "$pg_table"; then
        chunk_mode="daily"
    fi

    step "Copying ${pg_table} (chunked ${chunk_mode})..."

    local insert_cols
    insert_cols=$(echo "$columns" | tr '\n' ', ' | sed 's/,$//')
    insert_cols="${insert_cols}, _peerdb_synced_at, _peerdb_is_deleted, _peerdb_version"

    local select_cols
    select_cols=$(echo "$columns" | tr '\n' ', ' | sed 's/,$//')
    select_cols="${select_cols}, now64(), false, 0"

    # Get date range
    local date_info
    date_info=$(get_date_range "$pg_table")

    local min_date max_date
    min_date=$(echo "$date_info" | cut -d'|' -f1 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    max_date=$(echo "$date_info" | cut -d'|' -f2 | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    local boundaries boundary_array
    if [ "$chunk_mode" = "daily" ]; then
        local start_date end_date
        start_date=$(echo "$min_date" | cut -d' ' -f1)
        end_date=$(echo "$max_date" | cut -d' ' -f1)
        boundaries=$(generate_day_boundaries "$start_date" "$end_date")
    else
        local start_year start_month end_year end_month
        start_year=$(echo "$min_date" | cut -d'-' -f1)
        start_month=$(echo "$min_date" | cut -d'-' -f2 | sed 's/^0//')
        end_year=$(echo "$max_date" | cut -d'-' -f1)
        end_month=$(echo "$max_date" | cut -d'-' -f2 | sed 's/^0//')
        boundaries=$(generate_month_boundaries "$start_year" "$start_month" "$end_year" "$end_month")
    fi
    readarray -t boundary_array <<< "$boundaries"

    local total_chunks=$(( ${#boundary_array[@]} - 1 ))
    local failed_chunks=0

    for ((i=0; i<total_chunks; i++)); do
        local chunk_start="${boundary_array[$i]}"
        local chunk_end="${boundary_array[$((i+1))]}"
        local chunk_num=$((i + 1))
        local chunk_ok=false

        for ((retry=1; retry<=MAX_CHUNK_RETRIES; retry++)); do
            echo "  Chunk ${chunk_num}/${total_chunks}: ${chunk_start} to ${chunk_end} ($(date '+%H:%M:%S'))$([ "$retry" -gt 1 ] && echo " [retry ${retry}/${MAX_CHUNK_RETRIES}]")"

            if run_ch_query "INSERT INTO ${ch_table} (${insert_cols}) SELECT ${select_cols} FROM postgresql($(pg_conn_string "${pg_table}")) WHERE created_at >= '${chunk_start}' AND created_at < '${chunk_end}'" 2>&1; then
                echo "  Chunk ${chunk_num} done ($(date '+%H:%M:%S'))"
                chunk_ok=true
                break
            else
                warn "Chunk ${chunk_num} failed (attempt ${retry}/${MAX_CHUNK_RETRIES})"
                kill_zombie_queries "$pg_table"
                if [ "$retry" -lt "$MAX_CHUNK_RETRIES" ]; then
                    echo "  Retrying in 5s..."
                    sleep 5
                fi
            fi
        done

        if [ "$chunk_ok" = "false" ]; then
            # ── Progressive fallback: daily → hourly → pipe ──
            if [ "$chunk_mode" = "daily" ]; then
                warn "Chunk ${chunk_num} (${chunk_start} to ${chunk_end}) failed — escalating to hourly + pipe"
                copy_day_with_hourly_fallback "$pg_table" "$ch_table" "$columns" "$insert_cols" "$select_cols" "$chunk_start"
            elif [ "$chunk_mode" = "monthly" ]; then
                warn "Chunk ${chunk_num} (${chunk_start} to ${chunk_end}) failed — escalating to daily + pipe"
                copy_month_with_daily_fallback "$pg_table" "$ch_table" "$columns" "$insert_cols" "$select_cols" "$chunk_start" "$chunk_end"
            fi
        fi
    done

    if [ "$failed_chunks" -gt 0 ]; then
        warn "${pg_table}: ${failed_chunks}/${total_chunks} chunks needed fallback"
    fi

    log "${pg_table} chunked copy complete (${total_chunks} chunks)"
}

# When a daily chunk fails, split it into 24 hourly chunks.
# If an hourly chunk also OOMs via postgresql(), fall back to pipe mode.
copy_day_with_hourly_fallback() {
    local pg_table="$1"
    local ch_table="$2"
    local columns="$3"
    local insert_cols="$4"
    local select_cols="$5"
    local day="$6"

    echo "  Splitting ${day} into hourly chunks..."
    local hour_boundaries
    hour_boundaries=$(generate_hour_boundaries "$day")
    readarray -t hour_array <<< "$hour_boundaries"

    for ((h=0; h<24; h++)); do
        local h_start="${hour_array[$h]}"
        local h_end="${hour_array[$((h+1))]}"
        local hour_ok=false

        # Try postgresql() first for this hour
        for retry in 1 2 3; do
            if run_ch_query "INSERT INTO ${ch_table} (${insert_cols}) SELECT ${select_cols} FROM postgresql($(pg_conn_string "${pg_table}")) WHERE created_at >= '${h_start}' AND created_at < '${h_end}'" 2>&1; then
                hour_ok=true
                break
            else
                kill_zombie_queries "$pg_table"
                sleep 3
            fi
        done

        if [ "$hour_ok" = "false" ]; then
            # Hourly chunk also OOMed — fall back to pipe mode (guaranteed to work)
            warn "  Hour ${h} (${h_start}) OOMed — switching to pipe mode"
            copy_chunk_pipe "$pg_table" "$ch_table" "$columns" "$h_start" "$h_end" "h${h}"
        fi
    done
}

# When a monthly chunk fails, split into daily chunks with pipe fallback.
copy_month_with_daily_fallback() {
    local pg_table="$1"
    local ch_table="$2"
    local columns="$3"
    local insert_cols="$4"
    local select_cols="$5"
    local month_start="$6"
    local month_end="$7"

    echo "  Splitting ${month_start}..${month_end} into daily chunks..."
    local start_date end_date
    start_date=$(echo "$month_start" | cut -d' ' -f1)
    end_date=$(echo "$month_end" | cut -d' ' -f1)
    local day_boundaries
    day_boundaries=$(generate_day_boundaries "$start_date" "$end_date")
    readarray -t day_array <<< "$day_boundaries"

    local total_days=$(( ${#day_array[@]} - 1 ))

    for ((d=0; d<total_days; d++)); do
        local d_start="${day_array[$d]}"
        local d_end="${day_array[$((d+1))]}"
        local day_ok=false

        for retry in 1 2 3; do
            if run_ch_query "INSERT INTO ${ch_table} (${insert_cols}) SELECT ${select_cols} FROM postgresql($(pg_conn_string "${pg_table}")) WHERE created_at >= '${d_start}' AND created_at < '${d_end}'" 2>&1; then
                day_ok=true
                break
            else
                kill_zombie_queries "$pg_table"
                sleep 3
            fi
        done

        if [ "$day_ok" = "false" ]; then
            # Daily chunk OOMed — escalate to hourly + pipe
            warn "  Day ${d_start} OOMed — escalating to hourly + pipe"
            copy_day_with_hourly_fallback "$pg_table" "$ch_table" "$columns" "$insert_cols" "$select_cols" "$d_start"
        fi
    done
}

# ─── Main ────────────────────────────────────────────────────────────────────

main() {
    echo "============================================================"
    echo " PeerDB Hybrid — Bulk Copy PG → ClickHouse"
    echo " Mode: ${CH_MODE}"
    echo " Chunk threshold: ${CHUNK_THRESHOLD} rows"
    echo " Pipe batch size: ${PIPE_BATCH_SIZE} rows"
    if [ -n "$DETACH_MVS" ]; then
        echo " Detach MVs: ${DETACH_MVS}"
    fi
    echo "============================================================"

    # Auto-detect containers in docker mode
    if [ "$CH_MODE" = "docker" ]; then
        if [ -z "$CH_CONTAINER" ]; then
            CH_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i clickhouse | head -1)
        fi
        if [ -z "$PG_CONTAINER" ]; then
            PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i postgres | head -1)
        fi
        echo " PG container: ${PG_CONTAINER}"
        echo " CH container: ${CH_CONTAINER}"
    elif [ "$CH_MODE" = "k8s" ]; then
        echo " K8s namespace: ${K8S_NAMESPACE}"
        echo " CH pod: ${K8S_CH_POD}"
        echo " PG host: ${PG_HOST}"
    else
        echo " CH host: ${CH_HOST}:${CH_PORT}"
        echo " PG host: ${PG_HOST}:${PG_PORT}"
    fi

    # Check psql availability
    if command -v psql &>/dev/null; then
        echo " psql: available (pipe fallback enabled)"
    else
        warn " psql: not found — pipe fallback will not be available"
        warn " Install postgresql-client for resilient bulk copy of large tables"
    fi
    echo ""

    # Ensure PG won't kill long-running bulk read queries
    set_pg_timeout

    # Detach heavy materialized views to save memory during inserts
    detach_materialized_views

    local total=${#ALL_TABLES[@]}
    local current=0
    local copied=0
    local skipped=0
    local failed=0
    local failed_tables=""

    for entry in "${ALL_TABLES[@]}"; do
        local pg_table ch_table table_type
        pg_table=$(echo "$entry" | cut -d: -f1)
        ch_table=$(echo "$entry" | cut -d: -f2)
        table_type=$(echo "$entry" | cut -d: -f3)
        current=$((current + 1))

        echo ""
        echo "─── [${current}/${total}] ${pg_table} (${table_type}) ───"

        # Skip if requested
        if should_skip "$pg_table"; then
            warn "Skipping ${pg_table} (in SKIP_TABLES)"
            skipped=$((skipped + 1))
            continue
        fi

        # Get PG column list
        local columns
        columns=$(get_pg_columns "$pg_table")

        if [ -z "$columns" ]; then
            err "No columns found for ${pg_table} — skipping"
            failed=$((failed + 1))
            failed_tables="${failed_tables} ${pg_table}"
            continue
        fi

        # Get PG row count
        local pg_count
        pg_count=$(get_pg_count "$pg_table" 2>/dev/null | tr -d ' ')

        if [ -z "$pg_count" ] || [ "$pg_count" = "0" ]; then
            warn "${pg_table}: empty table, skipping"
            skipped=$((skipped + 1))
            continue
        fi

        echo "  PG rows: ${pg_count}"

        # Choose single vs chunked based on row count
        if [ "$pg_count" -gt "$CHUNK_THRESHOLD" ]; then
            if ! copy_table_chunked "$pg_table" "$ch_table" "$columns" 2>&1; then
                err "Failed to copy ${pg_table}"
                failed=$((failed + 1))
                failed_tables="${failed_tables} ${pg_table}"
                continue
            fi
        else
            if ! copy_table_single "$pg_table" "$ch_table" "$columns" 2>&1; then
                err "Failed to copy ${pg_table}"
                failed=$((failed + 1))
                failed_tables="${failed_tables} ${pg_table}"
                continue
            fi
        fi

        # Verify
        local ch_unique
        ch_unique=$(get_ch_unique_count "$ch_table" 2>/dev/null | tr -d ' ')
        local pct=0
        if [ -n "$ch_unique" ] && [ "$pg_count" -gt 0 ]; then
            pct=$((ch_unique * 100 / pg_count))
        fi

        if [ "$pct" -ge 95 ]; then
            log "Verified: ${ch_unique}/${pg_count} unique rows (${pct}%)"
        else
            warn "Incomplete: ${ch_unique}/${pg_count} unique rows (${pct}%) — may need retry"
        fi

        copied=$((copied + 1))
    done

    # ── Reattach MVs before dedup (so OPTIMIZE populates them) ──
    reattach_materialized_views

    # ── Dedup: OPTIMIZE TABLE FINAL on copied tables ──
    if [ "$copied" -gt 0 ]; then
        step "Running OPTIMIZE TABLE FINAL to deduplicate copied tables..."
        for entry in "${ALL_TABLES[@]}"; do
            local ch_table
            ch_table=$(echo "$entry" | cut -d: -f2)
            local pg_table
            pg_table=$(echo "$entry" | cut -d: -f1)

            if should_skip "$pg_table"; then
                continue
            fi

            echo "  OPTIMIZE ${ch_table}..."
            if run_ch_query "OPTIMIZE TABLE ${ch_table} FINAL" 2>&1; then
                log "  ${ch_table} deduplicated"
            else
                warn "  ${ch_table} OPTIMIZE failed — run manually: OPTIMIZE TABLE ${ch_table} FINAL"
            fi
        done
    fi

    # ── Reset PG timeout ──
    reset_pg_timeout

    echo ""
    echo "============================================================"
    echo " Bulk Copy Summary"
    echo "   Copied:  ${copied}"
    echo "   Skipped: ${skipped}"
    echo "   Failed:  ${failed}"
    if [ -n "$failed_tables" ]; then
        echo "   Failed tables:${failed_tables}"
        echo "   Retry with: SKIP_TABLES=<completed_tables> $0"
    fi
    echo "============================================================"

    if [ "$failed" -gt 0 ]; then
        exit 1
    fi
}

main "$@"
