import numpy as np
from scipy.signal import spectrogram
from signal_generator import generate_radar_signal

def create_dataset(samples=200):
    classes = ["drone", "aircraft", "bird", "clutter"]
    X, y = [], []

    for label, cls in enumerate(classes):
        for _ in range(samples):
            sig = generate_radar_signal(cls)
            _, _, Sxx = spectrogram(sig)
            Sxx = Sxx[:128, :128]
            X.append(Sxx)
            y.append(label)

    X = np.array(X)
    X = X / np.max(X)
    X = X.reshape(-1, 128, 128, 1)

    return X, np.array(y)
