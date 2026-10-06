@echo off
setlocal
cd /d %~dp0frontend
if not exist node_modules (
  echo Run setup_local.bat first.
  pause
  exit /b 1
)
call npm run dev -- --host 127.0.0.1
pause
