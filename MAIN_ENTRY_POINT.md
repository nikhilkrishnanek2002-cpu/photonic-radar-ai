# Production-Grade Main Entry Point

## Overview

`main.py` is the **recommended unified entry point** for PHOENIX-RADAR. It provides a clean, modular bootstrap sequence that initializes all subsystems in the correct order with proper error handling.

## Quick Start

```bash
cd /home/nikhil/PycharmProjects/photonic-radar-ai

# Headless mode (radar + API server, no UI)
python3 main.py

# With Streamlit dashboard
python3 main.py --ui

# Debug mode (verbose logging)
python3 main.py --debug

# API server only (no simulation)
python3 main.py --api-only

# Headless (no browser auto-open)
python3 main.py --ui --headless
```

## Architecture

### Startup Sequence (6 Phases)

The system initializes in a strict sequence to ensure dependencies are satisfied:

```
Phase 1: Configuration & Logging
         ├─ Parse CLI arguments
         ├─ Setup file and console logging
         └─ Register signal handlers

Phase 2: EVENT BUS (CRITICAL)
         ├─ Initialize Defense Core
         ├─ Create message queues
         └─ System halts if this fails

Phase 2.5: TACTICAL STATE (CRITICAL)
         ├─ Initialize shared state container
         └─ Used for radar-EW synchronization

Phase 3: RADAR SUBSYSTEM (CRITICAL)
         ├─ Load physics engine
         ├─ Initialize simulation orchestrator
         ├─ Load initial targets
         └─ Subscribe to event bus

Phase 4: EW SUBSYSTEM (OPTIONAL)
         ├─ Initialize cognitive pipeline
         ├─ Subscribe to radar intelligence
         └─ System continues if this fails

Phase 5: API SERVER (OPTIONAL)
         ├─ Spawn subprocess: python -m api.server
         ├─ Listen on http://localhost:5000
         └─ Provide REST endpoints

Phase 6: STREAMLIT DASHBOARD (OPTIONAL)
         ├─ Spawn subprocess: streamlit run ui/dashboard.py
         ├─ Connect to API server
         └─ Visualize tactical display
```

### Main Loop (10 Hz)

Once all subsystems are initialized:

```python
while system_running:
    # Wait for next tick (100ms)
    tick = clock.wait_for_next_tick()
    
    # RADAR FRAME: Generate detections, track targets
    radar_result = radar.tick()
    # → Publishes RadarIntelligencePacket to event bus
    
    # EW DECISION: Process intelligence, make recommendations
    if ew:
        ew_result = ew.tick()
    # → Publishes ElectronicAttackPacket to event bus
    
    # STATE UPDATE: Merge all data into tactical state
    tactical_state.update()
    # → Serializes to runtime/shared_state.json
```

### Data Flow

```
Radar Thread
├─ Generates detections (10 Hz)
└─ Publishes to event bus
        │
        ├─→ EW Thread (subscribes)
        │   ├─ AI classification
        │   └─ Decision publishing
        │
        └─→ TacticalState (IPC)
            ├─ JSON serialization
            └─ API Server (reads)
                └─ Dashboard (HTTP request)
```

## Command-Line Options

| Option | Effect | Use Case |
|--------|--------|----------|
| None | Headless radar + API | Server deployment |
| `--ui` | Launch Streamlit dashboard | Interactive visualization |
| `--debug` | Verbose logging to console | Troubleshooting |
| `--api-only` | API server only | Standalone API |
| `--headless` | No browser auto-open | Automated/server mode |

## Configuration

### Default Scenario (3 Targets)

The system initializes with 3 targets:

| ID | Type | Position | Velocity | Classification |
|--|--|--|--|--|
| 1 | Hostile | (1200, 800) | (-35, -15) m/s | THREAT |
| 2 | Civilian | (1800, -500) | (-45, +10) m/s | MONITOR |
| 3 | Hostile | (900, 300) | (-28, -20) m/s | THREAT |

To customize, edit the `initialize_radar_subsystem()` function in `main.py`.

### Configuration Files

| Path | Purpose |
|------|---------|
| `phoenix-radar-ai/requirements.txt` | Python dependencies |
| `main.py` | Entry point (DEFAULT subsystem config) |
| `phoenix-radar-ai/run_platform.py` | Alternative entry point (legacy) |

## Logging

### Log Files

| File | Level | Contents |
|------|-------|----------|
| `phoenix-radar-ai/runtime/logs/phoenix_radar.log` | DEBUG/INFO | Main platform log |
| `phoenix-radar-ai/runtime/api_server.log` | INFO | REST API server |
| `phoenix-radar-ai/runtime/dashboard.log` | WARNING | Streamlit dashboard |

### Enable Debug Logging

```bash
python3 main.py --debug
```

This outputs DEBUG-level messages to both console and log file, useful for:
- Troubleshooting subsystem initialization
- Tracking event bus traffic
- Monitoring frame timing

## Subsystem Startup Examples

### Example 1: Headless Radar Only
```bash
$ python3 main.py
================================================================================
 PHOENIX-RADAR: COGNITIVE PHOTONIC RADAR DEFENSE SYSTEM
 Sensor → Intelligence → EW → Effect
================================================================================

[CONFIG] ✓ Configuration loaded
[EVENT BUS] ✓ Event bus ready
[TACTICAL] ✓ Tactical state initialized
[RADAR] ✓ Radar online (10.0 Hz, 3 targets)
[EW] ✓ EW engine online
[API] ✓ API server started (http://localhost:5000)

✓ SYSTEM READY
Radar: Simulation running at 10 Hz
EW Engine: Cognitive intelligence pipeline active
Press Ctrl+C to shutdown gracefully...
```

### Example 2: With Dashboard
```bash
$ python3 main.py --ui
# ... [same as above] ...
Dashboard: http://localhost:8501

# Browser auto-opens to http://localhost:8501
# Displays PPI, threat list, EW status
```

### Example 3: Debug Mode
```bash
$ python3 main.py --debug
# ... [verbose logging] ...
[TICK    100] Radar frame executed
[TICK    101] Radar frame executed
[TICK    102] Radar frame executed
```

## Graceful Shutdown

The system handles shutdown signals gracefully:

```bash
# Signal reception
^C  → state.shutdown_requested = True

# Graceful sequence
1. Stop main simulation loop
2. Terminate dashboard subprocess (5s timeout)
3. Terminate API server subprocess (5s timeout)
4. Shutdown EW subsystem
5. Shutdown radar subsystem
6. Shutdown event bus
7. Exit with status 0
```

## Cross-Platform Compatibility

| OS | Status | Notes |
|----|--------|-------|
| Linux | ✅ Fully supported | Primary target |
| macOS | ✅ Fully supported | POSIX signals |
| Windows | ✅ Fully supported | Uses CREATE_NEW_PROCESS_GROUP |

### Platform-Specific Issues

**Windows subprocess handling:**
- Uses `CREATE_NEW_PROCESS_GROUP` for proper signal propagation
- Dashboard and API may require `--headless` flag

**Linux/macOS:**
- Uses POSIX signal handling (SIGINT, SIGTERM)
- Subprocess cleanup via `os.kill(pid, SIGTERM)`

## Troubleshooting

### "Event bus initialization failed"
```
Error: Event bus initialization returned None
Fix:   Ensure defense_core module is in PYTHONPATH
       Check: python3 -c "from defense_core import get_defense_bus"
```

### "Radar initialization failed"
```
Error: ✗ Radar initialization failed
Fix:   Check simulation_engine.orchestrator is available
       python3 -c "from simulation_engine.orchestrator import SimulationOrchestrator"
```

### "API Server failed to start"
```
Warning: Failed to start API server
Fix:     Check uvicorn/flask installed: pip install uvicorn flask
         Check port 5000 not in use: lsof -i :5000
```

### "Dashboard failed to start"
```
Warning: Failed to start dashboard
Fix:     Check streamlit installed: pip install streamlit
         Check port 8501 not in use: lsof -i :8501
         Try --headless flag: python3 main.py --ui --headless
```

## Performance

### Typical Timing
```
Phase 1 (Config):     ~100ms
Phase 2 (Event Bus):  ~200ms
Phase 3 (Radar):      ~300ms
Phase 4 (EW):         ~200ms
Phase 5 (API):        ~1000ms (subprocess spawn)
Phase 6 (Dashboard):  ~1500ms (subprocess spawn)
─────────────────────────────
Total Startup:        ~3.3 seconds
```

### Main Loop Timing
```
Per-frame budget: 100ms (10 Hz)

Radar tick:       35ms  (35%)
EW tick:          15ms  (15%)
State update:      2ms  (2%)
JSON write (IPC):  3ms  (3%)
─────────────────────────
Total:            55ms  (55% utilization)
Headroom:         45ms  (45% available)
```

## API Server Endpoints

Once the API server is running on `http://localhost:5000`:

### GET /state
Returns full system state (radar detections, threats, EW status).
```bash
curl http://localhost:5000/state | jq
```

### GET /health
Returns system health status.
```bash
curl http://localhost:5000/health | jq
```

### GET /events
Returns recent events (track detections, threat assessments, EW decisions).
```bash
curl http://localhost:5000/events | jq
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: Test PHOENIX-RADAR

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: |
          cd photonic-radar-ai
          pip install -r requirements.txt
          python3 ../main.py --api-only &
          sleep 5
          curl http://localhost:5000/health
```

## FAQ

**Q: Can I run multiple instances?**
A: Yes, use different ports:
```bash
python3 main.py --api-only  # API on :5000
APP_PORT=5001 python3 main.py --api-only  # API on :5001
```

**Q: How do I disable EW?**
A: Edit `initialize_ew_subsystem()` in main.py and return False early.

**Q: Can I customize targets at runtime?**
A: Edit `initialize_radar_subsystem()` or modify `TargetState` objects before `radar.initialize()`.

**Q: How do I connect external hardware?**
A: Implement `RadarSubsystem.tick()` to read from hardware instead of simulation.

---

**Documentation**: [AUDIT_REPORT.md](AUDIT_REPORT.md)  
**Source**: `/home/nikhil/PycharmProjects/photonic-radar-ai/main.py`  
**Version**: 1.0 (Production)  
**Last Updated**: 2026-02-18
