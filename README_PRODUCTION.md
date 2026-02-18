# 📡 PHOENIX-RADAR: Cognitive Photonic Radar with AI

![Status](https://img.shields.io/badge/Status-Production--Ready-00f2ff)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Framework](https://img.shields.io/badge/FastAPI-Streamlit-red)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)

**PHOENIX-RADAR** is a production-grade simulation and control platform for **Cognitive Photonic Radar** systems. It combines high-fidelity photonic signal modeling with advanced AI classification, closed-loop adaptation, and comprehensive evaluation framework.

---

## ⚡ Quick Start (Choose Your Mode)

### 1️⃣ **Demo Mode** - Full System Demonstration (2 minutes)
```bash
python demo.py
```
✅ **No setup required** - Shows complete system working: signal processing → detection → tracking → EW intelligence.

**Output:**
- Real-time console display of targets, detections, threats
- Performance statistics (frames/sec, accuracy%)
- No external services needed

---

### 2️⃣ **Main Mode** - Production Radar Engine
```bash
# Headless (API server only)
python main.py

# With dashboard
python main.py --ui

# Debug mode
python main.py --debug

# 30-second demo then exit
python main.py --headless
```

**Features:**
- FastAPI backend (http://localhost:5000)
- Streamlit dashboard (http://localhost:8501)
- Comprehensive logging
- Production error handling

---

### 3️⃣ **Dashboard Only** - Live Monitoring
```bash
streamlit run photonic-radar-ai/ui/dashboard.py
```

**Prerequisites:** API running at http://localhost:5000

---

### 4️⃣ **Docker Deployment** - Containerized (Production)
```bash
# Standard deployment
docker-compose up --build

# Production config
docker-compose -f docker-compose.prod.yml up

# Stop all containers
docker-compose down
```

**Services:**
- 📡 API Server: http://localhost:8000
- 🎛️ Dashboard: http://localhost:8501

---

## 📋 Entry Points Reference

| Mode | Command | Purpose | Output | Time |
|------|---------|---------|--------|------|
| **Demo** | `python demo.py` | Full system demo | Console | 10s |
| **Main** | `python main.py` | Production radar | Logs + API | 30s |
| **Dashboard** | `streamlit run ui/dashboard.py` | Live monitoring | Web UI | ∞ |
| **Research** | `python research/orchestrate.py --all` | Benchmarking | Reports | 5min |

---

## 🌟 System Capabilities

### Core Features
✅ **Physics-Based Photonic Simulation**
- Heterodyne mixing, laser noise modeling
- FMCW radar with tunable parameters
- Realistic target and clutter simulation

✅ **Adaptive Radar**
- Intelligent CFAR detection
- Dynamic threshold adjustment
- Multi-target tracking with Kalman filtering

✅ **Cognitive Intelligence**
- Real-time threat classification  
- Adaptive waveform optimization
- Decision logic with engagement recommendations

✅ **Electronic Warfare**
- Countermeasure planning
- Situation-dependent strategies
- Event-driven response

### Production-Grade
✅ Research-quality metrics logging  
✅ Performance benchmarking framework  
✅ SNR sensitivity analysis  
✅ Automated evaluation reports  
✅ Docker containerization  
✅ Cross-platform (Linux, macOS, Windows)  

---

## 🏗️ Directory Structure

```
photonic-radar-ai/                    # Project root
├── main.py                           # ← MAIN ENTRY POINT
├── demo.py                           # ← DEMO ENTRY POINT  
├── README.md                         # This file
│
├── photonic-radar-ai/                # Core system
│   ├── ui/
│   │   └── dashboard.py             # ← DASHBOARD ENTRY POINT
│   ├── api/                         # FastAPI implementation
│   ├── core/                        # Event orchestration
│   ├── defense_core/                # Event bus & schemas
│   ├── subsystems/                  # Radar, EW, integration
│   ├── simulation_engine/           # Physics & simulation
│   ├── signal_processing/           # DSP pipeline
│   ├── tracking/                    # Tracking filters
│   ├── cognitive/                   # Decision engine
│   ├── ai_models/                   # Neural network inference
│   └── runtime/                     # Logs
│
├── research/                        # Research framework
│   ├── metrics_logger.py            # Metrics Collection
│   ├── latency_profiler.py          # Performance timing
│   ├── benchmark.py                 # Benchmarking
│   ├── noise_experiment.py          # SNR analysis
│   ├── report_generator.py          # Report generation
│   └── orchestrate.py               # Run all tests
│
├── configs/                         # Configuration
│   ├── benchmark_config.yaml
│   ├── noise_experiment_config.yaml
│   └── master_experiment_config.yaml
│
├── Docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.prod.yml
│
└── docs/
    ├── QUICKSTART.md
    ├── INTEGRATION_GUIDE.md
    └── ARCHITECTURE.md
```

---

## 🚀 Installation

### Requirements
- Python 3.11+
- Linux/macOS/Windows
- 2GB+ disk space, 4GB+ RAM
- Optional: Docker

### Setup Steps

```bash
# 1. Clone repository
git clone <repository-url>
cd photonic-radar-ai

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# or
.venv\Scripts\activate             # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
# Test: Does demo run?
python demo.py --duration 5
# Should show detections and threats without errors

# Test: Does main start?
timeout 10 python main.py --headless || true
# Should initialize subsystems

# Test: Can dashboard import?
python -c "import streamlit; print('✓ Streamlit OK')"
```

---

## 📖 Usage Examples

### Example 1: Quick 10-Second Demo
```bash
python demo.py --duration 10 --verbose
```
Shows full pipeline: targets → processing → detections → threats

### Example 2: Start Full System
```bash
# Terminal 1: Backend
python main.py --ui

# Terminal 2: Watch logs  
tail -f photonic-radar-ai/runtime/logs/phoenix_radar.log

# Terminal 3: Open browser
# Dashboard auto-opens at http://localhost:8501
```

### Example 3: Performance Benchmarking
```bash
cd research
python benchmark.py --experiment-name production_baseline
# Output: results/benchmark_summary_*.json
```

### Example 4: SNR Sensitivity Analysis
```bash
cd research
python noise_experiment.py
# Output: SNR thresholds and optimal operating points
```

### Example 5: Docker Production Deployment
```bash
docker-compose up --build

# Access:
# - API: http://localhost:8000  
# - Dashboard: http://localhost:8501

# Logs:
docker logs -f <container-id>
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│          PHOENIX RADAR SYSTEM ARCHITECTURE          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐      ┌──────────────────┐   │
│  │ Radar Subsystem  │      │  EW Subsystem    │   │
│  ├──────────────────┤      ├──────────────────┤   │
│  │ • Signal Acq     │      │ • Assessment     │   │
│  │ • Processing     │◄─────┤ • Decision       │   │
│  │ • Detection      │      │ • Countermeas.   │   │
│  │ • Tracking       │      └──────────────────┘   │
│  └────────┬─────────┘                              │
│           │                                        │
│           ▼                                        │
│  ┌──────────────────────────────────────────┐     │
│  │   Defense Core Event Bus                 │     │
│  │   (Radar ↔ EW Communication)            │     │
│  └──────────────────────────────────────────┘     │
│           ▲             ▲                         │
│           │             │                         │
│  ┌────────┴────┐  ┌─────┴────────┐               │
│  │ API Server  │  │ UI Dashboard │               │
│  │ (FastAPI)   │  │ (Streamlit)  │               │
│  └─────────────┘  └──────────────┘               │
│                                                    │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Verification & Testing

### Quick Verification
```bash
# 1. Demo works
python demo.py --duration 5

# 2. Main initializes
timeout 10 python main.py --headless || echo "Completed"

# 3. Dashboard imports
python -c "import sys; sys.path.insert(0, 'photonic-radar-ai'); from ui import dashboard; print('✓')"
```

### Full Test Suite  
```bash
pytest photonic-radar-ai/tests/ -v
```

### Benchmark Test
```bash
cd research
python benchmark.py --num-trials 3
```

---

## 📈 Performance Targets

| Metric | Minimum | Target | Excellent |
|--------|---------|--------|-----------|
| **Throughput** | 8 fps | 10 fps | 15+ fps |
| **Latency** | 20ms | 10ms | 5ms |
| **Accuracy** | 75% | 85% | 92%+ |
| **CPU Usage** | - | <75% | <50% |
| **Memory** | - | <512 MB | <300 MB |

---

## 🔍 Research & Evaluation Tools

PHOENIX-RADAR includes comprehensive benchmarking:

```bash
# Performance benchmarking
python research/benchmark.py

# SNR sensitivity sweep  
python research/noise_experiment.py

# Automated report generation
python research/report_generator.py

# Complete workflow
python research/orchestrate.py --all
```

**Outputs:** CSV metrics, JSON summaries, Markdown reports

See [research/README.md](research/README.md) for details.

---

## 🐳 Docker Guide

### Quick Docker Run
```bash
docker-compose up --build
```

### Production Deployment  
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Container Management
```bash
docker-compose logs -f                    # View logs
docker-compose restart                    # Restart services
docker-compose down                       # Stop & remove
docker-compose ps                         # Status check
```

### Ports
- **8000** - FastAPI backend
- **8501** - Streamlit dashboard  
- **5000** - Internal API (container-only)

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'photonic_core'"
```bash
# Solution: Activate virtual environment
source .venv/bin/activate      # Linux/macOS
# or
.venv\Scripts\activate         # Windows
```

### "API connection refused" when running dashboard
```bash
# Solution: Start main.py first
python main.py --ui
# Dashboard will auto-connect on http://localhost:5000
```

### "Port 8501 already in use"
```bash
# Solution: Streamlit auto-selects new port
streamlit run photonic-radar-ai/ui/dashboard.py --logger.level=debug
# Check console output for port number
```

### "Import errors when running demo"
```bash
# Solution: Verify path setup
python -c "import sys; sys.path.insert(0, 'photonic-radar-ai'); import defense_core; print('✓')"
```

---

## 📚 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute getting started *(coming)*
- **[INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)** - Production integration *(coming)*
- **[research/README.md](research/README.md)** - Evaluation framework
- **[Dockerfile](Dockerfile)** - Container configuration
- **[docker-compose.yml](docker-compose.yml)** - Multi-service orchestration

---

## 🎯 Common Workflows

### Workflow 1: Demonstrate System to Stakeholders
```bash
python demo.py --duration 30
# Live console demo, no setup needed
```

### Workflow 2: Start Production System
```bash
python main.py --ui
# API + Dashboard ready in 30 seconds
```

### Workflow 3: Benchmark Your Setup
```bash
cd research && python orchestrate.py --all
# Performance report in results/evaluation_report_*.md
```

### Workflow 4: Deploy to Production (Docker)
```bash
docker-compose -f docker-compose.prod.yml up -d
# Scalable, containerized deployment
```

---

## 🔐 Security & Production Notes

✅ **Production Ready for:**
- Research environments
- Simulation and prototyping
- Academic demonstrations
- Performance evaluation

⚠️ **Security Considerations:**
- Deploy behind authentication layer for web access
- Use environment variables for sensitive config
- Implement rate limiting for API
- Monitor resource usage in production

---

## 📄 License & Citation

**License:** MIT  
**Status:** Production-Ready  
**Version:** 2.0.0 (February 2026)  
**Platform:** Linux, macOS, Windows  

---

## 📞 Support

**Getting Help:**
1. Read [QUICKSTART.md](docs/QUICKSTART.md)
2. Check [INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)
3. Review logs in `photonic-radar-ai/runtime/logs/`
4. Examine [example code](demo.py) in demo.py

**For Issues:**
- Check console output for error messages
- Enable debug mode: `python main.py --debug`
- Review detailed logs: `tail -f photonic-radar-ai/runtime/logs/phoenix_radar.log`

---

*Cognitive Photonic Radar AI - Advanced sensing for next-generation defense systems.*  
*Built for research, production-ready architecture.*
