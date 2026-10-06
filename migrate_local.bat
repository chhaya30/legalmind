@echo off
setlocal
cd /d %~dp0
if not exist backend\.venv\Scripts\python.exe (
  echo Python environment missing. Run setup_local.bat first.
  exit /b 1
)
cd backend
set PYTHONPATH=.
.\.venv\Scripts\python.exe -m alembic upgrade head
if errorlevel 1 (
  echo Migration failed. Check PostgreSQL, credentials, and pgvector installation.
  pause
  exit /b 1
)
echo Database migrations completed successfully.
pause
