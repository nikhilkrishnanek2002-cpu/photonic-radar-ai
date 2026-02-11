#!/usr/bin/env python3
"""
PHOENIX-RADAR Launcher
======================

Single entry point for the integrated defense simulation.

Architecture:
    main()
        ├── initialize()
        ├── start_subsystems()
        ├── run_simulation_loop()
        └── shutdown()

Usage:
    python3 launcher.py
"""

import sys
import os
import signal
import logging
import time
import subprocess
import threading
from typing import Optional, Dict, Any

# Silence TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Configure logging to console and file
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "system_launcher.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    force=True,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

# Unbuffered output for real-time log monitoring
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Import subsystems
from subsystems import EventBusSubsystem, RadarSubsystem, EWSubsystem
from simulation_engine.physics import TargetState
import numpy as np


# Simulation Clock
class SimulationClock:
    """
    Central simulation clock for synchronized execution.
    
    Handles fixed-rate ticking and drift correction.
    """
    def __init__(self, tick_rate_hz: float = 10.0):
        self.tick_rate = tick_rate_hz
        self.tick_interval = 1.0 / tick_rate_hz
        self.tick_count = 0
        self.start_time = None
        self.next_tick_time = None

    def start(self):
        """Start the clock."""
        self.start_time = time.perf_counter()
        self.next_tick_time = self.start_time + self.tick_interval
        self.tick_count = 0
        logger.info(f"[CLOCK] Simulation clock started at {self.tick_rate} Hz")

    def wait_for_next_tick(self) -> int:
        """
        Wait for the next tick, correcting for drift.
        
        Returns:
            Current tick count
        """
        if self.start_time is None:
            self.start()
            
        current_time = time.perf_counter()
        sleep_time = self.next_tick_time - current_time

        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            # We are running behind, don't sleep
            pass
        
        # Advance expected time for next tick (avoids drift accumulation)
        self.tick_count += 1
        self.next_tick_time = self.start_time + (self.tick_count + 1) * self.tick_interval
        
        return self.tick_count


# Global state
class LauncherState:
    """Global launcher state."""
    event_bus: Optional[EventBusSubsystem] = None
    radar: Optional[RadarSubsystem] = None
    ew: Optional[EWSubsystem] = None
    clock: Optional[SimulationClock] = None
    shutdown_requested: bool = False
    config: Dict[str, Any] = {}


state = LauncherState()


def signal_handler(signum, frame):
    """Handle keyboard interrupt safely."""
    logger.info(f"\n[SHUTDOWN] Signal {signum} received...")
    state.shutdown_requested = True


def initialize():
    """
    PHASE 1: Load configuration and setup.
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("")
    logger.info("="*70)
    logger.info(" COGNITIVE DEFENSE SYSTEM ONLINE")
    logger.info(" Sensor -> Intelligence -> EW -> Effect")
    logger.info("="*70)
    logger.info("")
    
    logger.info("[BOOT] Loading configuration...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--ui', action='store_true', help='Launch Tactical Dashboard (Streamlit)')
    args, _ = parser.parse_known_args()
    
    # Configuration
    state.config = {
        'debug': args.debug,
        'ui_enabled': args.ui,
        'radar': {
            'sensor_id': 'PHOENIX_RADAR_01',
            'frame_dt': 0.1,
            'rpm': 60,
            'scan_angle_deg': 120,
            'enable_defense_core': True,
            'enable_ew_effects': True,
            'ew_log_before_after': False,
            'debug_packets': False
        },
        'ew': {
            'effector_id': 'COGNITIVE_EW_01',
            'enable_ingestion': True,
            'ingestion_mode': 'event_bus',
            'log_all_updates': False
        },
        'scenario': {
            'targets': [
                TargetState(
                    id=1,
                    pos_x=1200.0,
                    pos_y=800.0,
                    vel_x=-35.0,
                    vel_y=-15.0,
                    type="hostile"
                ),
                TargetState(
                    id=2,
                    pos_x=1800.0,
                    pos_y=-500.0,
                    vel_x=-45.0,
                    vel_y=10.0,
                    type="civilian"
                ),
                TargetState(
                    id=3,
                    pos_x=900.0,
                    pos_y=300.0,
                    vel_x=-28.0,
                    vel_y=-20.0,
                    type="hostile"
                )
            ]
        },
        'simulation': {
            'max_frames': 1000,
            'frame_dt': 0.1
        }
    }
    
    logger.info("[BOOT] Configuration loaded")
    logger.info(f"       Targets: {len(state.config['scenario']['targets'])}")
    logger.info(f"       Max frames: {state.config['simulation']['max_frames']}")
    logger.info(f"       Frame rate: {1.0/state.config['simulation']['frame_dt']:.1f} Hz")
    logger.info("")
    
    return True


def start_subsystems():
    """
    PHASE 2-4: Boot all subsystems in strict order.
    
    Startup Order:
        1. defense_core (Event Bus)
        2. Radar thread/process
        3. EW thread/process
    
    Returns:
        True if all critical subsystems started, False otherwise
    """
    logger.info("="*70)
    logger.info("SUBSYSTEM STARTUP SEQUENCE")
    logger.info("="*70)
    logger.info("")
    
    # PHASE 2: Initialize defense_core (Event Bus) - CRITICAL
    logger.info("[BOOT] Initializing defense_core...")
    state.event_bus = EventBusSubsystem()
    if not state.event_bus.initialize():
        logger.error("[BOOT] ABORT: defense_core is required")
        return False
    logger.info("[BOOT] Event bus initialized")
    
    # PHASE 3: Start radar thread/process - CRITICAL
    logger.info("")
    logger.info("[BOOT] Starting radar thread/process...")
    state.radar = RadarSubsystem(state.config['radar'])
    if not state.radar.initialize(state.config['scenario']['targets'], event_bus=state.event_bus.bus):
        logger.error("[BOOT] ABORT: Radar is required")
        return False
    logger.info("[BOOT] Radar online")
    
    # PHASE 4: Start EW thread/process - OPTIONAL
    logger.info("")
    logger.info("[BOOT] Starting EW thread/process...")
    state.ew = EWSubsystem(state.config['ew'])
    if not state.ew.initialize():
        logger.warning("[BOOT] EW initialization failed - continuing in radar-only mode")
        state.ew = None
    else:
        logger.info("[BOOT] EW engine online")
    
    # PHASE 5: Start UI Server
    logger.info("")
    logger.info("[BOOT] Starting UI API Server...")
    try:
        from ui.server import start_server
        start_server(state)
        logger.info("[BOOT] UI Server online: http://localhost:5000")
    except Exception as e:
        logger.warning(f"[BOOT] UI Server failed to start: {e}")
    
    # Phase 6: Start Streamlit Dashboard (Always enabled)
    logger.info("")
    logger.info("[BOOT] Initializing Tactical Dashboard...")
    
    def launch_dashboard():
        """Launch Streamlit dashboard after API server is healthy."""
        import requests
        import webbrowser
        
        api_url = "http://localhost:5000/health"
        retries = 30  # 15 seconds max wait
        
        logger.info("[DASHBOARD] Waiting for API Server to become healthy...")
        while retries > 0:
            try:
                response = requests.get(api_url, timeout=0.5)
                if response.status_code == 200:
                    logger.info("[DASHBOARD] ✓ API Server is healthy")
                    break
            except:
                pass
            time.sleep(0.5)
            retries -= 1
        
        if retries <= 0:
            logger.warning("[DASHBOARD] ⚠ API Server health check timeout")
            logger.warning("[DASHBOARD] Launching dashboard anyway...")
        
        # Start Streamlit as subprocess
        try:
            subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "app.py",
                 "--server.port", "8501",
                 "--server.headless", "true"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            dashboard_url = "http://localhost:8501"
            logger.info("")
            logger.info("="*70)
            logger.info("✓ TACTICAL DASHBOARD LAUNCHED")
            logger.info(f"   URL: {dashboard_url}")
            logger.info("="*70)
            logger.info("")
            
            # Auto-open browser after brief delay
            time.sleep(2)
            logger.info("[DASHBOARD] Opening browser...")
            webbrowser.open(dashboard_url)
            
        except Exception as e:
            logger.error(f"[DASHBOARD] Failed to launch: {e}")
            logger.info("[DASHBOARD] You can manually start with: streamlit run app.py")

    # Run in daemon thread to not block simulation
    threading.Thread(target=launch_dashboard, daemon=True).start()


    logger.info("")
    logger.info("="*70)
    logger.info("[BOOT] ALL SUBSYSTEMS READY")
    logger.info("="*70)
    logger.info("")
    
    return True


def run_simulation_loop():
    """
    PHASE 5: Start threaded subsystems and monitor health.
    """
    logger.info("="*70)
    logger.info("STARTING SIMULATION")
    logger.info("="*70)
    logger.info("")
    
    # Start radar thread
    logger.info("[BOOT] Starting radar thread...")
    state.radar.start_thread()
    logger.info("[BOOT] Radar thread active")
    
    # Start EW thread
    if state.ew:
        logger.info("")
        logger.info("[BOOT] Starting EW thread...")
        state.ew.start_thread()
        logger.info("[BOOT] EW thread active")
    
    logger.info("")
    logger.info("[BOOT] Cognitive loop active")
    logger.info("")
    
    # Monitor threads
    logger.info("="*70)
    logger.info("THREAD MONITORING ACTIVE")
    logger.info("="*70)
    logger.info("")
    
    # Initialize clock
    state.clock = SimulationClock(tick_rate_hz=1.0/state.config['simulation']['frame_dt'])
    state.clock.start()
    
    try:
        max_frames = state.config['simulation']['max_frames']
        
        while state.clock.tick_count < max_frames:
            # Check for shutdown request
            if state.shutdown_requested:
                break
                
            # Wait for next tick
            tick = state.clock.wait_for_next_tick()
            
            # Log tick
            if tick % 10 == 0:
                logger.info(f"[TICK {tick:04d}]")
                
            # DEBUG LOGGING
            if state.config.get('debug', False):
                # Log queue sizes
                if state.event_bus:
                    q_sizes = state.event_bus.get_queue_sizes()
                    logger.info(f"[DEBUG] Frame {tick}: Queues={q_sizes}")
            
            # Health Monitoring & Recovery (Every 50 ticks / 5 seconds)
            if tick % 50 == 0:
                try:
                    # Check status
                    radar_ok = state.radar.is_thread_alive()
                    ew_ok = state.ew.is_thread_alive() if state.ew else False
                    bus_ok = state.event_bus is not None
                    
                    # Log status
                    logger.info(f"[RADAR] {'OK' if radar_ok else 'CRITICAL'}")
                    if state.ew:
                        logger.info(f"[EW] {'OK' if ew_ok else 'CRITICAL'}")
                    logger.info(f"[BUS] {'OK' if bus_ok else 'CRITICAL'}")
                    
                    # Report detailed stats
                    try:
                        radar_stats = state.radar.get_stats()
                        logger.info(f"[MONITOR] Frame {radar_stats['frame_count']}")
                        
                        if state.ew:
                            ew_stats = state.ew.get_stats()
                            logger.info(f"[MONITOR] EW: {ew_stats['intelligence_count']} intel, {ew_stats['decision_count']} decisions")
                    except Exception as stats_e:
                        logger.warning(f"[MONITOR] Failed to get stats: {stats_e}")

                    # RECOVERY LOGIC
                    
                    # 1. Radar Recovery (Critical)
                    if not radar_ok:
                        logger.error("[RADAR] CRASHED - Attempting restart...")
                        try:
                            state.radar.stop_thread() # Cleanup old thread
                            state.radar.start_thread() # Start new thread
                            
                            # Verify restart
                            time.sleep(0.5)
                            if state.radar.is_thread_alive():
                                logger.info("[RADAR] Restart successful")
                            else:
                                logger.critical("[RADAR] Restart failed. Aborting simulation.")
                                break
                        except Exception as e:
                            logger.critical(f"[RADAR] Recovery failed: {e}")
                            break
                    
                    # 2. EW Recovery (Optional)
                    if state.ew and not ew_ok:
                        logger.error("[EW] CRASHED - Attempting restart...")
                        try:
                            state.ew.stop_thread()
                            state.ew.start_thread()
                            
                            # Verify restart
                            time.sleep(0.5)
                            if state.ew.is_thread_alive():
                                logger.info("[EW] Restart successful")
                            else:
                                logger.warning("[EW] Restart failed. Disabling EW subsystem.")
                                state.ew = None
                        except Exception as e:
                            logger.error(f"[EW] Recovery error: {e}")
                            state.ew = None
                            
                except Exception as monitor_e:
                    logger.error(f"[MONITOR] Internal monitoring error: {monitor_e}")
                    # Do NOT break the loop, continue simulation

            
    except KeyboardInterrupt:
        logger.info("")
        logger.info("[MONITOR] Shutdown signal received")



def shutdown():
    """
    Gracefully shutdown all subsystems.
    """
    logger.info("")
    logger.info("="*70)
    logger.info("SHUTDOWN")
    logger.info("="*70)
    logger.info("")
    
    # Stop threads first (in reverse order)
    if state.ew:
        state.ew.stop_thread()
    
    if state.radar:
        state.radar.stop_thread()
    
    # Shutdown subsystems (in reverse order)
    if state.ew:
        state.ew.shutdown()
    
    if state.radar:
        state.radar.shutdown()
    
    if state.event_bus:
        state.event_bus.shutdown()
    
    logger.info("")
    logger.info("[SHUTDOWN] All systems offline.")


def main():
    """
    Main entry point.
    
    Flow:
        1. Initialize configuration
        2. Start subsystems
        3. Run simulation loop
        4. Shutdown
    """
    exit_code = 0
    
    try:
        # Initialize
        if not initialize():
            return 1
        
        # Start subsystems
        if not start_subsystems():
            shutdown()
            return 1
        
        # Run simulation loop
        run_simulation_loop()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    finally:
        # Always shutdown
        shutdown()
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())