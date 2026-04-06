@echo off
setlocal
chcp 65001 >nul

echo Building frontend...
cd /d "%~dp0..\frontend"
cmd /c npm run build
exit /b %errorlevel%
