"""
Classical radar detection chain utilities: matched filtering, Range/Doppler FFTs,
CA-CFAR and OS-CFAR detectors, and detection-statistics helpers.

This module is intentionally lightweight (NumPy) and designed to be
configurable via `src.config.get_config()` under key `detection`.

"""
from typing import Tuple, List, Dict, Optional
import numpy as np
from .config import get_config
from .logger import log_event


def matched_filter(received: np.ndarray, template: np.ndarray) -> np.ndarray:
    """Apply matched filtering via FFT convolution (linear convolution)."""
    # compute convolution via FFT for speed
    n = len(received) + len(template) - 1
    N = 1 << (n - 1).bit_length()
    R = np.fft.fft(received, N)
    T = np.fft.fft(np.conj(template[::-1]), N)
    y = np.fft.ifft(R * T)[:n]
    return np.abs(y)


def range_doppler_map(pulses: np.ndarray, n_range: int = 128, n_doppler: int = 128) -> np.ndarray:
    """Compute a 2D Range-Doppler map from a pulse matrix (slow-time x fast-time).

    pulses: shape (num_pulses, samples_per_pulse)
    """
    rd = np.fft.fftshift(np.fft.fft2(pulses, s=(n_doppler, n_range)))
    return np.abs(rd)


def ca_cfar(rd_map: np.ndarray, guard: int = 2, train: int = 8, pfa: float = 1e-6) -> Tuple[np.ndarray, float]:
    """Optimized Cell-Averaging CFAR using 2D convolution (FFT) for speed.

    The training window is the full window (train+guard) with the inner guard+CUT removed.
    Returns boolean detection map and alpha multiplier used for thresholding.
    """
    from scipy.signal import fftconvolve

    M, N = rd_map.shape
    full_h = 2 * train + 2 * guard + 1
    full_w = 2 * train + 2 * guard + 1
    inner_h = 2 * guard + 1
    inner_w = 2 * guard + 1

    # kernel for full window and inner (guard+CUT) window
    k_full = np.ones((full_h, full_w), dtype=float)
    k_inner = np.ones((inner_h, inner_w), dtype=float)

    # convolve to get sum over windows (same size as rd_map)
    sum_full = fftconvolve(rd_map, k_full, mode="same")
    sum_inner = fftconvolve(rd_map, k_inner, mode="same")

    num_train = full_h * full_w - inner_h * inner_w
    num_train = max(1, num_train)
    try:
        alpha = num_train * (pfa ** (-1.0 / num_train) - 1.0)
    except Exception:
        alpha = 1.0

    # training sum = full - inner
    train_sum = sum_full - sum_inner
    # avoid division by zero
    noise_level = train_sum / num_train
    noise_level[noise_level <= 0] = 1e-12

    threshold = noise_level * alpha
    det = rd_map > threshold

    log_event(f"CA-CFAR detections: {np.count_nonzero(det)}", level="info")
    return det, float(alpha)


def os_cfar(rd_map: np.ndarray, guard: int = 2, train: int = 16, rank: Optional[int] = None, pfa: float = 1e-6) -> Tuple[np.ndarray, float]:
    """Order-Statistic CFAR: select k-th ordered training cell as noise estimate.

    rank: position (1-based) in sorted training cells; default median (len/2)
    Returns detection map and multiplier (1.0 for OS since threshold uses statistic directly).
    """
    M, N = rd_map.shape
    det = np.zeros_like(rd_map, dtype=bool)
    for i in range(M):
        for j in range(N):
            i1 = max(0, i - train - guard)
            i2 = min(M, i + train + guard + 1)
            j1 = max(0, j - train - guard)
            j2 = min(N, j + train + guard + 1)

            cut_i1 = max(0, i - guard)
            cut_i2 = min(M, i + guard + 1)
            cut_j1 = max(0, j - guard)
            cut_j2 = min(N, j + guard + 1)

            window = rd_map[i1:i2, j1:j2].copy()
            window[cut_i1 - i1:cut_i2 - i1, cut_j1 - j1:cut_j2 - j1] = 0
            train_cells = window.flatten()
            train_cells = train_cells[train_cells != 0]
            if train_cells.size == 0:
                continue
            train_cells.sort()
            if rank is None:
                k = max(1, len(train_cells) // 2)
            else:
                k = min(len(train_cells), max(1, rank))
            noise_est = train_cells[k - 1]
            # use alpha that yields pfa roughly; simple scale factor
            alpha = 1.0
            if rd_map[i, j] > noise_est * alpha:
                det[i, j] = True

    log_event(f"OS-CFAR detections: {np.count_nonzero(det)}", level="info")
    return det, 1.0


def detect_targets_from_raw(signal: np.ndarray, fs: float = 4096, n_range: int = 128, n_doppler: int = 128,
                            method: str = "ca", **kwargs) -> Dict:
    """Full detection pipeline from raw complex signal to detection list.

    Returns dict with rd_map, det_map, detections (list of (i,j,value)), and stats.
    """
    # Reshape into pulses
    num_pulses = len(signal) // n_range
    if num_pulses == 0:
        rd_map = np.zeros((n_doppler, n_range))
    else:
        pulses = signal[:num_pulses * n_range].reshape(num_pulses, n_range)
        rd_map = range_doppler_map(pulses, n_range=n_range, n_doppler=n_doppler)

    if method.lower().startswith("ca"):
        det_map, alpha = ca_cfar(rd_map, **kwargs)
    else:
        det_map, alpha = os_cfar(rd_map, **kwargs)

    inds = list(zip(*np.where(det_map)))
    detections = [(int(i), int(j), float(rd_map[i, j])) for i, j in inds]

    stats = {
        "num_detections": len(detections),
        "alpha": alpha,
        "pfa_requested": kwargs.get("pfa", None)
    }

    log_event(f"Detection stats: {stats}", level="info")

    return {
        "rd_map": rd_map,
        "det_map": det_map,
        "detections": detections,
        "stats": stats
    }
