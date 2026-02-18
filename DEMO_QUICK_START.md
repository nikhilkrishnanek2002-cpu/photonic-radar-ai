# Quick Reference: Running the PHOENIX Demo

## Fastest Start
```bash
cd /home/nikhil/PycharmProjects/photonic-radar-ai
python demo.py
```

✅ Runs 20-second demo with 3 synthetic targets
✅ Shows real-time detections, tracks, threats
✅ Displays comprehensive statistics
✅ No external services needed

## Common Commands

### 10-Second Demo (Quick Test)
```bash
python demo.py --duration 10
```

### 60-Second Demo (Full Scenario)
```bash
python demo.py --duration 60
```

### Debug Mode (See All Details)
```bash
python demo.py --verbose
```

### Extended Run (5 Minutes)
```bash
python demo.py --duration 300
```

### Custom Duration + Debug
```bash
python demo.py --duration 60 --verbose
```

## Output Sections

### 1. Initialization (First 5 lines)
```
[EVENT BUS] Initializing... ✓
[TACTICAL STATE] Initializing... ✓
[RADAR SUBSYSTEM] Initializing... ✓
[EW SUBSYSTEM] Initializing... ✓
✓ All systems initialized and ready
```

### 2. Live Detection Stream
```
[DETECTION] Frame  1234 | Track # 1 | Range: 1200.5m | Azimuth: 45.2° | Velocity: -35.0m/s | SNR: 28.5dB | Quality: 0.95
[THREAT] Frame  1234 | Track # 1 | Class: HOSTILE | Priority: 9/10 | Confidence: 92.5% | Action: ENGAGE
[EW DECISION] Frame  1234 | Decision #15 | Status: ENGAGING
```

### 3. Summary Every 10 Frames
```
[SUMMARY] Frame  1234 | Tracks: 3 | Threats: 2 | Detections: 45 | EW Decisions: 15 | Avg SNR: 22.5dB
```

### 4. Final Statistics
```
Statistics:
  Total frames: 200
  Total detections: 1245
  Total threats: 89
  Elapsed time: 20.1s
  Avg frame time: 42.35ms
  Utilization: 42.3%
```

## System Components Active

| Component | Status | Purpose |
|-----------|--------|---------|
| Event Bus | ✅ Active | Message backbone |
| Radar | ✅ Active | Signal processing |
| Kalman Tracking | ✅ Active | Multi-target tracking |
| CFAR Detection | ✅ Active | Adaptive thresholds |
| EW Engine | ✅ Active | Threat classification |
| Cognitive AI | ✅ Active | Decision making |

## What You're Seeing

### Detections (CYAN)
- Real-time radar returns
- Position, velocity, quality
- Physical measurements

### Threats (Color-coded)
- 🔴 RED = HOSTILE (engage)
- 🟡 YELLOW = UNKNOWN (monitor)
- 🟢 GREEN = NEUTRAL/FRIENDLY (low threat)

### EW Decisions
- SCANNING = Passive watch
- ENGAGING = Active countermeasures

## Synthetic Scenario

3 aircraft are simulated:
1. **HOSTILE** - Military configuration (high threat)
2. **NEUTRAL** - Civilian aircraft (medium threat)
3. **CIVILIAN** - Light aircraft (low threat)

System tracks all three, classifies threats, and makes EW recommendations.

## Frames & Timing

- **Frame Rate**: 10 Hz (every 100ms)
- **Example**: 20-second demo = 200 frames
- **Duration = 10**: 2 seconds (20 frames)
- **Duration = 300**: 30 seconds (300 frames)

## Color Output

```
CYAN  = Detection data
RED   = HOSTILE threat
YELLOW = UNKNOWN threat
GREEN = Friendly/neutral
BLUE  = General info
BOLD  = Headers/summaries
```

## Typical Performance

| Metric | Value |
|--------|-------|
| Frame time | 40-50ms |
| CPU usage | 40-50% |
| Memory | ~150MB |
| Responsiveness | Real-time |

## Options Summary

```
--duration N    How long to run (seconds)
--verbose       Show debug/detailed output
-h, --help      Show help message
```

## Examples

```bash
# Basic (default 20 seconds)
python demo.py

# Quick test
python demo.py --duration 5

# Extended scenario
python demo.py --duration 120

# With debugging
python demo.py --verbose

# Long run with debug
python demo.py --duration 60 --verbose

# Save output
python demo.py --duration 30 > output.txt

# Display + save
python demo.py --duration 30 | tee demo_log.txt

# Only summaries
python demo.py | grep SUMMARY
```

## Troubleshooting

### No detections showing?
Wait 5-10 frames for first detections

### Too much output?
Use: `python demo.py | head -100`

### Want to see everything?
Use: `python demo.py --verbose | head -200`

### Save it?
Use: `python demo.py > file.txt 2>&1`

## File Location

```
/home/nikhil/PycharmProjects/photonic-radar-ai/demo.py
```

## Key System Features Demonstrated

✅ Physics-based radar simulation
✅ Multi-target Kalman tracking  
✅ Adaptive CFAR detection
✅ Real-time event messaging
✅ AI threat classification
✅ Cognitive adaptive intelligence
✅ Electronic warfare decisions
✅ Closed-loop feedback control

## Next Steps

1. **Run demo** - `python demo.py`
2. **Check output** - Observe detections and threats
3. **Analyze stats** - Review final statistics
4. **Try variations** - `python demo.py --duration 60`
5. **Read details** - See DEMO_GUIDE.md for full documentation

---

**That's it! You're now running the complete PHOENIX Radar AI system.**
