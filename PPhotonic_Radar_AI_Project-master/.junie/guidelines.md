# Development Guidelines - Multi-Input Cognitive Photonic Radar AI System

This document provides essential information for advanced developers working on the Photonic Radar AI Project.

## 1. Build/Configuration Instructions

### Prerequisites
- Python 3.10 (Recommended and tested).
- Recommended: NVIDIA GPU with CUDA for faster AI inference (optional, system falls back to CPU).

### Environment Setup
1. **Install Python 3.10**: Ensure Python 3.10 is installed on your system.
2. **Create Virtual Environment**:
   ```powershell
   python -m venv venv_310
   ```
3. **Install Dependencies**:
   ```powershell
   .\venv_310\Scripts\pip install -r requirements.txt
   ```
2. **Hardware Integration (Optional)**:
   - If using a physical RTL-SDR, ensure `librtlsdr` is installed on the system.
   - Toggle hardware mode in `src/signal_generator.py` by setting `USE_RTL_SDR = True`.

### Running the Application
- **Standard**: `.\venv_310\Scripts\python launcher.py`
- **Manual Streamlit**: `streamlit run app.py`
- **Windows Shortcut**: Use `run_radar.bat`.

## 2. Testing Information

### Core Logic Verification
A core workflow test should verify signal generation, feature extraction, and model inference.

#### Running Tests
To run the core workflow verification:
```powershell
.\venv_310\Scripts\python test_signal_and_model.py
```

#### Adding New Tests
When adding new features (e.g., a new radar feature or model layer):
1. Create a standalone script or add to `test_signal_and_model.py`.
2. Ensure you import from the `src` directory correctly by adding it to `sys.path` if running from the root.
3. Verify that new components handle complex I/Q data (common in this project).

#### Sample Test Script
```python
import torch
import numpy as np
from src.signal_generator import generate_radar_signal
from src.feature_extractor import get_all_features
from src.model_pytorch import build_pytorch_model

def quick_test():
    # 1. Signal Gen
    sig = generate_radar_signal("drone")
    # 2. Feature Extraction
    rd, spec, meta, _ = get_all_features(sig)
    # 3. Model Inference
    model = build_pytorch_model()
    # ... tensors conversion and model(rd, spec, meta)
    print("Test Passed")
```

## 3. Additional Development Information

### Architecture Overview
- **Multi-Input Fusion**: The AI model (`src/model_pytorch.py`) uses a dual-CNN branch for Range-Doppler maps and Spectrograms, fused with a Dense branch for photonic metadata.
- **Cognitive Logic**: Adaptive thresholds and Kalman tracking are integrated into the real-time processing loop in `app.py` and `src/tracking.py`.
- **Data Handling**:
  - `results/`: Directory for logs (`system.log`), database (`users.db`), and saved models (`radar_model_pytorch.pt`).
  - `src/db.py`: Handles SQLite user management.

### Code Style & Best Practices
- **I/Q Consistency**: Radar signals are represented as `np.complex64`. Ensure any new signal processing steps maintain or correctly handle complex data.
- **Pathing**: Always use `os.path.join` for cross-platform compatibility (Windows/Linux).
- **Logging**: Use `src.logger.log_event(message)` for consistent system logging to `results/system.log`.
- **Security**: Admin password hashing uses SHA-256 (`src/security.py`). Default admin is `nikhil` with password `123` (initialized in `src/db.py`).

### Debugging
- Check `results/system.log` for runtime events and errors.
- The `launcher.py` silences TensorFlow warnings; if debugging TF-related issues (if enabled), check the environment variables there.
