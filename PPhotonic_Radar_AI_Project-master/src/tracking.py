# ===== src/tracking.py =====
# ===== src/tracking.py =====
import numpy as np

class KalmanTracker:
    def __init__(self):
        self.A = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]])
        self.H = np.array([[1,0,0,0],[0,1,0,0]])
        self.P = np.eye(4)
        self.Q = np.eye(4)*0.01
        self.R = np.eye(2)*0.1
        self.x = np.zeros((4,1))
        self.history = []

    def update(self, z):
        z = np.array(z).reshape(2,1)
        self.x = self.A @ self.x
        self.P = self.A @ self.P @ self.A.T + self.Q
        K = self.P @ self.H.T @ np.linalg.inv(self.H @ self.P @ self.H.T + self.R)
        self.x = self.x + K @ (z - self.H @ self.x)

        pos = (float(self.x[0].item()), float(self.x[1].item()))
        self.history.append(pos)
        self.history = self.history[-20:]
        return self.x[:2]
