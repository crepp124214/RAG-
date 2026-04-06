@echo off
setlocal
chcp 65001 >nul

echo Starting FastAPI backend dev server...
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
exit /b %errorlevel%
