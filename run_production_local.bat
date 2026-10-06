@echo off
setlocal
cd /d %~dp0frontend
if not exist node_modules (
  echo Run setup_local.bat first.
  pause
  exit /b 1
)
echo === Building LegalMind production frontend ===
call npm run build
if errorlevel 1 (
  echo Production build failed.
  pause
  exit /b 1
)
echo === Starting production preview on http://127.0.0.1:5173 ===
call npm run preview -- --host 127.0.0.1 --port 5173
