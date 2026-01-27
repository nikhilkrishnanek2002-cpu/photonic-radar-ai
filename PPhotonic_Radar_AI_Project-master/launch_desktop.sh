#!/bin/bash
# PHOENIX-RADAR Application Launcher

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Navigate to the project root
cd "$SCRIPT_DIR"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run the application
python3 desktop_app/main.py
