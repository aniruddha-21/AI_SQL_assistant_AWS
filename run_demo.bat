@echo off
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 goto run_py
where python >nul 2>&1
if not errorlevel 1 goto run_python
echo Python was not found. Install Python 3 from python.org, then run this file again.
goto end

:run_py
py -3 -u app.py
goto end

:run_python
python -u app.py

:end
echo.
pause
