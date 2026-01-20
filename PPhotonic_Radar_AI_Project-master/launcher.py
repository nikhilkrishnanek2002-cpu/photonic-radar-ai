import subprocess
import sys
import os

# --- SILENCE TENSORFLOW WARNINGS ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Hide all TF info/warning/error logs

# Removed CUDA_VISIBLE_DEVICES = -1 to allow GPU usage

def launch():
    print("🚀 Starting AI Radar Web Interface...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ GPU Acceleration Detected: {torch.cuda.get_device_name(0)}")
        else:
            print("ℹ Running in CPU mode (No CUDA device found).")
    except ImportError:
        print("ℹ Running in CPU optimized mode.")
    try:
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\nStopping server...")

if __name__ == "__main__":
    launch()