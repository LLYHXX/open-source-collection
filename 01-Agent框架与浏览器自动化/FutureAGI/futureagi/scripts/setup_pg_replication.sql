-- PostgreSQL Logical Replication Setup for PeerDB CDC
-- Run this on the application PostgreSQL database

-- Create publication for PeerDB CDC
CREATE PUBLICATION IF NOT EXISTS peerdb_publication FOR TABLE
    tracer_observation_span,
    tracer_trace,
    trace_session,
    tracer_eval_logger;

-- Set replica identity for each table (primary key is sufficient)
ALTER TABLE tracer_observation_span REPLICA IDENTITY USING INDEX tracer_observation_span_pkey;
ALTER TABLE tracer_trace REPLICA IDENTITY USING INDEX tracer_trace_pkey;
ALTER TABLE trace_session REPLICA IDENTITY USING INDEX trace_session_pkey;
ALTER TABLE tracer_eval_logger REPLICA IDENTITY USING INDEX tracer_eval_logger_pkey;
