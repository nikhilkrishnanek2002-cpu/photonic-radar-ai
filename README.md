# 📡 PHOENIX-RADAR: Cognitive Photonic Radar with AI

![Status](https://img.shields.io/badge/Status-Operational-00f2ff)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Framework](https://img.shields.io/badge/Streamlit-App-red)
![Mode](https://img.shields.io/badge/Adaptive-Cognitive-green)

**PHOENIX-RADAR** is a next-generation simulation and control platform for **Cognitive Photonic Radar** systems. It combines high-fidelity photonic signal modeling with advanced AI classification and a closed-loop "cognitive" feedback engine to adapt to dynamic environments in real-time.

---

## 🌟 Key Features

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

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/nikhilkrishnanek2002-cpu/photonic-radar-ai.git
cd photonic-radar-ai

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r photonic-radar-ai/requirements.txt
```

### 2. Launch the System

```bash
# Start the unified platform launcher
python photonic-radar-ai/run_platform.py
```

This will:
1. Initialize the **Radar & EW Subsystems**.
2. Start the **API Server** (Port 5000).
3. Launch the **Tactical Dashboard** (Streamlit).

---

## 🧠 Cognitive Mode Overview

PHOENIX-RADAR implements a closed-loop cognitive engine that classifies the electromagnetic environment and adapts sensing parameters:

- **Search**: Wide-area scanning with standard parameters.
- **Tracking**: Resource-efficient focus on stable tracks.
- **Cluttered**: High-resolution bandwidth expansion to suppress false alarms.
- **Dense Swarm**: High PRF and separation logic for multiple targets.

---

## 🛠️ Verification

To run the automated test suite:

```bash
pytest photonic-radar-ai/tests/
```

---

## 📄 License & Attribution
- **Classification**: Academic / Research
- **Applications**: DRDO, Electronic Warfare (EW), Next-Gen Sensing.
- **License**: MIT

---
*Developed for advanced research in Cognitive Photonic Radar systems.*
