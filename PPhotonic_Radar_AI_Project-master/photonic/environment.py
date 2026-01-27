"""
Radar Channel Environment
========================

This module simulates the physical environment, including target reflection and channel effects.
It implements the breakdown of the transmitted signal into multiple echoes, each affected by:
1. Time Delay (Range)
2. Phase Rotation (Doppler)
3. Attenuation (Radar Equation)
4. Channel Noise (AWGN)

Author: Principal Photonic Radar Scientist
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Target:
    """Represents a physical radar target."""
    range_m: float          # Distance in meters
    velocity_m_s: float     # Radial velocity in m/s (positive = approaching)
    rcs_dbsm: float        # Radar Cross Section in dBsm
    description: str = "Unknown"

@dataclass
class ChannelConfig:
    """Configuration for the Environment."""
    c: float = 3e8          # Speed of light (m/s)
    carrier_freq: float = 10e9 # Carrier Frequency (Hz)
    noise_level_db: float = -50.0 # Noise floor relative to signal
    n_wavelengths: int = 1      # WDM: Number of wavelengths
    n_modes: int = 1            # MDM: Number of spatial modes
    wdm_spacing_hz: float = 100e9 # 100 GHz standard WDM spacing

def simulate_target_response(
    tx_signal: np.ndarray, 
    fs: float, 
    targets: List[Target], 
    config: ChannelConfig
) -> np.ndarray:
    """
    Simulates the receiver channel response for a list of targets.

    Args:
        tx_signal: The transmitted time-domain signal.
        fs: Sampling frequency (Hz).
        targets: List of Target objects.
        config: ChannelConfig parameters.

    Returns:
        rx_signal: The combined received signal with noise (complex).
                   If multi-channel, returns a dict of signals per channel.
    """
    n_samples = len(tx_signal)
    
    # 1. Orchestrate Channels (WDM x MDM)
    # Each channel effectively sees a slightly different Doppler shift due to fc
    channel_responses = {}
    
    for w in range(config.n_wavelengths):
        for m in range(config.n_modes):
            channel_id = f"W{w}_M{m}"
            fc_eff = config.carrier_freq + (w * config.wdm_spacing_hz)
            
            rx_chan = np.zeros(n_samples, dtype=complex)
            t = np.arange(n_samples) / fs
            
            # 2. Pre-calculate noise per channel
            noise_power = 10**(config.noise_level_db / 10)
            noise = (np.random.normal(0, np.sqrt(noise_power/2), n_samples) + \
                    1j * np.random.normal(0, np.sqrt(noise_power/2), n_samples))
            
            # 3. Superposition of Echoes
            for tgt in targets:
                # Delay tau = 2R/c
                tau = 2 * tgt.range_m / config.c
                delay_samples = int(round(tau * fs))
                
                # Doppler Freq fd = 2*v*fc/c (fc changes with wavelength)
                f_doppler = (2 * tgt.velocity_m_s * fc_eff) / config.c
                
                # Attenuation (Simplified Radar Equation)
                rcs_linear = 10**(tgt.rcs_dbsm / 10)
                r_safe = max(tgt.range_m, 1.0)
                # Scale factor (adjusted for multi-channel energy distribution)
                amplitude_scale = 1e4 * np.sqrt(rcs_linear) / (r_safe**2) 
                
                # 4. Construct Echo
                echo = np.zeros(n_samples, dtype=complex)
                if delay_samples < n_samples:
                    valid_len = n_samples - delay_samples
                    echo[delay_samples:] = tx_signal[:valid_len]
                
                # Apply Doppler Phase Rotation
                doppler_mod = np.exp(1j * 2 * np.pi * f_doppler * t)
                echo *= doppler_mod
                
                # Apply Attenuation
                echo *= amplitude_scale
                
                # Accumulate
                rx_chan += echo
            
            # Add Noise and Store
            rx_chan += noise
            channel_responses[channel_id] = rx_chan
            
    # If single channel, return array for backward compatibility
    if len(channel_responses) == 1:
        return list(channel_responses.values())[0]
        
    return channel_responses

if __name__ == "__main__":
    # Test
    fs = 1e6
    t = np.arange(1000) / fs
    tx = np.exp(1j * 2 * np.pi * 10e3 * t) # Simple tone
    cfg = ChannelConfig()
    tgts = [Target(range_m=100, velocity_m_s=30, rcs_dbsm=0)]
    
    rx = simulate_target_response(tx, fs, tgts, cfg)
    print(f"Generated RX signal: {rx.shape}, Max Amp: {np.max(np.abs(rx)):.4e}")
