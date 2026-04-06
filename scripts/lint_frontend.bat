@echo off
setlocal
chcp 65001 >nul

echo Running frontend lint...
cd /d "%~dp0..\frontend"
cmd /c npm run lint
exit /b %errorlevel%
