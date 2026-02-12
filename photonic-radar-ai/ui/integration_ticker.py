"""
Real-Time Integration Ticker
=============================

Visual ticker showing radar-EW integration cycle status in real-time.

Displays: RADAR → INTEL → EW → JAM → EFFECT

Updates every simulation tick with visual indicators.

Author: Integration UI Team
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class StageStatus(Enum):
    """Status of each integration stage."""
    IDLE = "IDLE"           # Not active
    ACTIVE = "ACTIVE"       # Currently processing
    SUCCESS = "SUCCESS"     # Completed successfully
    FAILED = "FAILED"       # Failed
    WAITING = "WAITING"     # Waiting for input


@dataclass
class IntegrationTickerState:
    """State of the integration ticker."""
    frame_id: int = 0
    
    # Stage statuses
    radar_status: StageStatus = StageStatus.IDLE
    intel_status: StageStatus = StageStatus.IDLE
    ew_status: StageStatus = StageStatus.IDLE
    jam_status: StageStatus = StageStatus.IDLE
    effect_status: StageStatus = StageStatus.IDLE
    
    # Stage metrics
    num_detections: int = 0
    num_tracks: int = 0
    num_threats: int = 0
    num_decisions: int = 0
    num_countermeasures: int = 0
    num_effects: int = 0
    
    # Timing
    last_update_time: float = 0.0
    cycle_latency_ms: float = 0.0


class IntegrationTicker:
    """
    Real-time integration ticker for radar-EW cycle visualization.
    
    Shows: RADAR → INTEL → EW → JAM → EFFECT
    
    Updates every tick with visual status indicators.
    """
    
    def __init__(self):
        """Initialize ticker."""
        self.state = IntegrationTickerState()
        self.cycle_start_time = None
        
        # Colors for terminal output
        self.RESET = "\033[0m"
        self.BOLD = "\033[1m"
        self.DIM = "\033[2m"
        
        # Status colors
        self.IDLE = "\033[90m"      # Gray
        self.ACTIVE = "\033[96m"    # Cyan
        self.SUCCESS = "\033[92m"   # Green
        self.FAILED = "\033[91m"    # Red
        self.WAITING = "\033[93m"   # Yellow
    
    def start_cycle(self, frame_id: int):
        """Start a new integration cycle."""
        self.state.frame_id = frame_id
        self.cycle_start_time = time.time()
        
        # Reset all stages to idle
        self.state.radar_status = StageStatus.IDLE
        self.state.intel_status = StageStatus.IDLE
        self.state.ew_status = StageStatus.IDLE
        self.state.jam_status = StageStatus.IDLE
        self.state.effect_status = StageStatus.IDLE
    
    def update_radar(self, num_detections: int, num_tracks: int):
        """Update radar stage."""
        self.state.radar_status = StageStatus.ACTIVE if num_tracks > 0 else StageStatus.IDLE
        self.state.num_detections = num_detections
        self.state.num_tracks = num_tracks
    
    def update_intel(self, num_threats: int, sent: bool):
        """Update intelligence stage."""
        self.state.num_threats = num_threats
        if sent:
            self.state.intel_status = StageStatus.SUCCESS if num_threats > 0 else StageStatus.IDLE
        else:
            self.state.intel_status = StageStatus.FAILED if num_threats > 0 else StageStatus.IDLE
    
    def update_ew(self, num_decisions: int, processed: bool):
        """Update EW stage."""
        self.state.num_decisions = num_decisions
        if processed:
            self.state.ew_status = StageStatus.SUCCESS if num_decisions > 0 else StageStatus.WAITING
        else:
            self.state.ew_status = StageStatus.IDLE
    
    def update_jam(self, num_countermeasures: int, active: bool):
        """Update jamming stage."""
        self.state.num_countermeasures = num_countermeasures
        if active:
            self.state.jam_status = StageStatus.ACTIVE if num_countermeasures > 0 else StageStatus.IDLE
        else:
            self.state.jam_status = StageStatus.IDLE
    
    def update_effect(self, num_effects: int, applied: bool):
        """Update effect stage."""
        self.state.num_effects = num_effects
        if applied:
            self.state.effect_status = StageStatus.SUCCESS if num_effects > 0 else StageStatus.IDLE
        else:
            self.state.effect_status = StageStatus.IDLE
    
    def end_cycle(self):
        """End the current cycle and calculate latency."""
        if self.cycle_start_time:
            self.state.cycle_latency_ms = (time.time() - self.cycle_start_time) * 1000
            self.state.last_update_time = time.time()
    
    def get_status_color(self, status: StageStatus) -> str:
        """Get color for status."""
        color_map = {
            StageStatus.IDLE: self.IDLE,
            StageStatus.ACTIVE: self.ACTIVE,
            StageStatus.SUCCESS: self.SUCCESS,
            StageStatus.FAILED: self.FAILED,
            StageStatus.WAITING: self.WAITING
        }
        return color_map.get(status, self.RESET)
    
    def get_status_icon(self, status: StageStatus) -> str:
        """Get icon for status."""
        icon_map = {
            StageStatus.IDLE: "○",
            StageStatus.ACTIVE: "●",
            StageStatus.SUCCESS: "✓",
            StageStatus.FAILED: "✗",
            StageStatus.WAITING: "⋯"
        }
        return icon_map.get(status, "?")
    
    def render_stage(self, name: str, status: StageStatus, metric: int) -> str:
        """Render a single stage."""
        color = self.get_status_color(status)
        icon = self.get_status_icon(status)
        
        # Format: NAME[icon:metric]
        return f"{color}{name}[{icon}:{metric}]{self.RESET}"
    
    def render_ticker(self) -> str:
        """Render the complete ticker."""
        # Render each stage
        radar = self.render_stage("RADAR", self.state.radar_status, self.state.num_tracks)
        intel = self.render_stage("INTEL", self.state.intel_status, self.state.num_threats)
        ew = self.render_stage("EW", self.state.ew_status, self.state.num_decisions)
        jam = self.render_stage("JAM", self.state.jam_status, self.state.num_countermeasures)
        effect = self.render_stage("EFFECT", self.state.effect_status, self.state.num_effects)
        
        # Arrow separator
        arrow = f"{self.DIM} → {self.RESET}"
        
        # Build ticker line
        ticker = f"{radar}{arrow}{intel}{arrow}{ew}{arrow}{jam}{arrow}{effect}"
        
        # Add frame and latency info
        info = f"{self.DIM}[Frame {self.state.frame_id} | {self.state.cycle_latency_ms:.1f}ms]{self.RESET}"
        
        return f"{info} {ticker}"
    
    def print_ticker(self):
        """Print the ticker to console."""
        print(self.render_ticker())
    
    def get_state_dict(self) -> Dict[str, Any]:
        """Get state as dictionary for UI integration."""
        return {
            'frame_id': self.state.frame_id,
            'stages': {
                'radar': {
                    'status': self.state.radar_status.value,
                    'metric': self.state.num_tracks,
                    'label': 'RADAR'
                },
                'intel': {
                    'status': self.state.intel_status.value,
                    'metric': self.state.num_threats,
                    'label': 'INTEL'
                },
                'ew': {
                    'status': self.state.ew_status.value,
                    'metric': self.state.num_decisions,
                    'label': 'EW'
                },
                'jam': {
                    'status': self.state.jam_status.value,
                    'metric': self.state.num_countermeasures,
                    'label': 'JAM'
                },
                'effect': {
                    'status': self.state.effect_status.value,
                    'metric': self.state.num_effects,
                    'label': 'EFFECT'
                }
            },
            'cycle_latency_ms': self.state.cycle_latency_ms,
            'last_update_time': self.state.last_update_time
        }


def demo_ticker():
    """Demonstrate the integration ticker."""
    import random
    
    print("\n" + "="*80)
    print("INTEGRATION TICKER DEMO")
    print("="*80 + "\n")
    
    ticker = IntegrationTicker()
    
    # Simulate 20 frames
    for frame in range(20):
        ticker.start_cycle(frame)
        
        # Simulate radar detection
        num_tracks = random.randint(0, 3)
        ticker.update_radar(num_tracks * 2, num_tracks)
        time.sleep(0.05)
        
        # Simulate intelligence export
        num_threats = min(num_tracks, random.randint(0, 2))
        ticker.update_intel(num_threats, num_threats > 0)
        time.sleep(0.05)
        
        # Simulate EW processing
        num_decisions = num_threats if random.random() > 0.2 else 0
        ticker.update_ew(num_decisions, num_threats > 0)
        time.sleep(0.05)
        
        # Simulate jamming
        num_cms = num_decisions if random.random() > 0.3 else 0
        ticker.update_jam(num_cms, num_cms > 0)
        time.sleep(0.05)
        
        # Simulate effects
        num_effects = num_cms if random.random() > 0.1 else 0
        ticker.update_effect(num_effects, num_cms > 0)
        
        ticker.end_cycle()
        ticker.print_ticker()
        
        time.sleep(0.2)
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80 + "\n")


if __name__ == '__main__':
    demo_ticker()
