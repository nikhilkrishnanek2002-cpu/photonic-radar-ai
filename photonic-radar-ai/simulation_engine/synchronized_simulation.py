"""
Synchronized Radar-EW Closed-Loop Simulation
============================================

Integrates radar and EW systems with:
- Shared simulation clock
- Deterministic execution
- No deadlocks (non-blocking operations)
- Comprehensive cycle logging

Author: Closed-Loop Simulation Team
"""

import logging
import time
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path

from simulation_engine.orchestrator import SimulationOrchestrator
from simulation_engine.physics import TargetState
from cognitive.intelligence_pipeline import EWIntelligencePipeline
from defense_core import get_defense_bus, reset_defense_bus

logger = logging.getLogger(__name__)


class SynchronizedRadarEWSimulation:
    """
    Synchronized closed-loop simulation of radar and EW systems.
    
    Features:
    - Shared simulation clock (no threads, deterministic)
    - Non-blocking event bus operations (no deadlocks)
    - Comprehensive cycle logging
    - 1-frame latency (realistic EW response time)
    """
    
    def __init__(self,
                 radar_config: Dict,
                 ew_config: Dict,
                 targets: List[TargetState],
                 max_frames: int = 100,
                 enable_cycle_logging: bool = True,
                 log_every_n_frames: int = 1):
        """
        Initialize synchronized simulation.
        
        Args:
            radar_config: Radar configuration
            ew_config: EW configuration
            targets: Initial target list
            max_frames: Maximum frames to simulate
            enable_cycle_logging: Enable detailed cycle logging
            log_every_n_frames: Log cycle every N frames
        """
        self.time = 0.0
        self.dt = radar_config.get('frame_dt', 0.1)
        self.frame_count = 0
        self.max_frames = max_frames
        self.enable_cycle_logging = enable_cycle_logging
        self.log_every_n_frames = log_every_n_frames
        
        # Reset event bus for clean start
        reset_defense_bus()
        
        # Initialize radar system
        logger.info("Initializing radar system...")
        self.radar = SimulationOrchestrator(radar_config, targets)
        
        # Initialize EW system
        logger.info("Initializing EW system...")
        self.ew_pipeline = EWIntelligencePipeline(
            enable_ingestion=ew_config.get('enable_ingestion', True),
            ingestion_mode=ew_config.get('ingestion_mode', 'event_bus'),
            log_all_updates=ew_config.get('log_all_updates', True)
        )
        self.ew_pipeline.start()
        
        # Get shared event bus
        self.defense_bus = get_defense_bus()
        
        # Statistics
        self.cycle_stats = {
            'total_detections': 0,
            'total_tracks': 0,
            'total_intel_packets': 0,
            'total_ew_decisions': 0,
            'total_jam_packets': 0,
            'total_radar_responses': 0
        }
        
        logger.info(f"Synchronized simulation initialized: dt={self.dt}s, max_frames={max_frames}")
    
    def tick(self) -> Dict[str, Any]:
        """
        Execute one synchronized simulation tick.
        
        Order:
        1. Radar tick (detect, track, publish intelligence, apply EW effects)
        2. EW processing (happens in background thread)
        3. Log complete cycle
        
        Returns:
            Tick results
        """
        tick_start = time.time()
        
        # === STEP 1: RADAR DETECT & PUBLISH ===
        radar_result = self.radar.tick()
        
        # Extract radar metrics
        num_detections = len(radar_result.get('detections', []))
        tracks = radar_result.get('tracks', [])
        num_tracks = len(tracks)
        
        # Count threats
        num_threats = sum(1 for t in tracks if t.get('class_label') in ['Missile', 'Aircraft', 'Drone'])
        
        # Update stats
        self.cycle_stats['total_detections'] += num_detections
        self.cycle_stats['total_tracks'] += num_tracks
        
        # Intelligence packet was published by radar (if defense_core enabled)
        if self.radar.enable_defense_core and self.radar.packets_sent > 0:
            self.cycle_stats['total_intel_packets'] += 1
        
        # === STEP 2: EW DECISION (Background) ===
        # EW pipeline processes intelligence in background thread
        # We can check its statistics
        ew_stats = self.ew_pipeline.get_statistics()
        ew_messages_processed = ew_stats.get('messages_processed', 0)
        
        # Check if EW published attack packet
        ew_publisher_stats = {}
        if hasattr(self.ew_pipeline, 'feedback_publisher'):
            ew_publisher_stats = self.ew_pipeline.feedback_publisher.get_statistics()
            ew_packets_sent = ew_publisher_stats.get('packets_sent', 0)
            if ew_packets_sent > self.cycle_stats['total_jam_packets']:
                self.cycle_stats['total_jam_packets'] = ew_packets_sent
        
        # === STEP 3: RADAR RESPONSE ===
        # Check if radar applied EW effects
        radar_response = {}
        if self.radar.enable_ew_effects and self.radar.ew_degradation:
            metrics = self.radar.ew_degradation.get_metrics()
            radar_response = {
                'snr_reduction_db': metrics.snr_reduction_db,
                'tracks_degraded': metrics.tracks_degraded,
                'false_tracks_injected': metrics.false_tracks_injected,
                'range_drift_m': metrics.range_drift_m,
                'velocity_drift_m_s': metrics.velocity_drift_m_s
            }
            
            if metrics.tracks_degraded > 0 or metrics.false_tracks_injected > 0:
                self.cycle_stats['total_radar_responses'] += 1
        
        # === STEP 4: LOG CYCLE ===
        if self.enable_cycle_logging and (self.frame_count % self.log_every_n_frames == 0):
            self._log_cycle(
                num_detections=num_detections,
                num_tracks=num_tracks,
                num_threats=num_threats,
                ew_stats=ew_stats,
                ew_publisher_stats=ew_publisher_stats,
                radar_response=radar_response
            )
        
        # Update time
        self.time += self.dt
        self.frame_count += 1
        
        tick_time = time.time() - tick_start
        
        return {
            'frame_count': self.frame_count,
            'time': self.time,
            'num_detections': num_detections,
            'num_tracks': num_tracks,
            'num_threats': num_threats,
            'tick_time_ms': tick_time * 1000
        }
    
    def _log_cycle(self,
                   num_detections: int,
                   num_tracks: int,
                   num_threats: int,
                   ew_stats: Dict,
                   ew_publisher_stats: Dict,
                   radar_response: Dict):
        """
        Log complete engagement cycle.
        
        Format:
        [CYCLE] Frame X @ T=Y.Ys
          [RADAR-DETECT] Detections=N, Tracks=M, Threats=K
          [INTEL-SENT] Packet published: M tracks, K threats
          [EW-DECISION] Messages processed=N, Adaptations made
          [JAM-SENT] Attack packets sent=N
          [RADAR-RESPONSE] SNR reduction=X dB, Tracks degraded=Y, False tracks=Z
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"[CYCLE] Frame {self.frame_count} @ T={self.time:.1f}s")
        logger.info(f"{'='*80}")
        
        # RADAR DETECT
        logger.info(f"  [RADAR-DETECT] Detections={num_detections}, "
                   f"Tracks={num_tracks}, Threats={num_threats}")
        
        # INTEL SENT
        if self.radar.enable_defense_core:
            logger.info(f"  [INTEL-SENT] Packet published: {num_tracks} tracks, "
                       f"{num_threats} threats")
        else:
            logger.info(f"  [INTEL-SENT] Event bus disabled")
        
        # EW DECISION
        messages_processed = ew_stats.get('messages_processed', 0)
        if messages_processed > 0:
            logger.info(f"  [EW-DECISION] Messages processed={messages_processed}, "
                       f"Intelligence received")
        else:
            logger.info(f"  [EW-DECISION] No intelligence received")
        
        # JAM SENT
        packets_sent = ew_publisher_stats.get('packets_sent', 0)
        packets_dropped = ew_publisher_stats.get('packets_dropped', 0)
        if packets_sent > 0:
            logger.info(f"  [JAM-SENT] Attack packets sent={packets_sent}, "
                       f"dropped={packets_dropped}")
        else:
            logger.info(f"  [JAM-SENT] No attack packets (no threats)")
        
        # RADAR RESPONSE
        if radar_response:
            snr_red = radar_response.get('snr_reduction_db', 0)
            tracks_deg = radar_response.get('tracks_degraded', 0)
            false_tracks = radar_response.get('false_tracks_injected', 0)
            range_drift = radar_response.get('range_drift_m', 0)
            vel_drift = radar_response.get('velocity_drift_m_s', 0)
            
            if snr_red > 0 or tracks_deg > 0 or false_tracks > 0:
                logger.info(f"  [RADAR-RESPONSE] SNR reduction={snr_red:.1f}dB, "
                           f"Tracks degraded={tracks_deg}, False tracks={false_tracks}, "
                           f"Range drift={range_drift:.1f}m, Velocity drift={vel_drift:.1f}m/s")
            else:
                logger.info(f"  [RADAR-RESPONSE] No jamming effects applied")
        else:
            logger.info(f"  [RADAR-RESPONSE] EW effects disabled")
        
        logger.info(f"{'='*80}\n")
    
    def run(self, num_frames: Optional[int] = None) -> Dict[str, Any]:
        """
        Run simulation for specified number of frames.
        
        Args:
            num_frames: Number of frames (default: max_frames)
            
        Returns:
            Simulation summary
        """
        if num_frames is None:
            num_frames = self.max_frames
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STARTING SYNCHRONIZED RADAR-EW SIMULATION")
        logger.info(f"{'='*80}")
        logger.info(f"Frames: {num_frames}, dt={self.dt}s, Duration={num_frames * self.dt:.1f}s")
        logger.info(f"{'='*80}\n")
        
        start_time = time.time()
        tick_times = []
        
        for i in range(num_frames):
            result = self.tick()
            tick_times.append(result['tick_time_ms'])
            
            # Progress logging
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{num_frames} frames "
                           f"(avg tick time: {np.mean(tick_times):.2f}ms)")
        
        elapsed_time = time.time() - start_time
        
        # Generate summary
        summary = {
            'frames_simulated': num_frames,
            'simulation_duration_s': self.time,
            'wall_clock_time_s': elapsed_time,
            'real_time_factor': self.time / elapsed_time if elapsed_time > 0 else 0,
            'mean_tick_time_ms': np.mean(tick_times) if tick_times else 0,
            'max_tick_time_ms': np.max(tick_times) if tick_times else 0,
            'cycle_stats': self.cycle_stats,
            'radar_stats': {
                'packets_sent': self.radar.packets_sent,
                'packets_dropped': self.radar.packets_dropped
            },
            'ew_stats': self.ew_pipeline.get_statistics()
        }
        
        logger.info(f"\n{'='*80}")
        logger.info(f"SIMULATION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Frames: {num_frames}, Duration: {self.time:.1f}s")
        logger.info(f"Wall clock: {elapsed_time:.2f}s, RTF: {summary['real_time_factor']:.2f}x")
        logger.info(f"Mean tick time: {summary['mean_tick_time_ms']:.2f}ms")
        logger.info(f"\nCycle Statistics:")
        logger.info(f"  Total detections: {self.cycle_stats['total_detections']}")
        logger.info(f"  Total tracks: {self.cycle_stats['total_tracks']}")
        logger.info(f"  Intel packets sent: {self.cycle_stats['total_intel_packets']}")
        logger.info(f"  EW decisions made: {summary['ew_stats'].get('messages_processed', 0)}")
        logger.info(f"  Jam packets sent: {self.cycle_stats['total_jam_packets']}")
        logger.info(f"  Radar responses: {self.cycle_stats['total_radar_responses']}")
        logger.info(f"{'='*80}\n")
        
        return summary
    
    def stop(self):
        """Stop simulation and cleanup."""
        logger.info("Stopping synchronized simulation...")
        
        # Stop EW pipeline
        self.ew_pipeline.stop()
        
        # Stop radar
        self.radar.stop()
        
        logger.info("Synchronized simulation stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current simulation statistics."""
        return {
            'frame_count': self.frame_count,
            'time': self.time,
            'cycle_stats': self.cycle_stats,
            'radar_stats': {
                'packets_sent': self.radar.packets_sent,
                'packets_dropped': self.radar.packets_dropped
            },
            'ew_stats': self.ew_pipeline.get_statistics()
        }


def create_test_scenario(scenario: str = 'single_hostile') -> tuple:
    """
    Create test scenario configurations.
    
    Args:
        scenario: Scenario name
        
    Returns:
        (radar_config, ew_config, targets)
    """
    # Base radar config
    radar_config = {
        'sensor_id': 'SYNC_RADAR_01',
        'frame_dt': 0.1,
        'enable_defense_core': True,
        'enable_ew_effects': True,
        'ew_log_before_after': True,
        'ew_max_snr_degradation_db': 20.0,
        'ew_max_quality_degradation': 0.5,
        'ew_false_track_probability': 0.3,
        'enable_intelligence_export': False,
        'debug_packets': False
    }
    
    # Base EW config
    ew_config = {
        'effector_id': 'SYNC_EW_01',
        'enable_ingestion': True,
        'ingestion_mode': 'event_bus',
        'log_all_updates': True
    }
    
    # Create targets based on scenario
    if scenario == 'single_hostile':
        targets = [
            TargetState(
                id=1,
                pos_x=1000.0,  # 1000m range
                pos_y=0.0,
                vel_x=-50.0,   # Approaching at 50 m/s
                vel_y=0.0,
                type="hostile"
            )
        ]
    elif scenario == 'multiple_targets':
        targets = [
            TargetState(id=1, pos_x=1000.0, pos_y=0.0, vel_x=-50.0, vel_y=0.0, type="hostile"),
            TargetState(id=2, pos_x=1500.0, pos_y=200.0, vel_x=-30.0, vel_y=0.0, type="hostile"),
            TargetState(id=3, pos_x=800.0, pos_y=-100.0, vel_x=-60.0, vel_y=0.0, type="civilian")
        ]
    else:
        targets = []
    
    return radar_config, ew_config, targets


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create test scenario
    radar_config, ew_config, targets = create_test_scenario('single_hostile')
    
    # Create simulation
    sim = SynchronizedRadarEWSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        max_frames=50,
        enable_cycle_logging=True,
        log_every_n_frames=5  # Log every 5 frames
    )
    
    try:
        # Run simulation
        summary = sim.run(num_frames=50)
        
        print("\n" + "="*80)
        print("FINAL SUMMARY")
        print("="*80)
        print(f"Real-time factor: {summary['real_time_factor']:.2f}x")
        print(f"Mean tick time: {summary['mean_tick_time_ms']:.2f}ms")
        print(f"Radar packets sent: {summary['radar_stats']['packets_sent']}")
        print(f"EW messages processed: {summary['ew_stats'].get('messages_processed', 0)}")
        print("="*80)
        
    finally:
        # Cleanup
        sim.stop()
