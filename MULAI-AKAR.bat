@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 tools\serve.py
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Instal Python 3.8+ dari https://www.python.org/downloads/ dan aktifkan Add Python to PATH.
        pause
        exit /b 1
    )
    python tools\serve.py
)
if errorlevel 1 pause
