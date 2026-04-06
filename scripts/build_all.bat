@echo off
setlocal
chcp 65001 >nul

call "%~dp0build_frontend.bat"
exit /b %errorlevel%
