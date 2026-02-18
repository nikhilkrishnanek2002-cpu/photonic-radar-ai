# 📡 PHOENIX-RADAR: Cognitive Photonic Radar with AI

![Status](https://img.shields.io/badge/Status-Production--Ready-00f2ff)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)
![Framework](https://img.shields.io/badge/FastAPI-Streamlit-red)

Production-grade cognitive photonic radar simulation platform with AI classification, adaptive waveform control, and comprehensive evaluation framework.

---

## ⚡ Quick Start

### **Desktop GUI** (Recommended - Single Click)
```bash
python run_desktop.py
```
Launches full desktop application with system controls, monitoring, and dashboard access.

**→ [Desktop App Documentation](DESKTOP_APP.md)**

### **Demo Mode** (No Setup)
```bash
python demo.py
```

### **Main System**
```bash
python main.py --ui
```

### **Dashboard Only**  
```bash
streamlit run photonic-radar-ai/ui/dashboard.py
```

### **Docker**
```bash
docker-compose up --build
```

**→ [See Full Documentation](README_PRODUCTION.md)**

---

### 1. Physics-Based Photonic Simulation
- **Heterodyne Mixing**: High-frequency RF signal generation using photonic heterodyning.
- **Noise Modeling**: Realistic laser phase noise and environmental thermal noise.
- **FMCW Radar**: Fully tunable chirp profiles, bandwidth, and pulse repetition frequencies.

### 2. Cognitive Closed-Loop Adaptation
- **Real-time Feedback**: Frame-to-frame adaptation of waveform parameters based on AI scene assessment.
- **Adaptive Waveform**: Dynamic scaling of Transmit Power, Bandwidth, and PRF.
- **Intelligent CFAR**: Adaptive detection thresholds to maintain constant false alarm rates in variable clutter.

### 3. AI-Driven Intelligence
- **Micro-Doppler Analysis**: Feature extraction for classification of Drones, Birds, Aircraft, and Missiles.
- **Explainable AI (XAI)**: Automated narrative generation justifying every cognitive decision with physics-based reasoning.
- **Tactical Dashboards**: Streamlit-based "Command Center" for real-time situational awareness.

---

## 🏗️ Architecture

The system follows a modular architecture designed for research scalability and defense readiness:

| Layer | Directory | Description |
|-------|-----------|-------------|
| **Core** | `photonic-radar-ai/core/` | System engine, telemetry, and central orchestration. |
| **Cognitive** | `photonic-radar-ai/cognitive/` | Intelligent decision engine and parameter management. |
| **Photonic** | `photonic-radar-ai/photonic/` | Physics-based modeling of optics, signals, and noise. |
| **Signal** | `photonic-radar-ai/signal_processing/` | Radar DSP (FFT, CFAR), detection, and feature extraction. |
| **AI** | `photonic-radar-ai/ai_models/` | Neural networks, inference engine, and XAI logic. |
| **Subsystems** | `photonic-radar-ai/subsystems/` | Fault-isolated components (Radar, EW, Event Bus). |
| **UI** | `photonic-radar-ai/ui/` | API server and Streamlit tactical dashboard. |

---

## 📖 Detailed Guides

- **Production Setup:** [README_PRODUCTION.md](README_PRODUCTION.md)
- **Research Framework:** [research/README.md](research/README.md)  
- **Docker Deployment:** [docker-compose.yml](docker-compose.yml)

---

## 🧠 Cognitive Adaptation Engine

PHOENIX-RADAR implements adaptive closed-loop control:

- **Search Mode**: Widearea scanning with standard parameters
- **Track Mode**: Focused tracking with optimized parameters
- **Clutter Mode**: High-resolution processing to suppress false alarms
- **Swarm Mode**: Multi-target handling with dynamic PRF

---

## 🛠️ Testing & Verification

```bash
# Quick demo
python demo.py --duration 5

# Full test suite
pytest photonic-radar-ai/tests/ -v

# Performance benchmarking
python research/benchmark.py

# SNR sensitivity analysis
python research/noise_experiment.py
```

---

## 📚 Also Available

- **Metrics Framework:** CSV logging with real-time statistics
- **Latency Profiler:** Per-stage timing analysis  
- **Benchmarking Suite:** Throughput, latency, accuracy measurement
- **Research Tools:** SNR sweeps, noise experiments, reports

---

## 📄 License & Properties
- **Status:** Production-Ready
- **License:** MIT
- **Python:** 3.11+
- **Platforms:** Linux, macOS, Windows
- **Classification:** Academic / Research

---
*Cognitive Photonic Radar AI - Next-generation sensing platform.*
