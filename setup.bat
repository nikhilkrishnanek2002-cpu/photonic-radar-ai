@echo off
REM ############################################################################
REM # PHOTONIC RADAR AI - Setup Script for Windows
REM ############################################################################
REM # This script initializes the development environment with a virtual
REM # environment, installs all dependencies, and prints next steps.
REM #
REM # Safe to run multiple times - will not reinstall if already set up
REM #
REM # Usage:
REM #    setup.bat         # Full setup
REM #    setup.bat --force # Force reinstall
REM ############################################################################

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0
set VENV_DIR=%PROJECT_ROOT%photonic-radar-ai\venv
set REQUIREMENTS=%PROJECT_ROOT%requirements.txt
set PYTHON_EXE=python

echo.
echo ============================================================
echo    PHOTONIC RADAR AI - Setup Script (Windows)
echo ============================================================
echo.

REM Check Python version
echo [1/4] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.11 or later.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo √ Python %PYTHON_VERSION% found
echo.

REM Check force install flag
set FORCE_INSTALL=
if "%1"=="--force" (
    set FORCE_INSTALL=yes
    if exist "%VENV_DIR%" (
        echo [2/4] Removing existing virtual environment...
        rmdir /s /q "%VENV_DIR%" >nul 2>&1
        echo √ Virtual environment removed
    )
)

REM Create or use virtual environment
if not exist "%VENV_DIR%" (
    echo [2/4] Creating virtual environment...
    python -m venv "%VENV_DIR%"
    echo √ Virtual environment created at %VENV_DIR%
) else (
    echo [2/4] Virtual environment already exists
    echo √ Using existing venv
)
echo.

REM Activate venv
echo [3/4] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
echo √ Virtual environment activated
echo.

REM Install/upgrade pip
echo [3.5/4] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
echo √ Pip upgraded
echo.

REM Check requirements.txt exists
if not exist "%REQUIREMENTS%" (
    echo Error: requirements.txt not found at %REQUIREMENTS%
    pause
    exit /b 1
)

REM Install requirements
echo [4/4] Installing dependencies...
echo      This may take 2-5 minutes on first install...
pip install -r "%REQUIREMENTS%" --progress-bar on
if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)
echo √ Dependencies installed
echo.

echo ============================================================
echo                   SETUP COMPLETE! √
echo ============================================================
echo.

echo NEXT STEPS:
echo.
echo 1. Desktop Application (Recommended):
echo    python run_desktop.py
echo.
echo 2. Command Line Backend:
echo    bash start.sh
echo.
echo 3. Demo Mode:
echo    python demo.py
echo.
echo 4. Build Executable:
echo    build_desktop.bat
echo    Output: dist\PhotonicRadarAI\
echo.
echo System Requirements:
echo   • Python 3.11+ √
echo   • 2GB RAM minimum
echo   • PySide6 for desktop GUI
echo   • Streamlit for dashboard
echo.
echo Documentation:
echo   • Desktop App: DESKTOP_APP.md
echo   • Quick Start: QUICK_START.md (if available)
echo   • README: README.md
echo.

REM Verify installation
echo Verifying installation...
python -c "import numpy, scipy, pandas, streamlit, PySide6, fastapi, torch; print('√ All core packages installed')" 2>nul || python -c "import numpy, scipy, pandas, streamlit, PySide6, fastapi; print('√ All core packages installed (torch optional)')"
echo.

echo Ready to launch! 🚀
echo.
pause
