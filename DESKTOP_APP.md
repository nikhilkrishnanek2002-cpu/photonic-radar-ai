# Photonic Radar AI - Desktop Application

## Quick Start

The desktop application provides a unified interface to manage and monitor the Photonic Radar AI system with a single click.

### Run Desktop App

```bash
python run_desktop.py
```

This launches the desktop GUI with:
- ✅ System control buttons (Start/Stop/Restart)
- ✅ Real-time CPU/Memory monitoring
- ✅ System health indicators
- ✅ API & Dashboard access buttons
- ✅ Live console output
- ✅ Process management

### What the Desktop App Does

When you click **"▶ Start System"**, the desktop app:

1. **Launches Backend** - Starts `main.py` as a background process
2. **Monitors Startup** - Waits for API server to be ready (localhost:5000)
3. **Tracks Metrics** - Shows real-time CPU, memory usage
4. **Detects Dashboard** - Waits for Streamlit dashboard (localhost:8501)
5. **Enables Controls** - Activates "Open Dashboard" and "API Docs" buttons
6. **Live Logging** - Streams backend output to console panel

---

## Desktop Application Features

### 🎮 System Control Panel

| Button | Action |
|--------|--------|
| **▶ Start System** | Launch backend with API + Dashboard |
| **⏹ Stop System** | Graceful shutdown of all services |
| **🔄 Restart System** | Stop and start again |
| **📊 Open Dashboard** | Opens Streamlit UI in browser |
| **🔌 API Docs** | Opens FastAPI documentation |

### 📊 System Status Indicators

Real-time status of three critical components:

```
🟢 Backend       : Ready / Offline
🟢 API Server (5000) : Ready / Offline  
🟢 Dashboard (8501)  : Ready / Offline
```

### 📈 System Metrics

Monitor live system performance:

```
┌─────────────────────────────────┐
│ CPU Usage: 12.5% ████░░░░░░░░░░ │
│ Memory: 2,048 MB (25.4%) ███░░░░ │
│ Uptime: 00:05:32                │
└─────────────────────────────────┘
```

### 📝 System Console

Live streaming console output from backend:

```
[21:17:45] Starting system...
[21:17:46] Event Bus initialized
[21:17:47] Radar Subsystem ready
[21:17:48] EW Pipeline active
[21:17:49] ✓ System ready
```

### 🟢 Health Status

Shows current system health:

```
Status: RUNNING
✓ System operational
```

---

## Build Executable

Package the desktop app as a standalone executable for distribution.

### Linux / macOS

```bash
bash build_desktop.sh
```

**Output:** `dist/PhotonicRadarAI`

### Windows

```cmd
build_desktop.bat
```

**Output:** `dist\PhotonicRadarAI.exe`

### What the Build Script Does

1. Activates Python virtual environment
2. Installs PyInstaller (if needed)
3. Creates standalone executable
4. Bundles Python runtime + dependencies
5. Includes all project assets and configs

---

## Desktop App Architecture

### Project Structure

```
app/
  __init__.py              # Package init
  desktop/
    __init__.py           # Desktop module
    main_window.py        # Main Qt GUI window
    launcher.py           # Backend process manager
    system_monitor.py     # System metrics collector

run_desktop.py            # Entry point script

photonic_radar_desktop.spec  # PyInstaller configuration
build_desktop.sh          # Linux/macOS build script
build_desktop.bat         # Windows build script
```

### Component Overview

#### **main_window.py** - Main GUI Application
- PySide6-based Qt application
- Controls layout, widgets, styling
- Dark theme with professional look
- Multiple panels:
  - Control buttons
  - Status indicators
  - Metrics visualization
  - Console output

#### **launcher.py** - Backend Process Manager
- Launches/stops `main.py` subprocess
- Handles graceful shutdown
- Waits for API server ready
- Detects Streamlit dashboard availability
- Opens browsers automatically

#### **system_monitor.py** - System Metrics
- Real-time CPU/memory monitoring
- Process health checking
- Port availability detection
- Background monitoring thread
- Callback-based metric updates

---

## Configuration

### Desktop App Settings

Edit `app/desktop/main_window.py` to customize:

```python
# Window size
self.resize(1200, 800)

# Theme colors
"background-color: #1e1e1e"  # Dark background
"color: #00ff00"             # Green text
```

### Backend Configuration

The desktop app launches `main.py` with `--ui` flag:

```python
cmd = [python_exe, str(self.main_script), "--ui"]
```

This enables:
- API server on localhost:5000
- Streamlit dashboard on localhost:8501

---

## Troubleshooting

### Desktop App Won't Start

**Error:** `ModuleNotFoundError: No module named 'PySide6'`

**Solution:**
```bash
pip install PySide6
```

### Backend Process Won't Start

**Check:** Backend logs at `photonic-radar-ai/runtime/logs/phoenix_radar.log`

**Solution:**
1. Manually test: `bash start.sh`
2. Check Python version: `python --version` (requires 3.11+)
3. Verify dependencies: `pip list | grep -E "numpy|scipy|torch"`

### Dashboard Not Opening

**Issue:** Click "📊 Open Dashboard" but nothing happens

**Solution:**
1. Wait 5-10 seconds for Streamlit to start
2. Manually visit: http://localhost:8501
3. Check console output for errors

### Port Already in Use

**Error:** Address already in use (localhost:5000 or 8501)

**Solution:**
1. Kill existing process: `pkill -f "python main.py"`
2. Or use different ports by editing `app/desktop/launcher.py`

### Auto-detection Not Working

If system status shows offline but backend is running:

1. Check localhost:5000 manually:
   ```bash
   curl http://localhost:5000/health
   ```

2. If API responds, restart desktop app

3. If API doesn't respond, check backend logs:
   ```bash
   tail -f photonic-radar-ai/runtime/logs/phoenix_radar.log
   ```

---

## Advanced Features

### Accessing from Network

To access dashboard from another machine:

1. Find your IP:
   ```bash
   hostname -I  # Linux
   ipconfig     # Windows
   ```

2. Access from remote machine:
   ```
   http://<your-ip>:8501
   ```

3. API available at:
   ```
   http://<your-ip>:5000
   ```

### System Monitoring via Desktop App

The desktop app continuously monitors:

- **Backend Process** - Running state and PID
- **CPU Usage** - Real-time percentage
- **Memory Usage** - MB and percentage
- **Port Availability** - API and Dashboard readiness
- **Process Health** - Detects unexpected termination

### Custom Logging

Logs are stored at:

```
photonic-radar-ai/runtime/logs/phoenix_radar.log
photonic-radar-ai/runtime/desktop_backend.log
```

View live logs:

```bash
tail -f photonic-radar-ai/runtime/logs/phoenix_radar.log
```

---

## Distribution

### Create Installer (Windows)

```bash
# After building executable:
cd dist
# Create Windows installer with NSIS or similar tool
```

### Create DMG (macOS)

```bash
# After PyInstaller creates app bundle:
hdiutil create -volname PhotonicRadarAI -srcfolder dist/PhotonicRadarAI.app -ov -format UDZO PhotonicRadarAI.dmg
```

### Create Snap Package (Linux)

```bash
# Configure snapcraft.yaml and build:
snapcraft
```

---

## Performance

- **Startup Time:** ~3-5 seconds (after first launch)
- **Memory Usage:** ~150-200 MB (GUI + monitoring)
- **CPU Usage:** <1% idle, varies with simulation load
- **Monitoring Refresh Rate:** 1 update per second

---

## Integration with Backend

### How Desktop App Controls Backend

```
User clicks "Start" 
    ↓
launcher.py spawns main.py subprocess
    ↓
Waits for API port 5000 to respond
    ↓
Waits for Dashboard port 8501 to respond
    ↓
Updates UI status to "RUNNING"
    ↓
system_monitor.py tracks health continuously
```

### Backend Event Flow

```
main.py starts
    ↓
Event Bus initialized
    ↓
Radar Subsystem running
    ↓
EW Pipeline active
    ↓
API server listening (5000)
    ↓
Dashboard available (8501)
    ↓
Simulation loop running
```

---

## Development

### Modifying Desktop App

To make changes to the GUI:

1. Edit `app/desktop/main_window.py`
2. Run: `python run_desktop.py`  
3. Test changes
4. Rebuild: `bash build_desktop.sh`

### Adding New Controls

Example: Add new button to control panel

```python
# In main_window.py, init_ui() method:

self.custom_button = QPushButton("🎯 Custom Action")
self.custom_button.clicked.connect(self.custom_action)
button_layout.addWidget(self.custom_button)

# Add handler:
def custom_action(self):
    self.console.log("Custom action triggered")
```

### Debugging

Run with debug output:

```bash
PYTHONUNBUFFERED=1 python -u run_desktop.py
```

---

## Support

For issues or questions:

1. Check console output in desktop app for error messages
2. Review backend logs: `photonic-radar-ai/runtime/logs/phoenix_radar.log`
3. Test backend manually: `bash start.sh`
4. Verify dependencies: `pip list | grep -E "PySide6|psutil"`

---

## Summary

| Task | Command |
|------|---------|
| **Run Desktop App** | `python run_desktop.py` |
| **Build Executable** | `bash build_desktop.sh` (Linux/macOS) or `build_desktop.bat` (Windows) |
| **View Backend Logs** | `tail -f photonic-radar-ai/runtime/logs/phoenix_radar.log` |
| **Test Backend** | `bash start.sh` |
| **Install Dependencies** | `pip install -r requirements.txt` |

---

**Photonic Radar AI Desktop Application** 🛰️✈️
