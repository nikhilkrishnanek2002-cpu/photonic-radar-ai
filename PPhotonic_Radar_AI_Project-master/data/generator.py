import numpy as np
from scipy.signal import butter, sosfilt
import time
from typing import List, Dict, Optional, Tuple

from src.signal.photonic_model import generate_photonic_rf
from src.config import get_config

class Target:
    def __init__(self, range_m: float, velocity_m_s: float, rcs_db: float, category: str):
        self.range_m = range_m
        self.velocity_m_s = velocity_m_s
        self.rcs_db = rcs_db
        self.category = category # 'drone', 'bird', 'aircraft', etc.

class RadarGenerator:
    """
    Simulates the entire radar chain:
    1. Photonic RF Generation (Tx)
    2. Channel Propagation (Delay, Doppler, Attenuation)
    3. Receiver Mixing (De-chirping) and Filtering
    """
    def __init__(self, fs=4096, max_range=200):
        self.fs = fs
        self.max_range = max_range
        self.c = 3e8 # Speed of light
        
        # Load config to get wave params
        self.cfg = get_config()
        self.model_cfg = self.cfg.get("photonic_model", {})
        
        # Override for baseband simulation if needed
        # If fs is low, we force LO offset to 0 to avoid aliasing
        if self.fs < 1e6:
             self.model_cfg['local_osc_freq_offset_hz'] = 0.0
        
        # Ensure we have bandwidth
        if 'fmcw_bandwidth_hz' not in self.model_cfg:
             self.model_cfg['fmcw_bandwidth_hz'] = 500e6 # 500 MHz default
        if 'fmcw_chirp_period_s' not in self.model_cfg:
             self.model_cfg['fmcw_chirp_period_s'] = 1.0 # 1 second chirp for demo visual
             
    def simulate_scenario(self, targets: List[Target], duration: float = 1.0) -> Dict[str, np.ndarray]:
        """
        Generates the IF (Intermediate Frequency) signal for the given targets.
        """
        # 1. Generate Transmitted Signal (Tx)
        # We perform simulation at higher resolution if possible, but for Python speed we stick to fs
        # This approximates Baseband simulation
        
        t, tx_sig_channels = generate_photonic_rf(
            duration=duration, 
            fs=self.fs, 
            num_channels=1, 
            cfg_override=self.model_cfg
        )
        tx_sig = tx_sig_channels[0] # Single channel for now
        
        rx_total = np.zeros_like(tx_sig)
        
        # 2. Simulate Echoes
        for target in targets:
            # Calculate delay and doppler
            tau = 2 * target.range_m / self.c
            delay_samples = tau * self.fs
            
            # Simple integer delay for now (fractional could be better)
            d_int = int(round(delay_samples))
            
            # Attenuation (Radar equation simplified)
            # Pr ~ Pt * G^2 * lambda^2 * RCS / ((4pi)^3 * R^4)
            # Linear scale factor
            rcs_lin = 10**(target.rcs_db / 10)
            # heavy attenuation dummy model
            attenuation = 1e-3 * rcs_lin / max(1.0, target.range_m**2) 
            
            if d_int < len(tx_sig):
                # Create delayed copy
                echo = np.zeros_like(tx_sig)
                if d_int > 0:
                    echo[d_int:] = tx_sig[:-d_int]
                else:
                    echo[:] = tx_sig
                
                # Apply Doppler shift
                # fd = 2 * v / lambda. 
                # Carrier freq ~ 77GHz? Or optical?
                # Photonic radar -> RF carrier. Let's assume 77GHz eq.
                fc = 77e9
                fd = 2 * target.velocity_m_s * fc / self.c
                
                # Apply phase ramp exp(j*2*pi*fd*t)
                # Since signals are Real, we modulate: echo * cos(2*pi*fd*t)
                doppler_mod = np.cos(2 * np.pi * fd * t)
                
                rx_component = echo * attenuation * doppler_mod
                rx_total += rx_component

        # 3. Add Noise (Receiver Noise)
        noise_floor = np.random.normal(0, 1e-4, size=len(t))
        rx_total += noise_floor
        
        # 4. Mix and Filter (De-chirp)
        # Mixer = Tx * Rx
        raw_mixed = tx_sig * rx_total
        
        # Low Pass Filter to remove sum-frequency terms
        # Cutoff: needs to pass the beat frequencies. 
        # Beat freq fb = Slope * tau = (BW/T) * (2R/c)
        # Max fb = (500e6 / 1.0) * (2*200 / 3e8) = 500e6 * 1.33e-6 = 666 Hz
        # So LPF close to 1kHz is fine.
        nyq = 0.5 * self.fs
        cutoff = min(nyq - 1, 2000) 
        sos = butter(4, cutoff, 'low', fs=self.fs, output='sos')
        if_signal = sosfilt(sos, raw_mixed)
        
        # Return as Complex (Analytic) for compatibility with range_doppler algorithm?
        # The detection.py logic uses FFT. Real input to FFT is fine, gives symmetric spectrum.
        # But commonly we want complex baseband.
        # Let's convert to analytic signal simply via Hilbert? Or just return real.
        # For now, return complex by adding 0j, but it is real data.
        # Actually detection logic might expect complex.
        
        # Wait, standard RD map on Real data mirrors.
        # Let's return Real data and handle it in processing or make it complex via Hilbert.
        # Just casting to complex for now.
        return {
            "t": t,
            "tx": tx_sig.astype(np.complex64),
            "rx": rx_total.astype(np.complex64),
            "if_signal": if_signal.astype(np.complex64)
        }

