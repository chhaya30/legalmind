@echo off
setlocal
cd /d %~dp0
set FAIL=0

echo === LegalMind local prerequisite check ===
where py >nul 2>&1 || (echo [FAIL] Python launcher 'py' not found. Install Python 3.11 or 3.12 and add it to PATH.& set FAIL=1)
where node >nul 2>&1 || (echo [FAIL] Node.js not found. Install Node.js 20+ and add it to PATH.& set FAIL=1)
where npm >nul 2>&1 || (echo [FAIL] npm not found.& set FAIL=1)
where psql >nul 2>&1 || (echo [FAIL] PostgreSQL psql not found. Install PostgreSQL 16+ and add its bin folder to PATH.& set FAIL=1)

echo.
if %FAIL%==0 (
  echo [OK] Python, Node/npm and PostgreSQL client are available.
  echo [NOTE] PostgreSQL must have the pgvector extension installed.
  echo [NOTE] Redis is NOT required in local mode.
) else (
  echo.
  echo Install the missing prerequisites, then run this script again.
)
exit /b %FAIL%
