# PHOENIX Demo - Files & Documentation Summary

## Core Demo Files

### 1. **demo.py** (17 KB, executable)
**Purpose:** Main demonstration script

**Features:**
- Complete system initialization
- 10 Hz simulation loop
- Synthetic target tracking
- Real-time console output
- Comprehensive statistics

**Usage:**
```bash
python demo.py
python demo.py --duration 60
python demo.py --verbose
```

**Output:** Color-coded detections, threats, and decisions in real-time

### 2. **demo_runner.sh** (4.5 KB, executable)
**Purpose:** Interactive helper script

**Features:**
- Menu-driven demo launcher
- Quick presets (10s, 20s, 60s, 5m)
- Custom duration option
- Debug mode toggle
- Output file saving
- Command-line shortcuts

**Usage:**
```bash
./demo_runner.sh                # Interactive menu
./demo_runner.sh quick          # 10-second demo
./demo_runner.sh extended       # 60-second demo
./demo_runner.sh debug          # With verbosity
```

## Documentation Files

### 3. **README_DEMO.md** (Comprehensive)
**Purpose:** Complete demo system documentation

**Sections:**
- Overview and features
- Installation and prerequisites
- Running the demo (all variations)
- Understanding output format
- System components breakdown
- Scenario overview
- Performance profile
- Command reference
- Advanced usage
- Integration with main system
- Troubleshooting guide
- Benchmarks and stress testing
- File structure
- Next steps

**Best for:** Comprehensive understanding of the demo system

### 4. **DEMO_GUIDE.md** (Technical)
**Purpose:** In-depth technical documentation

**Sections:**
- Features and architecture
- Quick start commands
- Output format and interpretation
- Color coding
- Subsystem descriptions
- Performance metrics
- Synthetic scenario details
- Customization options
- Troubleshooting solutions
- Integration with main system
- Code structure
- Advanced topics

**Best for:** Technical implementation details

### 5. **DEMO_QUICK_START.md** (Quick Reference)
**Purpose:** One-page quick reference

**Sections:**
- Fastest start (3 lines)
- Common commands
- Output sections explained
- System components status table
- What you're seeing
- Timing and frames
- Color output legend
- Performance expectations
- Options summary
- Examples
- Troubleshooting tips

**Best for:** Quick lookup while running demo

## Component Interaction

```
demo.py (Main Script)
│
├─→ Initialize Phase
│   ├─ Event Bus (Defense Core)
│   ├─ Tactical State
│   ├─ Radar Subsystem (3 targets)
│   └─ EW Subsystem
│
├─→ Main Loop (10 Hz)
│   ├─ Radar Tick (35ms): Physics simulation + tracking
│   ├─ EW Tick (15ms): AI classification + decisions
│   ├─ State Update (2ms): Merge data
│   └─ Frame Display (console output)
│
└─→ Statistics & Reporting
    ├─ Frame-by-frame output
    ├─ 10-frame summaries
    └─ Final statistics
```

## Quick Navigation

### "I want to..." → See this file

| Goal | File | Command |
|------|------|---------|
| Get started fast | DEMO_QUICK_START.md | `python demo.py` |
| Understand how it works | README_DEMO.md | Section: System Components |
| Troubleshoot issues | DEMO_GUIDE.md | Section: Troubleshooting |
| Technical deep-dive | DEMO_GUIDE.md | Full file |
| Use interactive menu | demo_runner.sh | `./demo_runner.sh` |
| Custom duration | README_DEMO.md | `python demo.py --duration N` |
| Debug mode | DEMO_GUIDE.md | `python demo.py --verbose` |
| Save output | demo_runner.sh | Option 7 in menu |
| Run continuously | README_DEMO.md | Performance benchmarks section |

## Running the Demo

### Absolute Quickest (3 commands)
```bash
cd /home/nikhil/PycharmProjects/photonic-radar-ai
python demo.py
# Observe output, wait 20 seconds, see final stats
```

### Using Helper Script
```bash
cd /home/nikhil/PycharmProjects/photonic-radar-ai
./demo_runner.sh quick
```

### Recommended First Time
```bash
python demo.py --duration 30 --verbose | head -200
cat README_DEMO.md | head -100
```

## What Each File Does

### demo.py Breakdown

```python
demo.py
│
├─ Colors class
│  └─ ANSI color codes for terminal
│
├─ Printing functions
│  ├─ print_header()           → Section headers
│  ├─ print_detection()        → Detection line
│  ├─ print_threat()           → Threat line
│  ├─ print_ew_decision()      → Decision line
│  └─ print_summary()          → Frame summaries
│
├─ System setup
│  ├─ setup_logging()          → Logging configuration
│  └─ initialize_system()      → All subsystems init
│
├─ Main demo loop
│  └─ run_demo()               → 10Hz simulation
│
├─ Reporting
│  └─ print_event_bus_summary()  → Queue statistics
│
└─ Entry point
   └─ main()                   → CLI parsing + orchestration
```

## Performance Expectations

### Expected Output Example
```
[EVENT BUS] Initializing... ✓
[TACTICAL STATE] Initializing... ✓
[RADAR SUBSYSTEM] Initializing... ✓
[EW SUBSYSTEM] Initializing... ✓

✓ All systems initialized and ready
Running for 20.0 seconds (200 frames at 10 Hz)...

[DETECTION] Frame     1 | Track # 1 | Range: 1200.5m | Azimuth:  45.2° | ...
[THREAT] Frame     1 | Track # 1 | Class: HOSTILE | Priority: 9/10 | ...
...
[SUMMARY] Frame    20 | Tracks: 3 | Threats: 2 | Detections: 45 | ...

Statistics:
  Total frames: 200
  Total detections: 1245
  Elapsed time: 20.1s
  Avg frame time: 42.35ms
  Utilization: 42.3%
```

## Command Cheat Sheet

```bash
# Basic
python demo.py                              # 20s default

# With options
python demo.py --duration 60                # 60 seconds
python demo.py --verbose                    # Debug output
python demo.py --duration 30 --verbose      # Combined

# Using helper
./demo_runner.sh                            # Menu
./demo_runner.sh quick                      # 10s
./demo_runner.sh extended                   # 60s

# Output handling
python demo.py > log.txt 2>&1              # Save
python demo.py | tee log.txt               # Show + save
python demo.py | grep DETECTION            # Filter detections
python demo.py | grep THREAT               # Filter threats
python demo.py | grep SUMMARY              # Summaries only

# Analysis
python demo.py 2>/dev/null | grep DETECTION | wc -l
python demo.py 2>/dev/null | grep THREAT | grep HOSTILE
```

## File Locations

```
/home/nikhil/PycharmProjects/photonic-radar-ai/
│
├─ Core Demo Files
│  ├─ demo.py                    (17 KB)
│  └─ demo_runner.sh             (4.5 KB)
│
├─ Documentation
│  ├─ README_DEMO.md             (Comprehensive)
│  ├─ DEMO_GUIDE.md              (Technical)
│  └─ DEMO_QUICK_START.md        (Quick ref)
│
├─ System Files
│  ├─ main.py                    (Production)
│  ├─ requirements.txt           (Dependencies)
│  └─ photonic-radar-ai/         (Modules)
│      ├─ subsystems/
│      ├─ simulation_engine/
│      ├─ defense_core/
│      ├─ cognitive/
│      └─ ui/
│
└─ Runtime
   └─ runtime/
       └─ shared_state.json      (IPC)
```

## Next Steps

1. **Today**: Run `python demo.py` to see it work
2. **Read**: DEMO_QUICK_START.md for overview
3. **Understand**: README_DEMO.md for details
4. **Experiment**: Try different durations and options
5. **Integrate**: Link with main.py and dashboard
6. **Extend**: Modify targets and scenarios

## Support Resources

| Question | Answer |
|----------|--------|
| How do I run it? | See DEMO_QUICK_START.md |
| What's the output? | See README_DEMO.md output format section |
| How do I troubleshoot? | See DEMO_GUIDE.md troubleshooting |
| What are the components? | See README_DEMO.md system components |
| Can I customize it? | See DEMO_GUIDE.md customization |
| What's the performance? | See README_DEMO.md performance profile |

## Summary

### Files Created
1. ✅ `demo.py` - Complete demonstration
2. ✅ `demo_runner.sh` - Helper script
3. ✅ `README_DEMO.md` - Comprehensive documentation
4. ✅ `DEMO_GUIDE.md` - Technical guide
5. ✅ `DEMO_QUICK_START.md` - Quick reference

### Capabilities Demonstrated
- ✅ Event bus (Defense Core) messaging
- ✅ Radar subsystem (signal processing)
- ✅ Kalman filtering (tracking)
- ✅ CFAR detection (adaptive thresholds)
- ✅ AI classification (threat assessment)
- ✅ EW decisions (countermeasures)
- ✅ Real-time 10 Hz processing
- ✅ Multi-target simultaneous tracking

### Ready to Go
```bash
python demo.py
```

Everything you need to demonstrate the complete PHOENIX Radar AI system!

---

**Documentation Complete** ✅
**System Demonstration Ready** ✅
**No External Dependencies** ✅
