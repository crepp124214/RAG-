@echo off
setlocal
chcp 65001 >nul

call "%~dp0test_backend.bat"
if errorlevel 1 exit /b %errorlevel%

call "%~dp0test_frontend.bat"
exit /b %errorlevel%
