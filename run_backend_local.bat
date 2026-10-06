@echo off
setlocal
cd /d %~dp0backend
if not exist .venv\Scripts\python.exe (
  echo Run setup_local.bat first.
  pause
  exit /b 1
)
set PYTHONPATH=.
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
pause
