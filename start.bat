@echo off
setlocal
chcp 65001 >nul

set "COMMAND=%~1"
if "%COMMAND%"=="" set "COMMAND=all"

if /I "%COMMAND%"=="help" goto :help_success
if /I "%COMMAND%"=="-h" goto :help_success
if /I "%COMMAND%"=="--help" goto :help_success

powershell -ExecutionPolicy Bypass -File scripts\dev.ps1 %*
exit /b %errorlevel%

:help_success
echo RAG developer entrypoint
echo.
echo Usage:
echo   start.bat [dev^|all^|backend^|frontend^|worker^|stop^|status^|test^|check^|build^|coverage^|lint^|health^|smoke^|clean^|help]
echo.
echo Examples:
echo   start.bat
echo   start.bat backend
echo   start.bat test
echo   start.bat stop all
exit /b 0
