import numpy as np
from src.detection import detect_targets_from_raw


def make_synthetic_signal(n_range=128, n_pulses=16, peak_range=30, peak_doppler=8, amp=10.0):
    # create pulses with a strong return at a given fast-time index across pulses
    pulses = np.random.normal(0, 0.1, size=(n_pulses, n_range))
    for p in range(n_pulses):
        pulses[p, peak_range] += amp * (1 + 0.1 * np.sin(2 * np.pi * p / n_pulses))
    return pulses.flatten()


def test_cfar_detects_peak():
    sig = make_synthetic_signal()
    res = detect_targets_from_raw(sig, fs=4096, n_range=128, n_doppler=16, method='ca', guard=1, train=4, pfa=1e-3)
    assert res['stats']['num_detections'] > 0
