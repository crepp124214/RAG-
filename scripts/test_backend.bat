@echo off
setlocal
chcp 65001 >nul

echo Running backend tests...
python -m pytest backend/tests -p no:cacheprovider
exit /b %errorlevel%
