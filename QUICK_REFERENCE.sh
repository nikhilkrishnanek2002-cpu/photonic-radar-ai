#!/usr/bin/env bash
# PHOENIX-RADAR: Quick Reference Cheat Sheet
# ============================================

# INSTALLATION
# ────────────
git clone https://github.com/nikhilkrishnanek2002-cpu/photonic-radar-ai.git
cd photonic-radar-ai
python3 -m venv .venv && source .venv/bin/activate
pip install -r photonic-radar-ai/requirements.txt


# QUICK START
# ───────────
python3 main.py                    # Radar + API server (default)
python3 main.py --ui               # With Streamlit dashboard
python3 main.py --debug            # Debug logging
python3 main.py --api-only         # API server only
python3 main.py --ui --headless    # Remote/server mode


# ENDPOINTS
# ─────────
http://localhost:5000              # API Server (Flask)
http://localhost:5000/health       # Health check
http://localhost:5000/state        # Full system state (JSON)
http://localhost:5000/events       # Recent events
http://localhost:8501              # Dashboard (Streamlit)


# API QUERIES
# ───────────
curl http://localhost:5000/health
curl http://localhost:5000/state | jq
curl http://localhost:5000/events | jq '.events[] | .message'


# LOGS
# ────
cat photonic-radar-ai/runtime/logs/phoenix_radar.log
tail -f photonic-radar-ai/runtime/logs/phoenix_radar.log
tail -f photonic-radar-ai/runtime/api_server.log


# TROUBLESHOOTING
# ───────────────
python3 -c "from defense_core import get_defense_bus; print('✓ OK')"
python3 -c "from simulation_engine.orchestrator import SimulationOrchestrator; print('✓ OK')"
lsof -i :5000                      # Check if port 5000 is in use
lsof -i :8501                      # Check if port 8501 is in use
ps aux | grep main.py              # Check if process is running


# SYSTEMD SERVICE (Linux)
# ───────────────────────
sudo systemctl start phoenix-radar
sudo systemctl stop phoenix-radar
sudo systemctl restart phoenix-radar
sudo systemctl status phoenix-radar
sudo journalctl -u phoenix-radar -f  # Watch logs


# DEVELOPMENT
# ───────────
python3 main.py --debug > /tmp/phoenix.log 2>&1 &  # Background with logging
kill %1                                            # Kill background job
python3 -m main --help                             # Show help


# MONITORING
# ──────────
watch -n 1 'curl -s http://localhost:5000/health | jq'
watch -n 1 'ps aux | grep main'
watch -n 1 'df -h photonic-radar-ai/runtime'


# DOCKER
# ──────
docker build -t phoenix-radar:latest .
docker run -p 5000:5000 -p 8501:8501 phoenix-radar:latest
docker ps
docker logs -f <container-id>


# KUBERNETES
# ──────────
kubectl apply -f deployment.yaml
kubectl get pods -l app=phoenix-radar
kubectl logs -f deployment/phoenix-radar
kubectl port-forward service/phoenix-radar-service 5000:5000


# CLEANUP
# ───────
rm -rf photonic-radar-ai/runtime/logs/*.log
rm -rf photonic-radar-ai/runtime/shared_state.json
pkill -f "python3 main.py"          # Kill all running instances


# FILE STRUCTURE
# ──────────────
photonic-radar-ai/
├── main.py                         # Main entry point (RECOMMENDED)
├── run_platform.py                 # Alternative entry point
├── requirements.txt                # Dependencies
├── MAIN_ENTRY_POINT.md            # Documentation
├── runtime/                        # Runtime files
│   ├── logs/
│   │   ├── phoenix_radar.log      # Main log
│   │   ├── api_server.log         # API server log
│   │   └── dashboard.log          # Dashboard log
│   ├── shared_state.json          # IPC state file
│   └── intelligence/              # EW intelligence exports
├── defense_core/                  # Event bus (CRITICAL)
├── subsystems/                    # Threading components
│   ├── event_bus_subsystem.py
│   ├── radar_subsystem.py
│   └── ew_subsystem.py
├── simulation_engine/             # Physics engine
├── cognitive/                      # AI intelligence pipeline
├── api/                           # REST server
│   └── server.py
└── ui/                            # Dashboard
    └── dashboard.py


# ENVIRONMENT VARIABLES
# ─────────────────────
export PYTHONUNBUFFERED=1          # Unbuffered Python output
export TF_CPP_MIN_LOG_LEVEL=3      # Suppress TensorFlow warnings
export LOG_LEVEL=DEBUG             # Custom log level


# CONFIGURATION (In main.py)
# ──────────────────────────
FRAME_RATE = 10                    # Hz (100ms per frame)
NUM_TARGETS = 3                    # Default scenario
SENSOR_ID = "PHOENIX_RADAR_01"
EFFECTOR_ID = "COGNITIVE_EW_01"


# PERFORMANCE NOTES
# ─────────────────
Total startup:          ~3 seconds
Per-frame budget:       100ms (10 Hz)
Used per frame:         ~55ms (radar + EW + state)
Headroom:              ~45ms (45%)


# LINKS & REFERENCES
# ──────────────────
Main Documentation:    MAIN_ENTRY_POINT.md
Deployment Guide:      DEPLOYMENT_GUIDE.py
Architecture Audit:    AUDIT_REPORT.md
GitHub:                https://github.com/nikhilkrishnanek2002-cpu/photonic-radar-ai


# COMMON COMMANDS
# ───────────────

# Start fresh instance with logging
function phoenix_run {
    cd /home/nikhil/PycharmProjects/photonic-radar-ai
    python3 main.py "$@"
}

# Check if system is healthy
function phoenix_health {
    curl -s http://localhost:5000/health | jq
}

# Watch system state
function phoenix_watch {
    watch -n 1 'curl -s http://localhost:5000/state | jq | head -50'
}

# Clean all logs
function phoenix_clean {
    rm -f photonic-radar-ai/runtime/logs/*.log
    rm -f photonic-radar-ai/runtime/shared_state.json
    echo "✓ Cleaned"
}

# Full reset
function phoenix_reset {
    pkill -f "python3 main.py"
    sleep 1
    phoenix_clean
    echo "✓ Reset complete"
}


# QUICK TESTS
# ───────────

# Test 1: Syntax check
python3 -m py_compile photonic-radar-ai/main.py && echo "✓ Syntax OK" || echo "✗ Syntax Error"

# Test 2: Import check
python3 -c "
import sys
sys.path.insert(0, 'photonic-radar-ai')
from subsystems import EventBusSubsystem, RadarSubsystem
print('✓ Imports OK')
" || echo "✗ Import Error"

# Test 3: API available
timeout 1 python3 main.py --api-only > /dev/null 2>&1 &
sleep 2
curl -s http://localhost:5000/health > /dev/null && echo "✓ API OK" || echo "✗ API Error"
pkill -f "main.py"

# Test 4: Full startup
python3 main.py &
PID=$!
sleep 3
curl -s http://localhost:5000/state | jq .system.health > /dev/null && echo "✓ System OK" || echo "✗ System Error"
kill $PID


# RESOURCES
# ─────────
# Python:   https://www.python.org/
# Numpy:    https://numpy.org/
# Flask:    https://flask.palletsprojects.com/
# Streamlit: https://streamlit.io/
# Docker:   https://www.docker.com/
# K8s:      https://kubernetes.io/


# SUPPORT
# ───────
# Issues:   https://github.com/nikhilkrishnanek2002-cpu/photonic-radar-ai/issues
# Email:    nikhil@example.com
# Discord:  https://discord.gg/example


# =============================================================================
# Generated: 2026-02-18
# Last Updated: 2026-02-18
# =============================================================================
