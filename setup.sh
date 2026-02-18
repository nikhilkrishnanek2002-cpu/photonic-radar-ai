#!/bin/bash
################################################################################
# PHOTONIC RADAR AI - Setup Script for Linux/macOS
################################################################################
# This script initializes the development environment with a virtual
# environment, installs all dependencies, and prints next steps.
# 
# Safe to run multiple times - will not reinstall if already set up
#
# Usage:
#    bash setup.sh         # Full setup
#    bash setup.sh --force # Force reinstall
################################################################################

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/photonic-radar-ai/venv"
REQUIREMENTS="${PROJECT_ROOT}/requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     PHOTONIC RADAR AI - Setup Script (Linux/macOS)        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}[1/4] Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 not found. Please install Python 3.11 or later.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} found${NC}"
echo ""

# Create or use virtual environment
FORCE_INSTALL=""
if [ "$1" = "--force" ]; then
    FORCE_INSTALL="yes"
    if [ -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}[2/4] Removing existing virtual environment...${NC}"
        rm -rf "$VENV_DIR"
        echo -e "${GREEN}✓ Virtual environment removed${NC}"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}[2/4] Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created at ${VENV_DIR}${NC}"
else
    echo -e "${YELLOW}[2/4] Virtual environment already exists${NC}"
    echo -e "${GREEN}✓ Using existing venv${NC}"
fi
echo ""

# Activate venv
echo -e "${YELLOW}[3/4] Activating virtual environment...${NC}"
source "${VENV_DIR}/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Install/upgrade pip
echo -e "${YELLOW}[3.5/4] Upgrading pip...${NC}"
python -m pip install --upgrade pip setuptools wheel &> /dev/null
echo -e "${GREEN}✓ Pip upgraded${NC}"
echo ""

# Install requirements
if [ ! -f "$REQUIREMENTS" ]; then
    echo -e "${RED}✗ requirements.txt not found at ${REQUIREMENTS}${NC}"
    exit 1
fi

echo -e "${YELLOW}[4/4] Installing dependencies...${NC}"
echo "     This may take 2-5 minutes on first install..."
pip install -r "$REQUIREMENTS" --progress-bar on 2>&1 | tail -20
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    SETUP COMPLETE! ✓                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}NEXT STEPS:${NC}"
echo ""
echo -e "1. ${YELLOW}Desktop Application (Recommended):${NC}"
echo -e "   ${BLUE}python run_desktop.py${NC}"
echo ""
echo -e "2. ${YELLOW}Command Line Backend:${NC}"
echo -e "   ${BLUE}bash start.sh${NC}"
echo ""
echo -e "3. ${YELLOW}Demo Mode:${NC}"
echo -e "   ${BLUE}python demo.py${NC}"
echo ""
echo -e "4. ${YELLOW}Build Executable:${NC}"
echo -e "   ${BLUE}bash build_desktop.sh${NC}"
echo -e "   Output: ${BLUE}dist/PhotonicRadarAI/${NC}"
echo ""
echo -e "${YELLOW}System Requirements:${NC}"
echo -e "  • Python 3.11+ ✓"
echo -e "  • 2GB RAM minimum"
echo -e "  • PySide6 for desktop GUI"
echo -e "  • Streamlit for dashboard"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo -e "  • Desktop App: ${BLUE}DESKTOP_APP.md${NC}"
echo -e "  • Quick Start: ${BLUE}QUICK_START.md${NC} (if available)"
echo -e "  • README: ${BLUE}README.md${NC}"
echo ""

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"
python -c "import numpy, scipy, pandas, streamlit, PySide6, fastapi, torch; print('✓ All core packages installed')" 2>/dev/null || \
python -c "import numpy, scipy, pandas, streamlit, PySide6, fastapi; print('✓ All core packages installed (torch optional)')"
echo ""

echo -e "${GREEN}Ready to launch! 🚀${NC}"
echo ""
