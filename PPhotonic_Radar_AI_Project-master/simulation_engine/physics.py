"""
Kinematic Physics Engine
========================

Simulates target motion using classical mechanics.
Supports:
- Constant Velocity (CV) model.
- Constant Acceleration (CA) model.

Mathematical Model:
p(t+dt) = p(t) + v(t)*dt + 0.5*a(t)*dt^2
v(t+dt) = v(t) + a(t)*dt

Author: Simulation Engineer
"""

import numpy as np
from dataclasses import dataclass

@dataclass
class TargetState:
    id: int
    pos_x: float            # Cartesian X (meters)
    pos_y: float            # Cartesian Y (meters)
    vel_x: float            # Velocity X (m/s)
    vel_y: float            # Velocity Y (m/s)
    acc_x: float = 0.0      # Acceleration X (m/s^2)
    acc_y: float = 0.0      # Acceleration Y (m/s^2)
    type: str = "civilian"
    maneuver_type: str = "linear"

    @property
    def range_m(self) -> float:
        return np.sqrt(self.pos_x**2 + self.pos_y**2)

    @property
    def azimuth_deg(self) -> float:
        return np.degrees(np.arctan2(self.pos_y, self.pos_x))

    @property
    def radial_velocity(self) -> float:
        # v_rad = (v . r) / |r|
        r_mag = self.range_m
        if r_mag == 0: return 0.0
        return (self.vel_x * self.pos_x + self.vel_y * self.pos_y) / r_mag

class KinematicEngine:
    def __init__(self, dt: float):
        self.dt = dt
        self.time = 0.0

    def update_state(self, state: TargetState) -> TargetState:
        """
        Calculates the next state based on current kinematics and maneuver models in 2D.
        """
        self.time += self.dt
        
        ax, ay = state.acc_x, state.acc_y
        
        # Maneuver Logic (Simplified 2D)
        if state.maneuver_type == "sinusoidal":
            # Circular loitering or weaving
            ax = 2.0 * np.cos(0.5 * self.time)
            ay = 2.0 * np.sin(0.5 * self.time)
        elif state.maneuver_type == "evasive":
            # Random jinks
            if int(self.time * 2) % 5 == 0:
                ax += np.random.uniform(-5, 5)
                ay += np.random.uniform(-5, 5)
        
        # Update Position: p = p0 + v0*t + 0.5*a*t^2
        new_px = state.pos_x + state.vel_x * self.dt + 0.5 * ax * (self.dt**2)
        new_py = state.pos_y + state.vel_y * self.dt + 0.5 * ay * (self.dt**2)
        
        # Update Velocity: v = v0 + a*t
        new_vx = state.vel_x + ax * self.dt
        new_vy = state.vel_y + ay * self.dt
        
        return TargetState(
            id=state.id,
            pos_x=new_px,
            pos_y=new_py,
            vel_x=new_vx,
            vel_y=new_vy,
            acc_x=ax,
            acc_y=ay,
            type=state.type,
            maneuver_type=state.maneuver_type
        )

def simulate_trajectory(initial_state: TargetState, duration_s: float, dt: float) -> list[TargetState]:
    """
    Generates a full trajectory over a specified duration.
    """
    engine = KinematicEngine(dt)
    trajectory = [initial_state]
    current_state = initial_state
    
    n_steps = int(duration_s / dt)
    for _ in range(n_steps):
        current_state = engine.update_state(current_state)
        trajectory.append(current_state)
        
    return trajectory
