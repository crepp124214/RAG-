@echo off
setlocal
chcp 65001 >nul

echo Running frontend type check...
cd /d "%~dp0..\frontend"
cmd /c npm run typecheck
exit /b %errorlevel%
