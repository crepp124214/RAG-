@echo off
setlocal
chcp 65001 >nul

echo Running backend coverage...
python -m pytest backend/tests -p no:cacheprovider --cov=backend --cov-report=term-missing --no-cov-on-fail
exit /b %errorlevel%
