#!/bin/bash
#
# Setup PostgreSQL Test Database
# Creates test user and database for running tests
#

echo "================================"
echo "PostgreSQL Test Database Setup"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# PostgreSQL connection info
PG_USER="${POSTGRES_USER:-postgres}"
PG_HOST="${POSTGRES_HOST:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"

# Test database info
TEST_USER="test"
TEST_PASSWORD="test"
TEST_DB="test_plan_beyond"

echo ""
echo "Creating PostgreSQL test user and database..."
echo "Host: $PG_HOST:$PG_PORT"
echo "Test User: $TEST_USER"
echo "Test Database: $TEST_DB"
echo ""

# Function to run psql command
run_psql() {
    psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d postgres -c "$1" 2>&1
}

# Create test user
echo "Step 1: Creating test user '$TEST_USER'..."
run_psql "DROP USER IF EXISTS $TEST_USER;"
result=$(run_psql "CREATE USER $TEST_USER WITH PASSWORD '$TEST_PASSWORD';")

if [[ $result == *"ERROR"* ]]; then
    echo -e "${RED}✗ Failed to create user${NC}"
    echo "$result"
    exit 1
else
    echo -e "${GREEN}✓ User '$TEST_USER' created${NC}"
fi

# Grant createdb privilege
echo ""
echo "Step 2: Granting CREATEDB privilege..."
result=$(run_psql "ALTER USER $TEST_USER CREATEDB;")

if [[ $result == *"ERROR"* ]]; then
    echo -e "${RED}✗ Failed to grant CREATEDB${NC}"
    echo "$result"
    exit 1
else
    echo -e "${GREEN}✓ CREATEDB privilege granted${NC}"
fi

# Drop existing test database if exists
echo ""
echo "Step 3: Cleaning up existing test databases..."
run_psql "DROP DATABASE IF EXISTS $TEST_DB;"

# Clean up any timestamped test databases
run_psql "SELECT datname FROM pg_database WHERE datname LIKE 'test_%';" | grep "test_" | while read -r db; do
    if [ ! -z "$db" ]; then
        echo "  Dropping old test database: $db"
        run_psql "DROP DATABASE IF EXISTS $db;"
    fi
done

echo -e "${GREEN}✓ Cleaned up old test databases${NC}"

# Create test database
echo ""
echo "Step 4: Creating test database '$TEST_DB'..."
result=$(run_psql "CREATE DATABASE $TEST_DB OWNER $TEST_USER;")

if [[ $result == *"ERROR"* ]]; then
    echo -e "${RED}✗ Failed to create database${NC}"
    echo "$result"
    exit 1
else
    echo -e "${GREEN}✓ Database '$TEST_DB' created${NC}"
fi

# Grant all privileges
echo ""
echo "Step 5: Granting privileges..."
result=$(run_psql "GRANT ALL PRIVILEGES ON DATABASE $TEST_DB TO $TEST_USER;")

if [[ $result == *"ERROR"* ]]; then
    echo -e "${RED}✗ Failed to grant privileges${NC}"
    echo "$result"
else
    echo -e "${GREEN}✓ All privileges granted${NC}"
fi

# Test connection
echo ""
echo "Step 6: Testing connection..."
TEST_CONN=$(PGPASSWORD=$TEST_PASSWORD psql -h "$PG_HOST" -p "$PG_PORT" -U "$TEST_USER" -d "$TEST_DB" -c "SELECT 1;" 2>&1)

if [[ $TEST_CONN == *"ERROR"* ]] || [[ $TEST_CONN == *"could not connect"* ]]; then
    echo -e "${RED}✗ Connection test failed${NC}"
    echo "$TEST_CONN"
    exit 1
else
    echo -e "${GREEN}✓ Connection test successful${NC}"
fi

echo ""
echo "================================"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "================================"
echo ""
echo "Test Database Connection String:"
echo "  postgresql://$TEST_USER:$TEST_PASSWORD@$PG_HOST:$PG_PORT/$TEST_DB"
echo ""
echo "You can now run tests with:"
echo "  pytest tests/unit/foundation/test_database_models.py -v"
echo ""
