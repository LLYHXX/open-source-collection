-- Test Database Initialization Script
-- This script sets up the test database with proper configurations

-- Create additional databases if needed
CREATE DATABASE test_tfc_analytics;
CREATE DATABASE test_tfc_cache;

-- Create test users with appropriate permissions
CREATE USER test_analytics WITH PASSWORD 'test_password';
CREATE USER test_cache WITH PASSWORD 'test_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE test_tfc TO test_user;
GRANT ALL PRIVILEGES ON DATABASE test_tfc_analytics TO test_analytics;
GRANT ALL PRIVILEGES ON DATABASE test_tfc_cache TO test_cache;

-- Connect to the main test database
\c test_tfc;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Set up test-specific configurations
ALTER DATABASE test_tfc SET timezone TO 'UTC';
ALTER DATABASE test_tfc SET default_text_search_config TO 'pg_catalog.english';

-- Create test schema for isolating test data
CREATE SCHEMA IF NOT EXISTS test_schema;
GRANT ALL PRIVILEGES ON SCHEMA test_schema TO test_user;

-- Set search path
ALTER USER test_user SET search_path = public,test_schema;

-- Performance optimizations for testing
-- Disable fsync for faster testing (only for test environment)
ALTER SYSTEM SET fsync = off;
ALTER SYSTEM SET synchronous_commit = off;
ALTER SYSTEM SET full_page_writes = off;
ALTER SYSTEM SET checkpoint_segments = 32;
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = 16MB;
ALTER SYSTEM SET shared_buffers = 256MB;

-- Reload configuration
SELECT pg_reload_conf();
