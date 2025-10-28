-- ====================================
-- PostgreSQL Test Database Setup
-- ====================================
-- Run this script to create test database and user
--
-- How to run (Windows PowerShell/CMD):
--   psql -U postgres -f setup_test_db.sql
--
-- Or connect to pgAdmin and run these commands
-- ====================================

-- Create test user
DROP USER IF EXISTS test;
CREATE USER test WITH PASSWORD 'test';

-- Grant CREATEDB privilege (needed for pytest to create temp databases)
ALTER USER test CREATEDB;

-- Drop existing test database if exists
DROP DATABASE IF EXISTS test_plan_beyond;

-- Create test database
CREATE DATABASE test_plan_beyond OWNER test;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE test_plan_beyond TO test;

-- Connect to test database and grant schema privileges
\c test_plan_beyond
GRANT ALL ON SCHEMA public TO test;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test;

-- Done!
\echo '✓ PostgreSQL test database setup complete!'
\echo ''
\echo 'Connection string:'
\echo '  postgresql://test:test@localhost:5432/test_plan_beyond'
\echo ''
\echo 'Run tests with:'
\echo '  pytest tests/unit/foundation/test_database_models.py -v'
