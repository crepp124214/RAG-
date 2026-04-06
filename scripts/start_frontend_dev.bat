@echo off
setlocal
chcp 65001 >nul

echo Starting Vite frontend dev server...
cd /d "%~dp0..\frontend"
cmd /c npm run dev -- --host 127.0.0.1 --port 5173
exit /b %errorlevel%
