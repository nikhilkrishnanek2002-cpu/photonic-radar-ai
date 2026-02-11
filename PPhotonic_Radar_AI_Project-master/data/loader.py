import numpy as np
import os
from typing import Tuple, Dict, Optional

class RealDataLoader:
    """
    Loader for the 'Radar measurements on drones, birds and humans' dataset (Zenodo 5845259).
    Link: https://zenodo.org/record/5845259
    """
    
    def __init__(self, data_path: str = "data/real_world/data_SAAB_SIRS_77GHz_FMCW.npy"):
        self.data_path = data_path
        self._data = None
        self._labels = None # If available in separate file or part of struct
        self._index = 0
        self._num_samples = 0
        self.is_loaded = False
        
    def load(self):
        """Load dataset into memory (mmap mode if possible)."""
        if not os.path.exists(self.data_path):
            print(f"⚠️ Dataset not found at {self.data_path}")
            return False

        try:
            # Load with mmap_mode='r' to avoid loading 1.6GB into RAM instantly
            self._data = np.load(self.data_path, mmap_mode='r')
            self._num_samples = self._data.shape[0]
            self.is_loaded = True
            print(f"✅ Loaded {self._num_samples} real-world radar samples. Shape: {self._data.shape}")
            return True
        except Exception as e:
            print(f"❌ Error loading real dataset: {e}")
            return False

    def get_next_sample(self) -> Optional[np.ndarray]:
        """Return next sample from the dataset."""
        if not self.is_loaded:
            if not self.load():
                return None
        
        sample = self._data[self._index]
        
        # Cycle index
        self._index = (self._index + 1) % self._num_samples
        
        return sample

    def get_shape(self):
        if self.is_loaded:
            return self._data.shape
        return None

if __name__ == "__main__":
    # Test script
    loader = RealDataLoader()
    if loader.load():
        print("Sample shape:", loader.get_shape())
        samp = loader.get_next_sample()
        print("First sample statistics:", np.min(samp), np.max(samp), np.mean(samp))
