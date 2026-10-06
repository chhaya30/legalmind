@echo off
setlocal
cd /d %~dp0
start "LegalMind Backend" cmd /k call "%~dp0run_backend_local.bat"
start "LegalMind Frontend" cmd /k call "%~dp0run_frontend_local.bat"
echo Started backend and frontend in separate windows.
echo Backend: http://127.0.0.1:8001
echo Frontend: http://127.0.0.1:5173
