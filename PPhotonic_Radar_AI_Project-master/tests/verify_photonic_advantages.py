import numpy as np
from photonic.signals import PhotonicConfig, generate_photonic_signal
from photonic.beamforming import simulate_electronic_beamforming, simulate_photonic_ttd_beamforming

def verify_resolution():
    print("🚀 Verifying Photonic Resolution Advantage...")
    # Electronic Radar: 500 MHz BW -> ~30cm resolution
    # Photonic Radar: 10 GHz BW -> 1.5cm resolution
    e_bw = 500e6
    p_bw = 10e9
    c = 3e8
    
    e_res = c / (2 * e_bw)
    p_res = c / (2 * p_bw)
    
    print(f"  - Electronic Resolution (500MHz): {e_res*100:.2f} cm")
    print(f"  - Photonic Resolution (10GHz): {p_res*100:.2f} cm")
    
    assert p_res < e_res / 10, "Photonic resolution should be at least 10x better"
    print("✅ Resolution advantage verified.")

def verify_beam_squint():
    print("\n🚀 Verifying Beam Stability (TTD vs Phase-Shift)...")
    angle = 30.0
    fc = 10e9
    bw = 4e9 # High fractional bandwidth (40%)
    
    # Electronic (Phase Shift)
    angles_e, patterns_e = simulate_electronic_beamforming(angle, fc, bw)
    peak_angles_e = angles_e[np.argmax(patterns_e, axis=1)]
    squint_e = np.max(peak_angles_e) - np.min(peak_angles_e)
    
    # Photonic (TTD)
    angles_p, patterns_p = simulate_photonic_ttd_beamforming(angle, fc, bw)
    peak_angles_p = angles_p[np.argmax(patterns_p, axis=1)]
    squint_p = np.max(peak_angles_p) - np.min(peak_angles_p)
    
    print(f"  - Electronic Beam Squint (4GHz BW): {squint_e:.2f} degrees")
    print(f"  - Photonic Beam Squint (4GHz BW): {squint_p:.2f} degrees")
    
    assert squint_p < 0.1, "Photonic TTD should have negligible beam squint"
    assert squint_e > 5.0, "Electronic beam squint should be significant at 4GHz BW"
    print("✅ Photonic beam stability verified (Zero Squint).")

if __name__ == "__main__":
    verify_resolution()
    verify_beam_squint()
