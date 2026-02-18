#!/bin/bash
# Build desktop executable for Linux/macOS using PyInstaller

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Photonic Radar AI - Desktop Build"
echo "=========================================="
echo ""

# Check if venv exists
if [ ! -d "photonic-radar-ai/venv" ]; then
    echo "Error: Virtual environment not found at photonic-radar-ai/venv"
    echo "Please run: bash start.sh first to initialize"
    exit 1
fi

# Activate venv
if [ -f "photonic-radar-ai/venv/bin/activate" ]; then
    source "photonic-radar-ai/venv/bin/activate"
else
    echo "Error: Cannot find venv activation script"
    exit 1
fi

echo "Virtual environment activated"
echo ""

# Install PyInstaller if needed
echo "Checking for PyInstaller..."
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    pip install -q PyInstaller
fi

# Install PySide6 if needed
echo "Checking for PySide6..."
if ! python -c "import PySide6" 2>/dev/null; then
    echo "Installing PySide6..."
    pip install -q PySide6
fi

echo ""
echo "Building executable..."
echo ""

# Clean previous builds
rm -rf build/ dist/ PhotonicRadarAI.spec 2>/dev/null || true

# Build with PyInstaller using onedir (directory mode) - more reliable for PySide6
# onedir is better for large deployments and avoids decompression issues
pyinstaller \
    --onedir \
    --windowed \
    --noupx \
    --name PhotonicRadarAI \
    --add-data "app:app" \
    --add-data "photonic-radar-ai:photonic-radar-ai" \
    --add-data "configs:configs" \
    --hidden-import=PySide6 \
    --hidden-import=PySide6.QtCore \
    --hidden-import=PySide6.QtGui \
    --hidden-import=PySide6.QtWidgets \
    --hidden-import=psutil \
    --distpath dist \
    run_desktop.py

echo ""
echo "=========================================="
echo "Build complete!"
echo "=========================================="
echo ""
echo "Application location:"
echo "  dist/PhotonicRadarAI/"
echo ""
echo "Executable:"
echo "  dist/PhotonicRadarAI/PhotonicRadarAI"
echo ""
echo "To run:"
echo "  ./dist/PhotonicRadarAI/PhotonicRadarAI"
echo ""
echo "Or run folder directly:"
echo "  cd dist/PhotonicRadarAI && ./PhotonicRadarAI"
echo ""
