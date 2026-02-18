@echo off
REM Build desktop executable for Windows using PyInstaller

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==========================================
echo Photonic Radar AI - Desktop Build (Windows)
echo ==========================================
echo.

REM Check if venv exists
if not exist "photonic-radar-ai\venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found at photonic-radar-ai\venv
    echo Please run: start.bat first to initialize
    exit /b 1
)

REM Activate venv
call photonic-radar-ai\venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    exit /b 1
)

echo Virtual environment activated
echo.

REM Install PyInstaller if needed
echo Checking for PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install -q PyInstaller
)

REM Install PySide6 if needed
echo Checking for PySide6...
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo Installing PySide6...
    pip install -q PySide6
)

echo.
echo Building executable...
echo.

REM Build with PyInstaller
pyinstaller photonic_radar_desktop.spec --clean
if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo.
echo ==========================================
echo Build complete!
echo ==========================================
echo.
echo Executable location:
echo   dist\PhotonicRadarAI.exe
echo.
echo To run:
echo   dist\PhotonicRadarAI.exe
echo.
pause
