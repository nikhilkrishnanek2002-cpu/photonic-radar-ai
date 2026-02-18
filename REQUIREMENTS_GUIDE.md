# PHOENIX Radar AI - Requirements Guide

## Overview

This project has three requirements files for different use cases:

### 📦 Production Requirements
- **File:** `requirements.txt`
- **Purpose:** Full production deployment with all features
- **Includes:** NumPy, SciPy, PyTorch, Streamlit, Flask, Plotly, Seaborn
- **Size:** ~3.5 GB (with PyTorch)
- **Use When:** Running full system with ML inference and visualization

### 🚀 Minimal Requirements
- **File:** `requirements-minimal.txt`
- **Purpose:** Lightweight Docker deployments
- **Excludes:** PyTorch, torchvision, advanced visualization
- **Size:** ~600 MB
- **Use When:** Building Docker images, edge devices, or core radar only

### 🧪 Development Requirements
- **File:** `requirements-dev.txt`
- **Purpose:** Development, testing, and code quality
- **Includes:** Pytest, Black, Flake8, Sphinx, Jupyter, profiling tools
- **Use When:** Contributing to the project, running tests locally

---

## Installation

### Method 1: Full Production Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import numpy, scipy, sklearn, torch, streamlit, flask; print('✓ All imports successful')"
```

### Method 2: Lightweight Docker Setup

```bash
# Inside Docker container (python:3.11-slim base image)
pip install --no-cache-dir -r requirements-minimal.txt
```

### Method 3: Development Setup

```bash
# Install production + development dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install git hooks for code quality
pre-commit install
```

---

## Version Compatibility

### Python Versions

| Version | Status | Notes |
|---------|--------|-------|
| 3.11+ | ✅ **Recommended** | Best compatibility, all packages stable |
| 3.10 | ✅ Supported | Good compatibility, minor issues possible |
| 3.9 | ⚠️ Legacy | Some packages may have issues |
| 3.8 | ❌ Not tested | Not recommended |

### Key Package Versions

| Package | Version | Reason |
|---------|---------|--------|
| torch | 2.0.1  | Latest stable (released 2023-07) |
| numpy | 1.24.3 | Compatible with scipy, sklearn |
| scipy | 1.11.2 | Latest stable with numpy 1.24 |
| streamlit | 1.26.0 | Latest with Python 3.11 support |
| Flask | 2.3.2  | Latest with Werkzeug 2.3 |

---

## Package Descriptions

### Scientific Computing

**numpy (1.24.3)**
- Numerical computing foundation
- Used for array operations, signal processing
- Required: YES

**scipy (1.11.2)**
- Scientific computing library
- `scipy.signal` for signal processing (beamforming, filtering)
- `scipy.special` for mathematical functions
- Required: YES

**pandas (2.0.3)**
- Data manipulation and analysis
- Used for tabular data handling
- Required: YES

### Machine Learning

**scikit-learn (1.3.0)**
- Machine learning utilities
- Used for: `confusion_matrix`, `classification_report`, metrics
- Well-integrated with numpy/scipy
- Required: YES

**torch (2.0.1)**
- Deep learning framework
- Neural network inference and training
- Large package (~2 GB)
- Required: For ML inference, Optional for core radar
- Alternative: Can skip if not using neural networks

### Visualization

**matplotlib (3.7.2)**
- Static 2D plotting
- Used for: signal plots, spectrogram visualization
- Lightweight, no web dependencies
- Required: For signal analysis

**seaborn (0.12.2)**
- Statistical visualization
- Built on matplotlib
- Used for: heatmaps, correlation plots
- Optional but recommended

**plotly (5.15.0)**
- Interactive visualization
- Used for: interactive dashboard plots
- Required: For Streamlit dashboard

### Web Frameworks

**Flask (2.3.2)**
- Web framework for API
- Used for: REST API endpoints
- Lightweight, good for small-to-medium services
- Required: For API server

**Werkzeug (2.3.6)**
- WSGI utilities library
- Dependency of Flask
- Required: YES (auto-installed with Flask)

**uvicorn (0.23.1)**
- ASGI server
- Used for: async HTTP server
- Optional but recommended for production

**requests (2.31.0)**
- HTTP client library
- Used for: API calls, web requests
- Required: YES

### Data Validation & Configuration

**Pydantic (2.1.1)**
- Data validation using Python type hints
- Used by: Streamlit, FastAPI
- Required: YES (for data validation)

**python-dotenv (1.0.0)**
- Environment variable management
- Used for: `.env` file support
- Required: For configuration

### Dashboard

**streamlit (1.26.0)**
- Web dashboard framework
- Used for: Real-time UI, data visualization
- Includes: Auto-reload, caching, widgets
- Required: For dashboard feature

---

## Special Cases

### GPU Support (CUDA)

If you have an NVIDIA GPU and want to use it with PyTorch:

```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU is available
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Minimal Docker Build

For production Docker images with smaller footprint:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt
# ... rest of Dockerfile
```

Expected image size: ~400 MB (vs 1.5 GB with full requirements)

### Development with Specific Tools

For specific development workflows, install subsets:

```bash
# Testing only
pip install pytest pytest-cov

# Code quality only
pip install black flake8 isort mypy

# Jupyter notebooks
pip install jupyter jupyterlab

# Database development
pip install sqlalchemy alembic
```

---

## Verification

### Test Imports

```bash
# Quick import test
python3 -c "
import numpy as np
import scipy
import pandas as pd
import sklearn
import matplotlib
import streamlit as st
import flask
print('✓ All imports successful!')
"
```

### Version Information

```bash
# Show all installed packages with versions
pip list

# Show specific package version
pip show numpy
pip show torch
```

### Dependency Tree

```bash
# Show dependency relationships
pip install pipdeptree
pipdeptree
```

---

## Troubleshooting

### Problem: Import errors for torch

**Solution:** PyTorch doesn't need to be installed if not using neural networks.

```bash
# Option 1: Install PyTorch
pip install torch

# Option 2: Skip and use minimal requirements
pip install -r requirements-minimal.txt
```

### Problem: "scipy installation failed"

**Solution:** Need build tools to compile C extensions

```bash
# Linux (Debian/Ubuntu)
sudo apt-get install build-essential python3-dev

# macOS
brew install python-dev@3.11

# Windows
# Use conda instead: conda install scipy
```

### Problem: Streamlit fails with "module not found"

**Solution:** Ensure Streamlit is installed and Python version is compatible

```bash
# Upgrade Streamlit
pip install --upgrade streamlit

# Check Python version
python --version  # Should be 3.8+
```

### Problem: "ModuleNotFoundError: No module named 'cuda'"

**Solution:** This is normal. CUDA is optional. Use CPU-only PyTorch if you don't have a GPU.

```bash
# This is expected behavior - CUDA is for GPU acceleration only
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
# Output: CUDA available: False (OK on non-GPU systems)
```

### Problem: Out of disk space during installation

**Solution:** PyTorch is large (~2GB). Use minimal requirements instead.

```bash
# Use lightweight version
pip install -r requirements-minimal.txt
```

---

## Performance Optimization

### Reduce Installation Size

```bash
# Use --no-cache-dir to skip cache (saves ~500MB)
pip install --no-cache-dir -r requirements.txt

# Use --no-deps with pre-built wheels
pip install --only-binary=:all: -r requirements.txt
```

### Faster Installation

```bash
# Parallel installation (faster on multi-core systems)
pip install -r requirements.txt --use-deprecated=legacy-resolver
```

### Generate Lock File

For reproducible installations, generate a lock file:

```bash
# Generate lock file (exact versions of all dependencies)
pip freeze > requirements.lock

# Later, install exact versions
pip install -r requirements.lock
```

---

## Updating Packages

### Update Specific Package

```bash
pip install --upgrade numpy
```

### Update All Packages

```bash
# Carefully - may break compatibility
pip install --upgrade -r requirements.txt
```

### Check for Updates

```bash
# Show packages with available updates
pip list --outdated
```

---

## Docker Integration

### Building Docker Image

The Dockerfile automatically uses `pip install -r requirements.txt`:

```dockerfile
# From docker-compose.yml
COPY requirements.txt .
RUN pip install -r requirements.txt
```

### Using Minimal Requirements in Docker

Modify Dockerfile or docker-compose.yml:

```dockerfile
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt

- name: Run tests
  run: pytest --cov=photonic-radar-ai tests/
```

---

## Support & Issues

### Common Questions

**Q: Why is PyTorch so large?**  
A: PyTorch includes pre-compiled binary libraries for CPU and CUDA. Use CPU-only or skip if not needed.

**Q: Should I use pip or conda?**  
A: Pip works well. Conda is optional, helps with C extensions like scipy/numpy.

**Q: Can I use Python 3.12?**  
A: Not tested. Some packages may not have wheels for 3.12 yet.

**Q: Can I remove streamlit to reduce size?**  
A: Yes, if only using API. Remove `streamlit==1.26.0` from requirements.txt.

---

## File Descriptions

### requirements.txt (Full)
- **Size:** ~3.5 GB installed
- **Python:** 3.10+
- **Use:** Production with all features
- **Installs:** All scientific, ML, visualization, and web packages

### requirements-minimal.txt (Lite)
- **Size:** ~600 MB installed
- **Python:** 3.10+
- **Use:** Docker, production minimal
- **Installs:** Core packages only, no PyTorch

### requirements-dev.txt (Dev)
- **Size:** ~2 GB additional
- **Python:** 3.10+
- **Use:** Development, testing, code quality
- **Installs:** Pytest, Black, Sphinx, Jupyter, profilers

---

**Last Updated:** February 2026  
**Status:** Production-Ready ✅  
**Python Support:** 3.10+ (3.11 recommended)
