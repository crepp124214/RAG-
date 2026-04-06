@echo off
setlocal
chcp 65001 >nul

echo Running frontend tests...
cd /d "%~dp0..\frontend"
cmd /c npm run test:unit -- --run
exit /b %errorlevel%
