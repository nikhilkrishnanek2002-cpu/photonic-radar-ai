#!/usr/bin/env python3
"""
AI Cognitive Photonic Radar - PHOENIX-RADAR Project Launcher
Main entry point for the radar application.
"""

import subprocess
import sys
import os

# --- SILENCE TENSORFLOW WARNINGS ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Hide all TF info/warning/error logs


def check_dependencies():
    """Verify required packages are installed."""
    # Map package names to module names where they differ
    packages = {
        'streamlit': 'streamlit',
        'torch': 'torch',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'scipy': 'scipy',
        'matplotlib': 'matplotlib',
        'pyyaml': 'yaml',
        'python-json-logger': 'pythonjsonlogger',
        'opencv-python': 'cv2',
        'psutil': 'psutil',
        'seaborn': 'seaborn',
        'scikit-learn': 'sklearn',
        'plotly': 'plotly'
    }
    missing = []
    
    for package, module in packages.items():
        try:
            __import__(module)
            # print(f"✅ {package} ok") # Debug
        except ImportError as e:
            print(f"❌ Failed to import {package} ({module}): {e}")
            missing.append(package)
        except Exception as e:
             print(f"❌ Error importing {package}: {e}")
             missing.append(package)
    
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        print("Attempting automatic installation...")
        
        try:
            import subprocess
            # Install missing packages
            # Note: We need to map module names back to package names for pip if they differ
            reverse_map = {v: k for k, v in packages.items()}
            # Some manual corrections for packages where import name != package name
            # already handled by the 'packages' dict keys, mostly.
            
            packages_to_install = [p for p in missing if p != 'torch']
            
            # 1. Install general packages (lightweight)
            if packages_to_install:
                print(f"Installing: {', '.join(packages_to_install)}")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir"] + packages_to_install)
            
            # 2. Install PyTorch (CPU Version) to save disk space (avoiding 2GB+ CUDA libs)
            if 'torch' in missing:
                print("Installing Lightweight PyTorch (CPU) to save disk space...")
                # We use the official PyTorch CPU wheel index
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "--no-cache-dir", 
                    "torch", "--index-url", "https://download.pytorch.org/whl/cpu"
                ])
                
            print("✅ Dependencies installed successfully! Restarting...")
            return True
        except Exception as e:
            print(f"❌ Auto-install failed: {e}")
            print("Try running: pip install --no-cache-dir -r requirements.txt")
            return False
            
    return True


def launch():
    """Launch the Streamlit application."""
    print("🚀 Starting PHOENIX-RADAR: Cognitive Photonic Radar with AI...")
    print("-" * 60)
    
    try:
        import torch  # type: ignore
        if torch.cuda.is_available():
            print(f"✅ GPU Acceleration Detected: {torch.cuda.get_device_name(0)}")
        else:
            print("ℹ️  Running in CPU mode (No CUDA device found).")
    except ImportError:
        print("ℹ️  Running in CPU optimized mode.")
    
    print("-" * 60)
    print("Opening application at: http://localhost:8501")
    print("Press Ctrl+C to stop the server.\n")
    
    try:
        # Run streamlit app
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app.py"],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping server...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if check_dependencies():
        launch()
    else:
        sys.exit(1)