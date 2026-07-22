@echo off
title Skyrim LLM Voice Mod Installer
color 0A

echo ===================================================
echo   Hello! Welcome to the installer for
echo   Skyrim Local LLM Voice mod.
echo ===================================================
echo.

:: Check for Python
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found on your system.
    echo Please download and install Python 3.10 or 3.11 from python.org
    echo Make sure to check the box "Add Python to PATH" during installation!
    pause
    exit /b
)

echo [OK] Python found.
echo.

:: Navigate to the server folder reliably
cd /d "%~dp0server"

:: Check and create virtual environment
IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment (venv). This may take a moment...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
    echo [OK] Virtual environment created successfully.
) ELSE (
    echo [OK] Virtual environment found.
)

echo.
echo [INFO] Activating environment and checking requirements...
call venv\Scripts\activate.bat

:: Update pip and install requirements
python -m pip install --upgrade pip >nul 2>&1
echo [INFO] Installing required libraries (this may take a while on first run)...
pip install -r requirements.txt

echo.
echo ===================================================
echo   All set! Launching the control panel...
echo ===================================================
timeout /t 2 >nul

:: Launch the python console app (which will be in Russian as requested)
python src\launcher.py

pause
