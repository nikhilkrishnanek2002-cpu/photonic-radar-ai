# Building PHOENIX-RADAR on Windows

This guide explains how to package the Phoenix Radar desktop application as a standalone `.exe` on Windows.

## Prerequisites
1.  **Python 3.9+** installed (Add to PATH during installation).
2.  **Git Bash** or **PowerShell**.

## Steps

### 1. Install Dependencies
Open standard Command Prompt or PowerShell and run:
```powershell
pip install PySide6 pyqtgraph numpy scipy scikit-learn torch pyyaml pyinstaller
```

### 2. Navigate to Project
```powershell
cd path\to\PPhotonic_Radar_AI_Project-master
```

### 3. Run PyInstaller
Use the provided spec file to build the application:
```powershell
pyinstaller packaging/phoenix_radar.spec
```

### 4. Locate Executable
After the build completes successfully:
- Go to the `dist/PhoenixRadar` directory.
- Run `PhoenixRadar.exe`.

## Troubleshooting
- **Missing DLLs:** If generic errors occur, ensure you don't have conflicting python installations.
- **Console Window:** The current build enables the console for debugging. To hide it, edit `packaging/phoenix_radar.spec` and set `console=False` in the `EXE()` block.
