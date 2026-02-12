# PHOENIX-RADAR: Advanced Signal Processing Strategy

## 1. Tactical Processing Flow
The PHOENIX-RADAR pipeline follows a rigorous defense-grade signal chain designed to maximize the Probability of Detection ($P_D$) while strictly controlling the Probability of False Alarm ($P_{fa}$).

```mermaid
graph LR
    A[Raw ADC / Photonic IF] --> B[Fast-Time FFT]
    B --> C[Slow-Time FFT]
    C --> D[NCI Integration]
    D --> E[Adaptive CFAR]
    E --> F[Detection List]
```

## 2. 2D Spectral Analysis
We utilize a two-stage FFT approach to resolve targets in both range and velocity:
- **Range FFT**: Transforms fast-time samples into the spatial domain ($R = \frac{c \cdot \Delta f}{2 \cdot BW}$).
- **Doppler FFT**: Transforms slow-time pulses into the frequency domain to resolve radial velocity ($V = \frac{\lambda \cdot f_d}{2}$).
- **Windowing**: Standardized on **Dolph-Chebyshev** windows with -80dB sidelobe suppression to prevent strong target leakage from masking smaller tactical signatures (e.g., stealth drones).

## 3. Thresholding & CFAR Logic
To maintain situational awareness in dynamic environments, we implement dual-mode Constant False Alarm Rate (CFAR) detection:

### Cell-Averaging (CA-CFAR)
Ideal for homogeneous noise environments. The threshold ($T$) is derived from the mean power of $N$ training cells:
$$T = \alpha \cdot P_{noise}$$
$$\alpha = N \cdot (P_{fa}^{-1/N} - 1)$$

### Ordered-Statistics (OS-CFAR)
Selected for multi-target or "congested" environments. By selecting the $k$-th ranked cell rather than the mean, we prevent high-power targets in the training window from masking adjacent low-RCS targets (target capture effect).

## 4. Multi-Frame Non-Coherent Integration (NCI)
Temporal averaging across frames is used to decorrelate transient noise spikes. By integrating $M$ frames in the linear power domain, we achieve an SNR improvement of approximately $\sqrt{M}$, significantly extending the radar's effective detection range for stealth intruders.

## 5. Clutter Suppression
Spatial clutter models (Weibull/K-distribution) are used to simulate ground and sea spikes. The pipeline effectively suppresses these via adaptive thresholding, ensuring that only true kinematic targets advance to the tracking and AI classification layers.
