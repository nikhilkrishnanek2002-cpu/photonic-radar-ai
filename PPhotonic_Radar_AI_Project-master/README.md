# Multi-Input Cognitive Photonic Radar AI System

Professional defence-research-grade AI-enabled cognitive photonic radar simulation.

## Features
- **Photonic Radar Signal Simulation**: High-bandwidth I/Q signal generation with micro-Doppler components.
- **Advanced Feature Extraction**: 
  - 2D Range-Doppler maps (2D FFT).
  - Micro-Doppler spectrograms (STFT).
  - Phase statistics (Coherence, Variance).
  - Photonic metadata (Instantaneous bandwidth, Chirp slope, TTD beamforming).
- **PyTorch AI Architecture**:
  - Multi-input fusion model.
  - Dual CNN branches for spatial feature extraction.
  - Dense branch for metadata integration.
- **Professional Dashboard**:
  - Tab-based Streamlit UI with multi-tab interface.
  - **Real-time Target Tracking**: Kalman filter integration with trajectory visualization.
  - **Explainable AI (XAI)**: Grad-CAM heatmaps for decision transparency.
  - **Cognitive Logic**: Adaptive detection thresholds based on environmental noise and **Admin-adjustable sensitivity**.
  - **Hardware & Streaming**: 
    - Optional RTL-SDR integration with automatic fallback to simulation if `librtlsdr` is missing.
    - Optional Kafka-based data bus for real-time result streaming.
    - Robust error handling for all external dependencies.
  - **Admin Control Center**:
    - Multi-user authentication (RBAC) with dedicated Admin Panel.
    - System health monitoring (CPU, RAM, Hardware, DB).
    - User management (CRUD operations for operators and viewers).
    - Advanced system tuning and log management.
  - Real-time analytics and photonic parameter monitoring.

## How to use on Desktop

### 🐧 Linux (Desktop Shortcut)
1. Ensure you have the project installed and dependencies met.
2. Locate the `AI_Radar.desktop` file in the project root.
3. Copy it to your desktop or applications folder:
   ```bash
   cp AI_Radar.desktop ~/Desktop/
   ```
4. Right-click the file on your desktop and select **"Allow Launching"** (on GNOME/KDE).
5. Double-click the icon to start the application.

### 🪟 Windows (Batch Launcher)
1. Locate the `run_radar.bat` file in the project root.
2. Right-click it and select **"Send to" -> "Desktop (create shortcut)"**.
3. Double-click the shortcut to start the application.

### 🐍 Manual Command
You can always run the application from the terminal:
```bash
python launcher.py
```
