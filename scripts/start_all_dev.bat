@echo off
setlocal
chcp 65001 >nul

echo Starting backend, frontend, and worker dev processes...

start "RAG Backend" cmd /k "cd /d %~dp0.. && call scripts\start_backend_dev.bat"
start "RAG Frontend" cmd /k "cd /d %~dp0.. && call scripts\start_frontend_dev.bat"
start "RAG Worker" cmd /k "cd /d %~dp0.. && call scripts\start_worker_dev.bat"

echo Dev services started in separate terminals.
echo Backend: http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
exit /b 0
