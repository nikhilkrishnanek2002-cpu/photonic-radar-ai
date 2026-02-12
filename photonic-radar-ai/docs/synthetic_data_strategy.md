# Synthetic Data Strategy for Radar Intelligence

## 1. Philosophy: Physics-First Generation
Training deep learning models on real radar data is challenging due to the scarcity of labeled tactical datasets. Our approach builds a **Physics-First Synthetic Generator** that simulates the electromagnetic signatures of targets with high fidelity, ensuring that the model learns robust, transferable features.

## 2. Target Modeling
We model targets not as point scatterers, but as complex kinematic entities with distinct micro-Doppler signatures:

### A. Drones (Multi-Rotor)
- **Physics**: We simulate the modulation from $N$ rotors, each with slightly varying RPM.
- **Harmonics**: The blade length $L$ and wavelength $\lambda$ determine the modulation depth ($\beta = \frac{4\pi L}{\lambda}$).
- **Signature**: Multiple sidebands around the central Doppler shift, creating a "fencing" pattern in the Micro-Doppler spectrogram.

### B. Aircraft (Jet Engine Modulation - JEM)
- **Physics**: Radar reflections from the rapidly spinning turbine blades inside the engine duct.
- **Signature**: High-frequency modulation sidebands ($f_{mod} = N_{blades} \times RPM / 60$) that act as a unique "acoustic fingerprint" for classification.

### C. Missiles (High-G Acceleration)
- **Physics**: Targets moving at Mach 3+ with varying acceleration.
- **Signature**: A "chirped" Doppler history where the central frequency shifts linearly or quadratically over the dwell time ($\phi(t) \propto v_0 t + 0.5 a t^2$).

## 3. Photonic Environmental Realism
To ensure the model is robust to the unique noise floor of the PHOENIX-RADAR:
- **WDM Crosstalk**: We inject coherent noise representing leakage from adjacent WDM channels.
- **RIN (Relative Intensity Noise)**: Laser phase noise is propagated through the signal chain to simulate realistic SNR degradation.
- **Clutter**: Non-Gaussian (Weibull/K-distribution) clutter is spatially mapped to train the model to ignore environmental artifacts.

## 4. Metadata-Driven XAI
Unlike standard datasets that only provide class labels, our generator exports full kinematic state vectors (Velocity, RCS, Acceleration, Rotor RPM) validation. This enables **Explainable AI (XAI)**, where we can verify if the model is focusing on the correct features (e.g., rotor flash) rather than spurious background noise.
