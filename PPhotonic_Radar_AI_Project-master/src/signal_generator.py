# ===== src/signal_generator.py =====
import numpy as np
from scipy.signal import chirp

from .config import get_config
from .photonic_signal_model import generate_photonic_rf

USE_RTL_SDR = False  # 🔴 SET TRUE when hardware connected

if USE_RTL_SDR:
    from src.rtl_sdr_receiver import RTLRadar
    rtl = RTLRadar()


def generate_radar_signal(target_type, distance=100, fs=4096):
    cfg = get_config()
    photonic_cfg = cfg.get("photonic_model", {})
    use_photonic = photonic_cfg.get("enabled", False)

    if USE_RTL_SDR:
        return rtl.read_samples()

    # If photonic model enabled, use generate_photonic_rf for end-to-end replacement
    if use_photonic:
        # duration=1 second to match previous behavior where t spans 0..1
        seed = photonic_cfg.get("seed", None)
        t, signals = generate_photonic_rf(duration=1.0, fs=fs, num_channels=1, seed=seed)
        # return single-channel complex baseband representation (real->complex)
        out = signals[0].astype(np.complex64) + 0j
        return out

    # ---- existing simulated logic (MODIFIED for Photonic Research Terminology) ----
    t = np.linspace(0, 1, fs)
    # Add random phase and amplitude jitter to noise
    noise_amp = np.random.uniform(0.01, 0.1)
    noise = np.random.normal(0, noise_amp, len(t))
    
    # Distance attenuation with some randomness
    dist_jitter = distance * np.random.uniform(0.95, 1.05)
    attenuation = (100 / max(dist_jitter, 1)) ** 2

    # Randomize chirp parameters slightly for each generation
    f0_offset = np.random.uniform(-100, 100)
    f1_offset = np.random.uniform(-200, 200)

    # Photonic-assisted signal generation
    # Simulating complex baseband representation
    if target_type == "drone":
        # Low RCS, oscillating micro-Doppler component
        signal = chirp(t, 100+f0_offset, 1, 200+f1_offset) + 0.1 * np.sin(2 * np.pi * (50 + np.random.uniform(-5, 5)) * t)
    elif target_type == "aircraft":
        # Large RCS, stable Doppler
        signal = chirp(t, 300+f0_offset, 1, 500+f1_offset)
    elif target_type == "missile":
        # High velocity, fast chirp rate
        signal = chirp(t, 800+f0_offset, 1, 1500+f1_offset)
    elif target_type == "helicopter":
        # Distinct rotor-blade micro-Doppler
        signal = chirp(t, 200+f0_offset, 1, 300+f1_offset) + 0.5 * np.sin(2 * np.pi * (120 + np.random.uniform(-10, 10)) * t)
    elif target_type == "bird":
        # Biological clutter, slow movement
        signal = chirp(t, 50+f0_offset, 1, 80+f1_offset) + 0.05 * np.random.randn(len(t))
    elif target_type == "clutter":
        # Stochastic Clutter
        signal = np.random.normal(0, 0.4, len(t))
    else:
        # Fallback for any unknown types
        signal = np.random.normal(0, 0.1, len(t))

    # Convert to complex signal to represent I/Q data in photonic radar
    complex_signal = (signal * attenuation + noise).astype(np.complex64)
    # Add a synthetic phase component
    complex_signal *= np.exp(1j * np.pi / 4) 
    
    return complex_signal
