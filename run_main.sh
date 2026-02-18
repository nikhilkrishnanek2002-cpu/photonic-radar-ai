#!/bin/bash
# Wrapper script to run main.py with proper Python environment
set -e

cd /home/nikhil/PycharmProjects/photonic-radar-ai

# Try venv first, fall back to system
if [ -f "photonic-radar-ai/venv/bin/python" ]; then
    PYTHON="photonic-radar-ai/venv/bin/python"
elif [ -f "photonic-radar-ai/.venv/bin/python" ]; then
    PYTHON="photonic-radar-ai/.venv/bin/python"
else
    PYTHON="python3"
fi

echo "Using Python: $PYTHON"
$PYTHON main.py "$@"
