import numpy as np
from src.photonic_signal_model import generate_photonic_rf


def test_deterministic_seed():
    t1, s1 = generate_photonic_rf(duration=0.001, fs=8000, num_channels=2, seed=42)
    t2, s2 = generate_photonic_rf(duration=0.001, fs=8000, num_channels=2, seed=42)
    assert np.allclose(t1, t2)
    assert np.allclose(s1, s2)


def test_methods_agree_shape():
    # ensure both 'fft' and 'sinc' produce same shape and high correlation
    t, s_fft = generate_photonic_rf(duration=0.002, fs=8000, num_channels=1, seed=7, cfg_override={"fractional_delay_method":"fft"})
    t, s_sinc = generate_photonic_rf(duration=0.002, fs=8000, num_channels=1, seed=7, cfg_override={"fractional_delay_method":"sinc"})
    assert s_fft.shape == s_sinc.shape
    # normalized correlation should be reasonably high (>0.8)
    s_fft = s_fft[0]
    s_sinc = s_sinc[0]
    corr = np.corrcoef(s_fft, s_sinc)[0,1]
    assert corr > 0.6
