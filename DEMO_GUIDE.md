# PHOENIX Radar AI - Full System Demonstration

## Overview

`demo.py` is a comprehensive demonstration of the PHOENIX Radar AI system that showcases all major components working together:

1. **Event Bus** (Defense Core) - Real-time messaging backbone
2. **Radar Subsystem** - Physics-based signal processing and detection
3. **Signal Processing Pipeline** - CFAR detection and Kalman tracking
4. **Cognitive Intelligence Engine** - AI-based threat classification
5. **Electronic Warfare (EW)** - Decision-making and adaptation

## Features

✅ **Fully Synthetic** - No hardware or external services required
✅ **Physics-Based** - Real radar effects (Doppler, SNR, clutter)
✅ **Real-Time Processing** - 10 Hz simulation with 100ms frame timing
✅ **Kalman Filtering** - Multi-target tracking with state estimation
✅ **AI Classification** - Threat assessment and anomaly detection
✅ **Event Publishing** - Defense core message bus integration
✅ **Console Visualization** - Color-coded real-time output

## Quick Start

### Basic Usage
```bash
cd /home/nikhil/PycharmProjects/photonic-radar-ai
python demo.py
```

**Output:** 20-second demo with synthetic 3-target scenario

### Extended Duration
```bash
python demo.py --duration 60
```

**Output:** 60-second demo (600 frames at 10 Hz)

### Verbose Debug Mode
```bash
python demo.py --verbose
```

**Output:** Includes DEBUG logging from all subsystems

### Combined Options
```bash
python demo.py --duration 30 --verbose
```

**Output:** 30 seconds with full debug output

## Output Format

### Detection Messages
```
[DETECTION] Frame  1234 | Track # 1 | Range: 1200.5m | Azimuth: 45.2° | Velocity: -35.0m/s | SNR: 28.5dB | Quality: 0.95
```

**Fields:**
- **Frame**: Simulation frame number (0.1s per frame)
- **Track**: Unique target identifier
- **Range**: Distance in meters
- **Azimuth**: Bearing in degrees (0-360)
- **Velocity**: Radial velocity (Doppler-derived)
- **SNR**: Signal-to-noise ratio in dB
- **Quality**: Track quality confidence (0.0-1.0)

### Threat Messages
```
[THREAT] Frame  1234 | Track # 1 | Class: HOSTILE | Priority: 9/10 | Confidence: 92.5% | Action: ENGAGE
```

**Fields:**
- **Class**: Classification (HOSTILE, UNKNOWN, NEUTRAL, FRIENDLY)
- **Priority**: Threat level (0-10)
- **Confidence**: Classification confidence
- **Action**: EW recommendation (ENGAGE, MONITOR, IGNORE)

### EW Decision Messages
```
[EW DECISION] Frame  1234 | Decision #15 | Status: ENGAGING
```

**Status Values:**
- SCANNING: Passive surveillance mode
- ENGAGING: Active countermeasure deployment

### Summary Statistics
```
[SUMMARY] Frame  1234 | Tracks: 3 | Threats: 2 | Detections: 45 | EW Decisions: 15 | Avg SNR: 22.5dB
```

**Aggregates per 10 frames:**
- **Tracks**: Number of active tracks
- **Threats**: Number of identified threats
- **Detections**: Cumulative detections
- **EW Decisions**: Countermeasure decisions made
- **Avg SNR**: Average signal quality

## Color Coding

The console output uses colors to indicate system state:

- 🔵 **CYAN** (`[DETECTION]`) - New target detection
- 🔴 **RED** (`[THREAT]`) - HOSTILE classification
- 🟡 **YELLOW** (`[THREAT]`) - UNKNOWN classification
- 🟢 **GREEN** (`[THREAT]`) - NEUTRAL/FRIENDLY classification
- 🔵 **BLUE** (`[THREAT]`) - Generic threat info
- 🔴 **RED** (`[EW DECISION]`) - ENGAGING status (active)
- 🟢 **GREEN** (`[EW DECISION]`) - SCANNING status (passive)

## System Architecture Demonstrated

### Phase 1: Initialization
1. **Event Bus Creation** - Defense core message backbone
2. **Tactical State** - Shared state management
3. **Radar Subsystem** - Physics simulation engine
4. **EW Subsystem** - Cognitive intelligence pipeline

### Phase 2: Processing Loop (10 Hz)
```
┌─────────────────────────────────────────┐
│ Frame Start (100ms slot)                │
├─────────────────────────────────────────┤
│ 1. RADAR TICK (~35ms)                   │
│    ├─ Generate synthetic targets        │
│    ├─ Simulate RF signals               │
│    ├─ Add noise/clutter                 │
│    ├─ Detection threshold (CFAR)        │
│    ├─ Kalman tracking                   │
│    └─ Publish to event bus              │
├─────────────────────────────────────────┤
│ 2. EW TICK (~15ms)                      │
│    ├─ Ingest radar detections           │
│    ├─ Run AI models                     │
│    ├─ Classify threats                  │
│    ├─ Generate decisions                │
│    └─ Publish to event bus              │
├─────────────────────────────────────────┤
│ 3. STATE UPDATE (~2ms)                  │
│    ├─ Merge radar data                  │
│    ├─ Merge EW results                  │
│    ├─ Update shared state               │
│    └─ Serialize to JSON (IPC)           │
├─────────────────────────────────────────┤
│ 4. TIMING SYNC                          │
│    └─ Sleep to 100ms boundary           │
└─────────────────────────────────────────┘
```

## Synthetic Scenario

The demo initializes 3 synthetic targets:

### Target 1: HOSTILE Aircraft
- **Position**: 1200m North, 800m East
- **Velocity**: -35 m/s North, -15 m/s West
- **Type**: Hostile military platform
- **Expected Classification**: HIGH threat priority

### Target 2: NEUTRAL Aircraft
- **Position**: 1800m North, -500m West
- **Velocity**: -45 m/s South, +10 m/s West
- **Type**: Neutral civilian aircraft
- **Expected Classification**: MEDIUM threat priority

### Target 3: CIVILIAN Aircraft
- **Position**: 900m North, 300m East
- **Velocity**: -28 m/s South, -20 m/s West
- **Type**: Civilian light aircraft
- **Expected Classification**: LOW threat priority

## Performance Metrics

The demo tracks and reports:

- **Total Frames**: Number of simulation cycles
- **Total Detections**: Cumulative radar detections
- **Total Threats**: Cumulative threat assessments
- **Elapsed Time**: Wall-clock duration
- **Avg Frame Time**: Average processing per frame (ms)
- **Utilization**: CPU usage as % of frame budget

### Expected Performance

| Metric | Value |
|--------|-------|
| Frame Rate | 10 Hz |
| Frame Budget | 100 ms |
| Avg Frame Time | 35-45 ms |
| CPU Utilization | 35-45% |
| Memory Usage | ~150 MB |
| Zero Detections Before | 5-10 frames |

## Event Bus Integration

The demo fully exercises the event bus:

### Published Events
- `RadarIntelligencePacket` - Detections and tracks
- `ElectronicAttackPacket` - EW decisions

### Consumed Events
- EW ingests radar detections
- Radar can respond to EW feedback

### Queue Monitoring
Final summary includes event bus queue depths and message counts.

## Customization

### Changing Duration
```python
# Default: 20 seconds
python demo.py --duration 120  # 120 seconds (1200 frames)
```

### Modifying Target Scenario
Edit the targets in `initialize_system()`:

```python
targets = [
    TargetState(
        id=1, 
        pos_x=1500.0,  # X position (meters)
        pos_y=1000.0,  # Y position (meters)
        vel_x=-40.0,   # X velocity (m/s)
        vel_y=-20.0,   # Y velocity (m/s)
        type="hostile"  # Type: hostile/neutral/civilian
    ),
    # Add more targets...
]
```

### Adjusting Frame Rate
Edit radar configuration:

```python
radar_config = {
    'frame_dt': 0.05,  # 50ms = 20 Hz instead of 100ms
    # ...
}
```

### Output Redirection
```bash
# Save to file
python demo.py --duration 30 > demo_output.txt 2>&1

# Stream to file while displaying
python demo.py --duration 30 | tee demo_output.txt

# Quiet mode (statistics only)
python demo.py --duration 30 2>/dev/null | grep "^\[SUMMARY\]"
```

## Troubleshooting

### Import Errors
**Error:** `ModuleNotFoundError: No module named 'defense_core'`

**Solution:**
```bash
# Ensure you're in the project directory
cd /home/nikhil/PycharmProjects/photonic-radar-ai

# Check PYTHONPATH
python -c "import sys; print(sys.path)"

# Run with explicit path
PYTHONPATH=. python demo.py
```

### No Detections Appearing
**Issue:** Running but no detection output after 10+ seconds

**Causes & Solutions:**
1. Targets too far away - Edit positions closer
2. SNR threshold too high - Check radar configuration
3. Physics engine not loaded - Check `simulation_engine` module

### High CPU Usage
**Issue:** CPU usage at 100%

**Solutions:**
1. Reduce duration: `python demo.py --duration 10`
2. Lower frame rate: Edit `frame_dt` to 0.2 (5 Hz)
3. Check system resources: `top`, `htop`

### Hanging/No Output
**Issue:** Demo starts but produces no output

**Likely Cause:** event bus initialization hanging

**Solution:**
```bash
# Run with timeout
timeout 5 python demo.py

# Or use verbose mode to see where it hangs
python demo.py --verbose 2>&1 | head -50
```

## Integration with Main System

The demo can run independently, but also coordinates with:

- `main.py` - Full system launcher
- `photonic-radar-ai/ui/dashboard.py` - Dashboard visualization
- REST API (`http://localhost:5000`) - External monitoring

### Running Alongside Main System

**Terminal 1:**
```bash
python demo.py --duration 300  # 5-minute demo
```

**Terminal 2:**
```bash
python main.py --api-only      # Just API server
```

**Terminal 3:**
```bash
streamlit run photonic-radar-ai/ui/dashboard.py
```

Dashboard will show generated synthetic radar data from demo.

## Code Structure

```python
demo.py
├── Colors                  # ANSI color codes
├── print_*()              # Formatted output functions
├── setup_logging()        # Configure logging
├── initialize_system()    # Subsystem initialization
├── run_demo()            # Main simulation loop
├── print_*_summary()     # Statistical summaries
└── main()                # Entry point
```

## Performance Analysis

### CPU Profile (Expected)
- Radar frame: ~35ms (35%)
- EW processing: ~8ms (8%)
- State updates: ~2ms (2%)
- Event bus: ~1ms (1%)
- **Total per frame**: ~46ms (46% of 100ms budget)
- **Headroom**: ~54ms available for extensions

### Memory Profile (Expected)
- Base system: ~80MB
- Event bus: ~20MB
- Radar buffers: ~40MB
- Detection history: ~15MB
- **Total**: ~150-200MB

## Advanced Topics

### Custom Target Trajectories
Targets can be modified to follow custom paths:

```python
# Add to initialize_system()
targets = [
    TargetState(id=1, pos_x=1000, pos_y=0, vel_x=-50, vel_y=0),
    TargetState(id=2, pos_x=2000, pos_y=500, vel_x=-30, vel_y=20),
]
```

### Scenario Recording
Save detection data for analysis:

```bash
python demo.py --duration 60 > scenario_detections.txt
grep "^\[DETECTION\]" scenario_detections.txt > tracks_only.txt
```

### Real-time Analysis
Pipe to analysis tools:

```bash
# Count detections per track
python demo.py | grep DETECTION | awk '{print $14}' | sort | uniq -c

# Extract high-priority threats
python demo.py | grep "Priority:  *[7-9]"
```

## Related Documentation

- **main.py** - Production-grade entry point
- **MAIN_ENTRY_POINT.md** - Detailed architecture
- **DEPLOYMENT_GUIDE.py** - System deployment
- **IMPLEMENTATION_SUMMARY.md** - Technical overview
- **dashboard.py** - Real-time visualization

## Summary

`demo.py` provides a **production-ready demonstration** of the complete PHOENIX Radar AI system, showcasing:

✅ Signal processing pipeline
✅ Multi-target tracking
✅ AI threat classification
✅ Real-time event messaging
✅ Cognitive adaptation
✅ Formation of integrated defense decisions

**No external dependencies beyond installed Python packages - fully self-contained and runnable anywhere.**

---

**Ready to demonstrate?** Simply run:
```bash
python demo.py
```
