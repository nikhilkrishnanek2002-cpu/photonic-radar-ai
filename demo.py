#!/usr/bin/env python3
"""
PHOENIX-RADAR: Full System Demonstration
==========================================

Demonstrates the complete Photonic Radar AI system including:
1. Synthetic radar environment generation
2. Target and noise simulation
3. Signal processing detection pipeline
4. Tracking with Kalman filtering
5. Cognitive intelligence decision layer
6. Event bus publishing
7. Real-time console output

Usage:
    python demo.py                  # Basic demo
    python demo.py --verbose        # With debug output
    python demo.py --duration 30    # Run for 30 seconds

No external services or hardware required - fully synthetic.
"""

import sys
import logging
import time
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from collections import deque

# Setup Python path
PROJECT_ROOT = Path(__file__).parent
PHOTONIC_CORE = PROJECT_ROOT / "photonic-radar-ai"

# Standardize Python path: add photonic-radar-ai directory for all imports
if str(PHOTONIC_CORE) not in sys.path:
    sys.path.insert(0, str(PHOTONIC_CORE))

# =============================================================================
# CONSOLE FORMATTING & UTILITIES
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_detection(detection: Dict[str, Any], frame: int):
    """Print formatted detection."""
    track_id = detection.get('id', detection.get('track_id', '?'))
    range_m = detection.get('range_m', 0)
    azimuth = detection.get('azimuth_deg', 0)
    velocity = detection.get('radial_velocity_m_s', 0)
    snr = detection.get('snr_db', 0)
    quality = detection.get('track_quality', 0)
    
    print(f"{Colors.OKCYAN}[DETECTION] Frame {frame:5d} | "
          f"Track #{track_id:2} | "
          f"Range: {range_m:7.1f}m | "
          f"Azimuth: {azimuth:6.1f}° | "
          f"Velocity: {velocity:7.1f}m/s | "
          f"SNR: {snr:6.1f}dB | "
          f"Quality: {quality:.2f}{Colors.ENDC}")

def print_threat(threat: Dict[str, Any], frame: int):
    """Print formatted threat assessment."""
    track_id = threat.get('track_id', threat.get('id', '?'))
    threat_class = threat.get('threat_class', 'UNKNOWN')
    priority = threat.get('threat_priority', 0)
    confidence = threat.get('classification_confidence', 0)
    recommendation = threat.get('engagement_recommendation', 'MONITOR')
    
    # Color based on threat level
    if threat_class == 'HOSTILE':
        color = Colors.FAIL
    elif threat_class == 'UNKNOWN':
        color = Colors.WARNING
    elif threat_class == 'NEUTRAL':
        color = Colors.OKGREEN
    else:
        color = Colors.OKBLUE
    
    print(f"{color}[THREAT] Frame {frame:5d} | "
          f"Track #{track_id:2} | "
          f"Class: {threat_class:8} | "
          f"Priority: {priority:2}/10 | "
          f"Confidence: {confidence:.1%} | "
          f"Action: {recommendation}{Colors.ENDC}")

def print_ew_decision(decision: Dict[str, Any], frame: int):
    """Print formatted EW decision."""
    decision_count = decision.get('decision_count', 0)
    jamming = decision.get('active_jamming', False)
    status = "ENGAGING" if jamming else "SCANNING"
    status_color = Colors.FAIL if jamming else Colors.OKGREEN
    
    print(f"{status_color}[EW DECISION] Frame {frame:5d} | "
          f"Decision #{decision_count} | "
          f"Status: {status}{Colors.ENDC}")

def print_summary(tick: int, radar_stats: Dict, ew_stats: Dict):
    """Print frame summary statistics."""
    track_count = len(radar_stats.get('tracks', []))
    threat_count = len(radar_stats.get('threats', []))
    detections = radar_stats.get('detections', 0)
    ew_decisions = ew_stats.get('decision_count', 0)
    snr_avg = radar_stats.get('snr_avg', 0)
    
    print(f"{Colors.BOLD}[SUMMARY] Frame {tick:5d} | "
          f"Tracks: {track_count:2} | "
          f"Threats: {threat_count:2} | "
          f"Detections: {detections:3} | "
          f"EW Decisions: {ew_decisions:3} | "
          f"Avg SNR: {snr_avg:6.1f}dB{Colors.ENDC}")

# =============================================================================
# SETUP & INITIALIZATION
# =============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger(__name__)

def initialize_system(logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Initialize all system components.
    
    Returns:
        Dictionary with initialized components or None on failure
    """
    print_header("PHOENIX RADAR AI - SYSTEM INITIALIZATION")
    
    state = {
        'event_bus': None,
        'tactical_state': None,
        'radar': None,
        'ew': None,
        'running': False,
        'tick': 0
    }
    
    try:
        # Phase 1: Initialize Event Bus
        print(f"{Colors.OKGREEN}[EVENT BUS]{Colors.ENDC} Initializing... ", end='', flush=True)
        try:
            import defense_core
            defense_core.reset_defense_bus()
            event_bus = defense_core.get_defense_bus()
            state['event_bus'] = event_bus
            print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}✗ {e}{Colors.ENDC}")
            return None
        
        # Phase 2: Initialize Tactical State
        print(f"{Colors.OKGREEN}[TACTICAL STATE]{Colors.ENDC} Initializing... ", end='', flush=True)
        try:
            from subsystems.event_bus_subsystem import EventBusSubsystem
            # Create minimal tactical state
            state['tactical_state'] = type('TacticalState', (), {
                'event_bus': event_bus,
                'radar': {},
                'ew': {},
                'update_radar': lambda *args, **kw: None,
                'update_ew': lambda *args, **kw: None,
            })()
            print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}✗ {e}{Colors.ENDC}")
            return None
        
        # Phase 3: Initialize Radar Subsystem
        print(f"{Colors.OKGREEN}[RADAR SUBSYSTEM]{Colors.ENDC} Initializing... ", end='', flush=True)
        try:
            from subsystems import RadarSubsystem
            from simulation_engine.physics import TargetState
            
            # Create synthetic target scenario
            targets = [
                TargetState(
                    id=1, pos_x=1200.0, pos_y=800.0,
                    vel_x=-35.0, vel_y=-15.0, type="hostile"
                ),
                TargetState(
                    id=2, pos_x=1800.0, pos_y=-500.0,
                    vel_x=-45.0, vel_y=10.0, type="neutral"
                ),
                TargetState(
                    id=3, pos_x=900.0, pos_y=300.0,
                    vel_x=-28.0, vel_y=-20.0, type="civilian"
                ),
            ]
            
            radar_config = {
                'sensor_id': 'PHOENIX_DEMO_RADAR',
                'frame_dt': 0.1,  # 10 Hz
                'rpm': 60,
                'scan_angle_deg': 120,
                'enable_defense_core': True,
                'enable_ew_effects': True
            }
            
            radar = RadarSubsystem(radar_config)
            radar.initialize(
                initial_targets=targets,
                event_bus=event_bus,
                tactical_state=state['tactical_state']
            )
            state['radar'] = radar
            print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
            logger.info(f"Radar initialized with {len(targets)} targets")
            
        except Exception as e:
            print(f"{Colors.FAIL}✗ {e}{Colors.ENDC}")
            logger.error(f"Radar initialization failed: {e}", exc_info=True)
            return None
        
        # Phase 4: Initialize EW Subsystem
        print(f"{Colors.OKGREEN}[EW SUBSYSTEM]{Colors.ENDC} Initializing... ", end='', flush=True)
        try:
            from subsystems import EWSubsystem
            
            ew_config = {
                'effector_id': 'PHOENIX_DEMO_EW',
                'enable_ingestion': True,
                'ingestion_mode': 'event_bus',
                'log_all_updates': False
            }
            
            ew = EWSubsystem(ew_config)
            ew.initialize(tactical_state=state['tactical_state'])
            state['ew'] = ew
            print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
            logger.info("EW subsystem initialized")
            
        except Exception as e:
            print(f"{Colors.WARNING}⚠ {e}{Colors.ENDC} (continuing without EW)")
            logger.warning(f"EW initialization failed: {e}")
            state['ew'] = None
        
        state['running'] = True
        return state
        
    except Exception as e:
        logger.error(f"System initialization failed: {e}", exc_info=True)
        return None

# =============================================================================
# MAIN SIMULATION LOOP
# =============================================================================

def run_demo(state: Dict[str, Any], duration: float, logger: logging.Logger):
    """
    Run the demonstration.
    
    Args:
        state: Initialized system state
        duration: Runtime in seconds
        logger: Logger instance
    """
    print_header("RADAR DEMONSTRATION - RUNNING")
    
    print(f"{Colors.BOLD}Running for {duration} seconds ({int(duration*10)} frames at 10 Hz)...{Colors.ENDC}\n")
    
    frame_count = 0
    detections_total = 0
    threats_total = 0
    start_time = time.time()
    frame_times = deque(maxlen=100)
    
    try:
        while state['running']:
            frame_start = time.time()
            state['tick'] += 1
            
            # RADAR FRAME
            if state['radar']:
                radar_result = state['radar'].tick()
                
                if 'error' not in radar_result:
                    tracks = radar_result.get('tracks', [])
                    threats = radar_result.get('threats', [])
                    
                    # Print detections
                    for track in tracks:
                        print_detection(track, state['tick'])
                        detections_total += 1
                    
                    # Print threats
                    for threat in threats:
                        print_threat(threat, state['tick'])
                        threats_total += 1
            
            # EW DECISION
            if state['ew']:
                ew_result = state['ew'].tick()
                
                if ew_result and 'error' not in ew_result:
                    if ew_result.get('decision_count', 0) > 0:
                        print_ew_decision(ew_result, state['tick'])
            
            # Print summary every 10 frames
            if state['radar'] and state['tick'] % 10 == 0:
                radar_stats = state['radar'].get_stats() if hasattr(state['radar'], 'get_stats') else {}
                ew_stats = state['ew'].get_stats() if state['ew'] and hasattr(state['ew'], 'get_stats') else {}
                print_summary(state['tick'], radar_stats, ew_stats)
                print()  # Blank line for readability
            
            frame_count += 1
            
            # Timing
            frame_time = time.time() - frame_start
            frame_times.append(frame_time)
            
            # Check duration
            if time.time() - start_time > duration:
                state['running'] = False
                break
            
            # Sleep to maintain 10 Hz
            sleep_time = 0.1 - frame_time
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Print final statistics
        elapsed = time.time() - start_time
        avg_frame_time = sum(frame_times) / len(frame_times) * 1000  # Convert to ms
        
        print_header("DEMONSTRATION COMPLETE")
        
        print(f"{Colors.BOLD}Statistics:{Colors.ENDC}")
        print(f"  Total frames: {frame_count}")
        print(f"  Total detections: {detections_total}")
        print(f"  Total threats: {threats_total}")
        print(f"  Elapsed time: {elapsed:.1f}s")
        print(f"  Avg frame time: {avg_frame_time:.2f}ms")
        print(f"  Nominal frame rate: 10 Hz (100ms/frame)")
        print(f"  Utilization: {(avg_frame_time/100)*100:.1f}%")
        print()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Interrupted by user{Colors.ENDC}")
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
    finally:
        state['running'] = False

# =============================================================================
# EVENT BUS MONITORING
# =============================================================================

def print_event_bus_summary(state: Dict[str, Any], logger: logging.Logger):
    """Print event bus status."""
    if not state.get('event_bus'):
        return
    
    bus = state['event_bus']
    
    print_header("EVENT BUS SUMMARY")
    
    # Get queue info
    try:
        q_info = bus.get_queue_info() if hasattr(bus, 'get_queue_info') else {}
        print(f"{Colors.BOLD}Message Queues:{Colors.ENDC}")
        for queue_name, queue_data in q_info.items():
            size = queue_data.get('size', 0) if isinstance(queue_data, dict) else queue_data
            print(f"  {queue_name:30} | Messages: {size:5}")
    except Exception as e:
        logger.debug(f"Could not get queue info: {e}")
    
    print()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='PHOENIX Radar AI System Demonstration',
        epilog='Example: python demo.py --duration 30 --verbose'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=20.0,
        help='Duration to run in seconds (default: 20)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug output'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Print banner
    print(f"""\n
{Colors.HEADER}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════════╗
║                  PHOENIX RADAR AI DEMONSTRATION                   ║
║          Cognitive Photonic Radar with AI Intelligence            ║
║                  No Hardware or Services Required                  ║
╚═══════════════════════════════════════════════════════════════════╝
{Colors.ENDC}
{Colors.BOLD}System Components:{Colors.ENDC}
  • Event Bus (Defense Core): Real-time messaging
  • Radar Subsystem: Physics-based signal processing
  • Signal Processing: Detection & Kalman filtering
  • Cognitive Engine: AI-based threat classification
  • EW Subsystem: Electronic warfare decisions
  
{Colors.BOLD}Synthetic Scenario:{Colors.ENDC}
  • 3 target aircraft simulated
  • Realistic Doppler effects and noise
  • Adaptive detection thresholds (CFAR)
  • Closed-loop cognitive adaptation
    
""")
    
    # Initialize system
    state = initialize_system(logger)
    if not state:
        print(f"{Colors.FAIL}✗ System initialization failed{Colors.ENDC}")
        return 1
    
    print(f"\n{Colors.BOLD}✓ All systems initialized and ready{Colors.ENDC}\n")
    
    # Run demonstration
    try:
        run_demo(state, args.duration, logger)
    except Exception as e:
        logger.error(f"Demonstration failed: {e}", exc_info=True)
        print(f"{Colors.FAIL}✗ Demonstration failed: {e}{Colors.ENDC}")
        return 1
    finally:
        # Print event bus summary
        try:
            print_event_bus_summary(state, logger)
        except Exception as e:
            logger.debug(f"Could not print event bus summary: {e}")
    
    print(f"{Colors.OKGREEN}✓ Demonstration complete{Colors.ENDC}\n")
    return 0

if __name__ == '__main__':
    sys.exit(main())
