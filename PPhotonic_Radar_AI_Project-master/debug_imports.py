import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"User Site: {sys.prefix}")
print("Sys Path:")
for p in sys.path:
    print(f"  {p}")

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

print("\nImporting packages:")
for pkg, mod in packages.items():
    try:
        __import__(mod)
        print(f"✅ {pkg} imported successfully")
    except ImportError as e:
        print(f"❌ {pkg} failed to import: {e}")
    except Exception as e:
        print(f"❌ {pkg} failed with unrelated error: {e}")
