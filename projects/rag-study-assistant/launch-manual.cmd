@echo off
setlocal
cd /d "%~dp0"
set "MANUAL_PYTHON=%~dp0.venv\Scripts\pythonw.exe"
if not exist "%MANUAL_PYTHON%" (
    echo This folder needs its Python environment first.
    echo Follow the Setup and run from source steps in README.md.
    pause
    exit /b 1
)
start "" "%MANUAL_PYTHON%" "%~dp0src\manual_app.py" %*
