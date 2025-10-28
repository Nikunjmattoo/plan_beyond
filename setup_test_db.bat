@echo off
REM ====================================
REM PostgreSQL Test Database Setup (Windows)
REM ====================================

echo.
echo ================================
echo PostgreSQL Test Database Setup
echo ================================
echo.

echo Creating test user and database...
echo.

REM Run the SQL script
psql -U postgres -f setup_test_db.sql

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Failed to setup test database
    echo.
    echo Make sure:
    echo   1. PostgreSQL is installed
    echo   2. psql is in your PATH
    echo   3. You can connect as 'postgres' user
    echo.
    echo Try running manually:
    echo   psql -U postgres -f setup_test_db.sql
    echo.
    pause
    exit /b 1
)

echo.
echo ================================
echo Setup Complete!
================================
echo.
echo Test database connection string:
echo   postgresql://test:test@localhost:5432/test_plan_beyond
echo.
echo Run tests with:
echo   pytest tests/unit/foundation/test_database_models.py -v
echo.
pause
