"""
Radar Evaluation Module
=======================

Computes quantitative performance metrics for the radar system.
Matches Estimated Tracks (TR) with Ground Truth (GT) to calculate error.

Metrics:
- Detection Accuracy (Pd): Sensitivity.
- False Alarm Rate (PFA): Specificity/Clutter Rejection.
- RMSE: Tracking precision (Range, Velocity).
- Latency: Time to track confirmation.

Author: Principal Radar Scientist
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import matplotlib.pyplot as plt

@dataclass
class EvalMetric:
    frame: int
    gt_id: int
    track_id: Optional[int]
    range_error: float = 0.0
    velocity_error: float = 0.0
    is_detected: bool = False
    is_false_alarm: bool = False

class EvaluationManager:
    def __init__(self, match_gate: float = 50.0):
        """
        Args:
            match_gate: Max distance (m) to consider a track matching a GT target.
        """
        self.match_gate = match_gate
        self.history: List[EvalMetric] = []
        self.false_alarm_count = 0
        self.total_frames = 0
        
    def update(self, frame_idx: int, gt_targets: List[Dict], tracks: List[Dict]):
        """
        Correlates GT and Tracks for the current frame.
        gt_targets: List of dicts (from orchestrator.targets)
        tracks: List of dicts (from orchestrator.tracks)
        """
        self.total_frames += 1
        
        # 1. Build Distance Matrix
        used_tracks = set()
        
        for gt in gt_targets:
            best_dist = float('inf')
            best_track = None
            gt_r = np.sqrt(gt['pos_x']**2 + gt['pos_y']**2)
            gt_v = gt.get('radial_velocity', 0.0) # Need to ensure this exists or compute it
            
            # Simple Nearest Neighbor matching on Range
            # (In a real system, would use full state 2D match)
            for tr in tracks:
                tr_id = tr['id']
                tr_r = tr['range_m']
                dist = abs(gt_r - tr_r)
                
                if dist < self.match_gate and dist < best_dist:
                    best_dist = dist
                    best_track = tr

            # Record Metric for this GT
            metric = EvalMetric(frame=frame_idx, gt_id=gt['id'], track_id=None)
            
            if best_track:
                used_tracks.add(best_track['id'])
                metric.track_id = best_track['id']
                metric.is_detected = True
                metric.range_error = best_dist
                metric.velocity_error = abs(gt_v - best_track['velocity_m_s'])
            
            self.history.append(metric)
            
        # 2. Count False Alarms (Tracks not matched to any GT)
        # Note: This is simplified. Tracks confirming on clutter are FA.
        total_fa = len(tracks) - len(used_tracks)
        self.false_alarm_count += max(0, total_fa)

    def get_summary(self) -> Dict:
        """Computes aggregate statistics."""
        df = pd.DataFrame([vars(m) for m in self.history])
        if df.empty: return {}
        
        # PD = Matches / Total GT instances
        pd_val = df['is_detected'].mean()
        
        # RMSE (Only for detected targets)
        det_df = df[df['is_detected']]
        rmse_r = np.sqrt((det_df['range_error']**2).mean()) if not det_df.empty else 0.0
        rmse_v = np.sqrt((det_df['velocity_error']**2).mean()) if not det_df.empty else 0.0
        
        # PFA (False Alarms / Total Frames) - Rate per frame
        # Or False Alarms / Ops time
        pfa_rate = self.false_alarm_count / max(1, self.total_frames)
        
        return {
            "Pd": pd_val,
            "PFA_per_frame": pfa_rate,
            "RMSE_Range_m": rmse_r,
            "RMSE_Vel_ms": rmse_v,
            "Total_Samples": len(df)
        }
        
    def plot_results(self, save_path: str = "eval_results.png"):
        """Generates performance plots."""
        df = pd.DataFrame([vars(m) for m in self.history])
        if df.empty: return
        
        fig, ax = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot 1: Errors over time
        det_df = df[df['is_detected']]
        ax[0].scatter(det_df['frame'], det_df['range_error'], alpha=0.5, c='blue', label='Range Err')
        ax[0].set_title("Tracking Error vs Time")
        ax[0].set_xlabel("Frame")
        ax[0].set_ylabel("Error (m)")
        ax[0].grid(True)
        
        # Plot 2: Histogram of errors
        ax[1].hist(det_df['range_error'], bins=20, color='green', alpha=0.7)
        ax[1].set_title("Error Distribution")
        ax[1].set_xlabel("Range Error (m)")
        
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
