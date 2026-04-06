@echo off
setlocal
chcp 65001 >nul

echo Starting RQ worker dev process...
python -m worker.main
exit /b %errorlevel%
