import numpy as np
from scipy.signal import stft

def extract_range_doppler(signal, n_fft=128):
    """
    Computes the Range-Doppler map using 2D FFT.
    In a real system, this involves FFT across fast-time and slow-time.
    Here we simulate it by reshaping the signal.
    """
    # Reshape signal to simulate pulses (slow-time) and samples (fast-time)
    num_pulses = len(signal) // n_fft
    if num_pulses == 0:
        return np.zeros((n_fft, n_fft))
    
    pulses = signal[:num_pulses * n_fft].reshape(num_pulses, n_fft)
    
    # 2D FFT: Fast-time FFT (range) then Slow-time FFT (Doppler)
    rd_map = np.fft.fft2(pulses, s=(n_fft, n_fft))
    rd_map = np.fft.fftshift(rd_map)
    return np.abs(rd_map)

def extract_micro_doppler(signal, fs=4096, nperseg=256):
    """
    Computes Micro-Doppler spectrogram using STFT.
    """
    f, t, Zxx = stft(signal, fs=fs, nperseg=nperseg)
    return np.abs(Zxx)

def extract_phase_statistics(signal):
    """
    Calculates phase-related statistics from the complex signal.
    """
    phase = np.angle(signal)
    mean_phase = np.mean(phase)
    var_phase = np.var(phase)
    # Coherence as a simple measure of phase stability
    coherence = np.abs(np.mean(np.exp(1j * phase)))
    
    return {
        "mean_phase": mean_phase,
        "var_phase": var_phase,
        "coherence": coherence
    }

def estimate_photonic_parameters(signal, bandwidth=1e9, pulse_width=10e-6):
    """
    Estimates photonic-specific radar parameters.
    """
    # Simulated True Time Delay (TTD) beamforming vector (8-element array)
    ttd_vector = np.exp(-1j * 2 * np.pi * 0.5 * np.arange(8))
    
    # Noise and clutter estimation
    noise_power = np.var(signal[-100:]) if len(signal) > 100 else 0.01
    clutter_power = np.var(signal[:100]) if len(signal) > 100 else 0.05
    
    chirp_slope = bandwidth / pulse_width
    
    return {
        "instantaneous_bandwidth": bandwidth,
        "chirp_slope": chirp_slope,
        "pulse_width": pulse_width,
        "ttd_vector": np.abs(ttd_vector).tolist(),
        "noise_power": float(noise_power),
        "clutter_power": float(clutter_power)
    }

def get_all_features(signal, fs=4096):
    rd_map = extract_range_doppler(signal)
    spectrogram = extract_micro_doppler(signal, fs=fs)
    phase_stats = extract_phase_statistics(signal)
    photonic_params = estimate_photonic_parameters(signal)
    
    # Combine metadata
    metadata = np.array([
        phase_stats['mean_phase'],
        phase_stats['var_phase'],
        phase_stats['coherence'],
        photonic_params['instantaneous_bandwidth'],
        photonic_params['chirp_slope'],
        photonic_params['pulse_width'],
        photonic_params['noise_power'],
        photonic_params['clutter_power']
    ], dtype=np.float32)
    
    return rd_map, spectrogram, metadata, photonic_params
