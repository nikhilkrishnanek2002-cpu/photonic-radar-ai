"""
Synthetic Radar Dataset Generator
=================================

This module generates large-scale synthetic datasets for training 
Radar AI models. It leverages the photonic and signal_processing layers 
to create physically realistic samples.

Classes:
- Drone: High micro-Doppler variance.
- Aircraft: Large RCS, steady trajectory.
- Missile: High velocity, low micro-Doppler.
- Noise: Thermal/Clutter background.

Author: Radar AI Engineer
"""

import numpy as np
import os
import torch
from typing import Tuple, List, Dict
from photonic.signals import generate_photonic_signal
from signal_processing.transforms import compute_range_doppler_map, compute_spectrogram
from signal_processing.noise import add_awgn, generate_clutter

class RadarDatasetGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.classes = ["drone", "aircraft", "missile", "bird", "noise"]
        
    def generate_sample(self, target_class: str) -> Dict[str, np.ndarray]:
        """
        Generates a physically realistic multi-modal sample.
        Includes complex modulation for Micro-Doppler and tactical noise.
        """
        duration = self.config.get('duration', 0.1)
        fs = self.config.get('fs', 5e5)
        n_samples = int(fs * duration)
        t = np.arange(n_samples) / fs
        
        # 1. Physics-based Signal Generation
        if target_class == "noise":
            # Tactical Clutter (Sea/Urban mix)
            signal = generate_clutter(n_samples, distribution='k', shape=1.5, scale=2.0)
        
        elif target_class == "bird":
            # Biological modulation: Low frequency, erratic amplitude
            v = np.random.uniform(5, 15)
            flapping_freq = np.random.uniform(3, 10)
            carrier = np.exp(1j * 2 * np.pi * v * t)
            # Amplitude modulation for wing flapping
            am = 0.5 * (1 + 0.6 * np.sin(2 * np.pi * flapping_freq * t))
            signal = carrier * am
            
        else:
            params = {
                "drone": {"v": 15, "rcs": -15, "rotors": 4, "rpm": 15000, "blade_len": 0.15},
                "aircraft": {"v": 250, "rcs": 25, "jem_blades": 32, "jem_rpm": 8000},
                "missile": {"v_start": 400, "accel": 150, "rcs": 5}
            }[target_class]
            
            if target_class == "drone":
                # Multi-rotor simulation with multiple blade harmonics
                v_actual = params["v"] + np.random.normal(0, 3)
                carrier = np.exp(1j * 2 * np.pi * v_actual * t)
                
                md_signal = np.zeros(n_samples, dtype=complex)
                for _ in range(params["rotors"]):
                    rpm = params["rpm"] + np.random.normal(0, 1000)
                    fm = rpm / 60.0 # modulation freq
                    # Phase modulation depth proportional to blade length/wavelength
                    # lambda = 3cm @ 10GHz
                    beta = (2 * np.pi * params["blade_len"]) / 0.03
                    # Drone signature often has multiple harmonics (blade edges)
                    md_signal += np.exp(1j * beta * np.sin(2 * np.pi * fm * t))
                    md_signal += 0.3 * np.exp(1j * 2 * beta * np.sin(2 * np.pi * fm * t))
                
                signal = carrier * (md_signal / params["rotors"])
                
            elif target_class == "aircraft":
                # Jet Engine Modulation (JEM)
                # JEM is the chopping of the radar signal by turbine blades
                v_actual = params["v"] + np.random.normal(0, 5)
                carrier = np.exp(1j * 2 * np.pi * v_actual * t)
                
                # JEM frequency = N_blades * RPM / 60
                jem_freq = params["jem_blades"] * params["jem_rpm"] / 60.0
                # JEM typically appears as sidebands in the spectrum
                jem_modulation = 1 + 0.2 * np.cos(2 * np.pi * jem_freq * t)
                signal = carrier * jem_modulation
                
            elif target_class == "missile":
                # High speed with linear acceleration (Doppler drift)
                v0 = params["v_start"] + np.random.normal(0, 50)
                a = params["accel"] + np.random.normal(0, 20)
                # Phase is integral of freq: phi = 2pi * integral( v/lambda dt )
                # lambda = 0.03m
                # v(t) = v0 + a*t
                # phi(t) = 2pi * (v0*t + 0.5*a*t^2) / lambda
                phase = (2 * np.pi / 0.03) * (v0 * t + 0.5 * a * t**2)
                signal = np.exp(1j * phase)

        # 2. Photonic Noise Integration (WDM/MDM Crosstalk simulation)
        # We simulate the effects of optical nonlinearities and crosstalk
        snr = np.random.uniform(5, 30)
        signal = add_awgn(signal, snr_db=snr)
        
        # Add a subtle "channel hum" representing MDM crosstalk
        hum_freq = 50.0 # Hz
        signal += 0.01 * np.exp(1j * 2 * np.pi * hum_freq * t)

        # 3. Feature Extraction
        # Range-Doppler Tensor (Spatial)
        rd_map = compute_range_doppler_map(signal, n_chirps=64, samples_per_chirp=n_samples//64)
        
        # Spectrogram (Temporal Frequency)
        spec = compute_spectrogram(signal, fs=fs, nperseg=256, noverlap=128)
        
        # 4. Metadata Enrichment (For XAI and tracking validation)
        metadata = {
            "class": target_class,
            "snr_db": snr,
            "kinematics": params if target_class not in ["noise", "bird"] else {},
            "dt": duration
        }
        
        # Sub-sampled IQ for time-series branch
        ts_points = 512
        time_series = np.stack([np.real(signal[:ts_points]), np.imag(signal[:ts_points])])
        
        return {
            "rd_map": rd_map,
            "spectrogram": spec,
            "time_series": time_series,
            "label": self.classes.index(target_class),
            "metadata": metadata
        }

    def generate_batch(self, samples_per_class: int = 50) -> Dict[str, torch.Tensor]:
        """
        Generates a full batch ready for training.
        """
        all_rd, all_spec, all_ts, all_y = [], [], [], []
        
        for cls in self.classes:
            for _ in range(samples_per_class):
                sample = self.generate_sample(cls)
                all_rd.append(sample["rd_map"])
                all_spec.append(sample["spectrogram"])
                all_ts.append(sample["time_series"])
                all_y.append(sample["label"])
                
        return {
            "rd_maps": torch.tensor(np.array(all_rd), dtype=torch.float32).unsqueeze(1),
            "spectrograms": torch.tensor(np.array(all_spec), dtype=torch.float32).unsqueeze(1),
            "time_series": torch.tensor(np.array(all_ts), dtype=torch.float32),
            "labels": torch.tensor(np.array(all_y), dtype=torch.long)
        }

if __name__ == "__main__":
    cfg = {"duration": 0.05, "fs": 1e5}
    gen = RadarDatasetGenerator(cfg)
    batch = gen.generate_batch(5)
    print(f"Generated batch | RD shape: {batch['rd_maps'].shape} | Labels: {batch['labels']}")
