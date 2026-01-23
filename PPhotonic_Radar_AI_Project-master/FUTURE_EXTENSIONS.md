# Future Extension Roadmap & Hooks

PHOENIX-RADAR is designed for modular growth. The following hooks have been integrated to facilitate future research and industrialization.

## 1. Hardware Integration (`src/interfaces/hardware.py`)
Provides abstract base classes for physical hardware interfacing:
- **SDRInterface**: Hook for streaming real I/Q data from digitizers (e.g., USRP, LabView-FPGA).
- **OpticalController**: Remote control interfaces for tunable lasers, MZM bias controllers, and optical attenuators.
- **FPGAAcceleration**: Offloading heavy FFT/DSP tasks to hardware description language (HDL) cores for real-time performance.

## 2. Real-World Data Ingest (`src/interfaces/data.py`)
- **BaseDataLoader**: Interface for loading field trial recordings (HDF5, .mat, .bin).
- **Cross-Validation**: Pre-designed hooks to compare simulated waveforms against experimental ground truth.

## 3. AI & Cognitive Evolution (`src/ai/model.py`)
- **Vision Transformers (ViT)**: Placeholder `upgrade_to_transformer` to replace CNN branches with attention mechanisms for better feature global context.
- **Reinforcement Learning (RL)**: Placeholder `enable_reinforcement_learning` for cognitive feedback loops where the AI adapts radar parameters (PRR, BW) in real-time based on environmental uncertainty.

## 4. Pipeline Integration Points (`src/pipeline.py`)
A hardware bypass hook is available in the main pipeline. When enabled, it replaces the `simulation_layer` with live `SDR_streaming`.

---
**Developer Note**: To implement any of these, create a concrete class inheriting from the abstract interfaces and inject it into the `RadarPipeline` in `app.py`.
