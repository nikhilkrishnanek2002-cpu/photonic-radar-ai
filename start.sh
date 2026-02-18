#!/bin/bash
# Single unified startup script for PHOENIX Radar AI
# Usage: bash start.sh

cd /home/nikhil/PycharmProjects/photonic-radar-ai

# Use venv Python
PYTHON="photonic-radar-ai/venv/bin/python"

# Run production system with API + Dashboard + Simulation
echo "Starting PHOENIX Radar AI System..."
$PYTHON main.py --ui
