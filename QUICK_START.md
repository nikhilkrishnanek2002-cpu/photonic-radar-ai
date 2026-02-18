# 🚀 Photonic Radar AI - Quick Start Guide

**For fresh machine setup → production ready in 5 minutes**

---

## 📋 Prerequisites

- **Python 3.11+** (Download from [python.org](https://www.python.org/downloads/))
- **2GB RAM minimum**
- **Internet connection** (for package installation)
- **Git** (optional, for cloning repo)

---

## ⚙️ ONE-COMMAND SETUP

### **Linux / macOS** 
```bash
cd /path/to/photonic-radar-ai
bash setup.sh
python run_desktop.py
```

### **Windows**
```cmd
cd C:\path\to\photonic-radar-ai
setup.bat
python run_desktop.py
```

**That's it!** The setup script will:
✅ Create virtual environment  
✅ Install all 40+ dependencies  
✅ Verify installation  
✅ Show you what's next  

---

## 🎮 What to Do Next

### **Option 1: Desktop Application (Recommended)**
```bash
python run_desktop.py
```
✅ Professional dark-themed GUI  
✅ One-click system control  
✅ Real-time monitoring  
✅ Dashboard integration  
✅ Demo mode built-in  

### **Option 2: Demo (No Backend Needed)**
```bash
python demo.py
```
Perfect for testing when you don't have the full system running.

### **Option 3: Full Backend**
```bash
python main.py --ui
```
This includes:
- Event bus (core message routing)
- Radar simulation engine
- EW cognitive pipeline
- API server (localhost:5000)
- Dashboard (localhost:8501)

### **Option 4: Dashboard Only**
```bash
streamlit run photonic-radar-ai/ui/dashboard.py
```

---

## 🎯 Desktop Application Guide

### **Main Controls**

| Button | Function |
|--------|----------|
| **▶ Start System** | Launch backend with event bus, radar, EW, and API |
| **⏹ Stop System** | Graceful shutdown of all components |
| **🔄 Restart System** | Quick stop + start |
| **🎮 Run Demo** | Stream demo simulation output |
| **📊 Open Dashboard** | Browser → tactical command center |
| **🔌 API Docs** | Browser → FastAPI interactive docs |

### **Status Indicators**

```
🟢 Backend:   Ready     (main.py running)
🟢 API:       Ready     (port 5000 responding)
🟢 Dashboard: Ready     (Streamlit UI active)
```

If any show 🔴, click **Restart** to fix.

### **Console Panel**

Shows live logs from:
- Backend startup/shutdown
- Component initialization
- Radar frames processed
- EW assessments
- System health

### **Metrics Panel**

Real-time system resources:
- CPU usage %
- Memory usage (MB/%  )
- System uptime
- Process count

---

## 📊 Dashboard Guide

### **Access**

**Via Desktop App:** Click 📊 Open Dashboard  
**Direct:**  Browser → http://localhost:8501  

### **Modes**

**LIVE MODE** (🟢 API Connected)
- Real radar simulation data
- Live threat assessments
- Actual system metrics

**DEMO MODE** (🟡 No API)
- Synthetic but realistic data
- Perfect for UI/visualization testing
- No backend needed
- Automatically switches when API unavailable

### **Main Sections**

1. **ACTIVE RADAR TRACKS**
   - Track ID, Range, Azimuth, Velocity, Quality
   - Colored by track confidence

2. **SIGNAL STRENGTH HISTORY (SNR)**
   - Line chart of signal-to-noise ratio
   - Trends show detection reliability

3. **THREAT ASSESSMENTS**
   - Classification (FRIENDLY/UNKNOWN/HOSTILE)
   - Priority levels
   - Confidence scores
   - Color-coded: 🟢 green ~ 🔴 red

4. **EW STATUS**  
   - Electronic warfare pipeline state
   - Jammer detection status
   - Interference metrics

5. **SYSTEM HEALTH**
   - Event bus performance
   - Component uptime
   - Fault status

6. **LIVE EVENT TICKER**
   - Real-time system events
   - Timestamp-stamped log

---

## 🎯 Demo Mode

### **Standalone Demo**

Run WITHOUT backend infrastructure:
```bash
python demo.py
```

Features:
- Generates synthetic radar frames
- Simulates target tracks
- Produces EW assessments
- NO dependencies beyond core libraries
- Perfect for testing on fresh machines

### **Dashboard Demo**

If backend not running (🟡 DEMO):
- Dashboard automatically generates synthetic data
- Shows realistic UI/visualization
- Useful for design/layout testing
- No manual intervention needed

---

## 📦 Build Standalone Executable

Convert to .exe / standalone app (no Python needed to run):

### **Linux/macOS**
```bash
bash build_desktop.sh
# Output: dist/PhotonicRadarAI/PhotonicRadarAI
./dist/PhotonicRadarAI/PhotonicRadarAI
```

### **Windows**
```cmd
build_desktop.bat
# Output: dist\PhotonicRadarAI\PhotonicRadarAI.exe
dist\PhotonicRadarAI\PhotonicRadarAI.exe
```

---

## 🔧 Troubleshooting

### **"Python not found"**
- Install from [python.org](https://www.python.org/downloads/)
- Make sure to check ✅ "Add Python to PATH" during installation

### **"Module not found" error**
- Run setup again: `bash setup.sh` or `setup.bat`
- Or manually install: `pip install -r requirements.txt`

### **"Port 5000 already in use"**
- Another app is using the API port
- Change in code or kill the process: `lsof -i :5000` (Linux/Mac)

### **"API not responding"**
- Check console for error messages
- Try restart: 🔄 button in desktop app

### **Dashboard shows DEMO mode only**
- Backend might not be running
- Check API status: 🟢 vs 🔴 indicator
- Try clicking ▶ Start System

### **Performance issues**
- Check CPU/Memory in metrics panel
- Close other apps
- Reduce dashboard refresh rate if needed

---

## 📚 Full Documentation

- **Desktop App:** [DESKTOP_APP.md](DESKTOP_APP.md)
- **Architecture:** [README.md](README.md)
- **Development:** [DESKTOP_DELIVERY.md](DESKTOP_DELIVERY.md)
- **Production:** [README_PRODUCTION.md](README_PRODUCTION.md) (if available)

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] `bash setup.sh` completes without errors
- [ ] `python run_desktop.py` launches GUI
- [ ] Desktop window appears with buttons
- [ ] Click ▶ Start → see startup logs
- [ ] Indicators change to 🟢 green
- [ ] Click 📊 Open Dashboard → browser opens
- [ ] Dashboard shows "LIVE" or "DEMO" mode
- [ ] Metrics panel shows CPU/Memory

**All green?** ✅ Ready for production!

---

## 🚀 Next Steps

1. **Explore Dashboard**
   - View radar tracks
   - Check threat assessments
   - Monitor system health

2. **Review Components**
   - Event bus (core routing)
   - Radar engine (simulation)
   - EW pipeline (intelligence)
   - API (backend interface)

3. **Run Demo**
   - `python demo.py` for standalone testing
   - Useful for CI/CD pipelines

4. **Build for Distribution**
   - `bash build_desktop.sh` creates standalone exe
   - Send to others - no Python installation needed!

---

## 💡 Tips

- **Save logs:** Desktop app logs go to `photonic-radar-ai/runtime/logs/`
- **Docker:** Full containerized setup in `docker-compose.yml`
- **API docs:** Full endpoint list at http://localhost:5000/docs
- **Demo mode:** Always available via 🎮 button even when backend running

---

**Ready to launch? 🚀**

```bash
python run_desktop.py
```

Questions? Check [README.md](README.md) or [DESKTOP_APP.md](DESKTOP_APP.md)
