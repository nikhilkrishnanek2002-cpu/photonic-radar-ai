"""
True-Time Delay (TTD) Beamforming Logic
=======================================

This module compares Photonic True-Time Delay (TTD) with conventional 
Electronic Phase-Shifting to highlight the "Beam Squint" phenomenon.

Author: Principal Photonic Radar Scientist
"""

import numpy as np
from typing import Tuple

def simulate_electronic_beamforming(
    steering_angle_deg: float, 
    center_freq: float, 
    bandwidth: float, 
    n_elements: int = 16, 
    d_lambda: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulates electronic phase-shifted beamforming.
    Shows "Beam Squint" where the beam direction shifts with frequency.
    """
    c = 3e8
    lambda0 = c / center_freq
    d = d_lambda * lambda0
    theta0 = np.radians(steering_angle_deg)
    
    # Range of frequencies in the pulse
    freqs = np.linspace(center_freq - bandwidth/2, center_freq + bandwidth/2, 100)
    
    # Requested phase shift at center frequency
    # Delta_phi = 2*pi * d * sin(theta0) / lambda0
    delta_phi_center = 2 * np.pi * d * np.sin(theta0) / lambda0
    
    # Beam patterns per frequency
    angles = np.linspace(-90, 90, 500)
    theta = np.radians(angles)
    patterns = []
    
    for f in freqs:
        lam = c / f
        # Array Factor: AF = sum( exp(j * (k*d*sin(theta) - n*delta_phi_center)) )
        # Note: delta_phi_center is FIXED (electronic phase shifter)
        af = np.zeros_like(theta, dtype=complex)
        for n in range(n_elements):
            phi_n = n * delta_phi_center
            af += np.exp(1j * (2 * np.pi * n * d * np.sin(theta) / lam - phi_n))
        patterns.append(np.abs(af)**2)
        
    return angles, np.array(patterns)

def simulate_photonic_ttd_beamforming(
    steering_angle_deg: float, 
    center_freq: float, 
    bandwidth: float, 
    n_elements: int = 16, 
    d_lambda: float = 0.5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulates photonic True-Time Delay (TTD) beamforming.
    Shows stable beam across the entire bandwidth (No Squint).
    """
    c = 3e8
    lambda0 = c / center_freq
    d = d_lambda * lambda0
    theta0 = np.radians(steering_angle_deg)
    
    # Range of frequencies
    freqs = np.linspace(center_freq - bandwidth/2, center_freq + bandwidth/2, 100)
    
    # Requested Time Delay (Photonic)
    # Delta_tau = d * sin(theta0) / c
    delta_tau = d * np.sin(theta0) / c
    
    # Beam patterns per frequency
    angles = np.linspace(-90, 90, 500)
    theta = np.radians(angles)
    patterns = []
    
    for f in freqs:
        lam = c / f
        # Array Factor: AF = sum( exp(j * 2*pi*f * (n*d*sin(theta)/c - n*delta_tau)) )
        # Note: tau is constant, so phase shift changes LINEARLY with frequency.
        af = np.zeros_like(theta, dtype=complex)
        for n in range(n_elements):
            phase_n = 2 * np.pi * f * n * delta_tau
            af += np.exp(1j * (2 * np.pi * f * n * d * np.sin(theta) / c - phase_n))
        patterns.append(np.abs(af)**2)
        
    return angles, np.array(patterns)
