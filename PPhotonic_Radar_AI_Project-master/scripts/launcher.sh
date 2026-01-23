#!/bin/bash
# PHOENIX-RADAR Desktop Launcher

# Ensure we are in the script's directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/.."

echo "🚀 Launching PHOENIX-RADAR from $DIR..."

# Check for virtual environment
if [ -d ".venv" ]; then
    echo "Using local virtual environment..."
    python_exec=".venv/bin/python3"
else
    echo "Using system python..."
    python_exec="/usr/bin/python3"
fi

# Run the python launcher
"$python_exec" launcher.py

# Keep terminal open on error
if [ $? -ne 0 ]; then
    echo "❌ Application exited with error."
    echo "Press Enter to exit..."
    read
fi
