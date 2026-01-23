import numpy as np
from scipy.signal import stft, windows

def compute_spectrogram(signal, fs=4096, nperseg=256, noverlap=128):
    """
    Computes the spectrogram (magnitude of STFT) of the signal.
    Returns: frequencies, times, magnitude_spectrogram
    """
    f, t, Zxx = stft(signal, fs=fs, window='hann', nperseg=nperseg, noverlap=noverlap)
    return f, t, np.abs(Zxx)

def compute_range_doppler_map(signal, n_range=128, n_doppler=128):
    """
    Computes the Range-Doppler map from a raw 1D radar signal.
    Assumes the signal contains multiple pulses (slow-time).
    Reshapes internally based on n_range (fast-time samples per pulse).
    """
    # 1. Reshape into Pulses (Slow-time x Fast-time)
    total_samples = len(signal)
    num_pulses = total_samples // n_range
    
    if num_pulses < 2:
        # Not enough data for meaningful Doppler
        return np.zeros((n_doppler, n_range))
    
    # Truncate to fit integral number of pulses
    pulses = signal[:num_pulses * n_range].reshape(num_pulses, n_range)
    
    # 2. Windowing (Optional but recommended)
    # We can apply window in both dimensions
    
    # 3. 2D FFT
    # Axis 1 (Fast-time) -> Range
    # Axis 0 (Slow-time) -> Doppler
    # We use n_doppler for the slow-time FFT size (zero padding if num_pulses < n_doppler)
    
    rd_complex = np.fft.fft2(pulses, s=(n_doppler, n_range))
    rd_shifted = np.fft.fftshift(rd_complex)
    
    return np.abs(rd_shifted)

def compute_wvd_pseudo(signal, fs=4096):
    """
    Computes a pseudo-Wigner-Ville Distribution.
    This is computationally expensive O(N^2), use with localized chunks.
    For this project, we might stick to STFT for performance, but here is a placeholder.
    """
    # Placeholder for now, returning STFT as it's more robust for real-time
    return compute_spectrogram(signal, fs)
