@echo off
setlocal
cd /d %~dp0

echo === LegalMind local setup (NO DOCKER) ===
call check_local_prereqs.bat
if errorlevel 1 exit /b 1

if not exist backend\.venv (
  echo Creating Python virtual environment...
  py -3.11 -m venv backend\.venv
  if errorlevel 1 py -m venv backend\.venv
)

if not exist backend\.env (
  copy /Y .env.local.example backend\.env >nul
  echo Created backend\.env from .env.local.example
) else (
  echo backend\.env already exists; leaving it unchanged.
)

echo Installing Python dependencies...
backend\.venv\Scripts\python.exe -m pip install --upgrade pip
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if errorlevel 1 exit /b 1

echo Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 exit /b 1
cd ..

echo.
echo IMPORTANT: create PostgreSQL database/user and enable pgvector before migration.
echo See LOCAL_RUN.md for exact PostgreSQL commands.
echo.
pause
