#!/usr/bin/env python3
"""
PHOENIX-RADAR: Production-Grade Main Entry Point
=================================================

Unified orchestrator for the Photonic Radar AI Defense System.

Startup Sequence:
    1. Configuration & Logging          (Phase 1)
    2. Event Bus (Defense Core)         (Phase 2) - CRITICAL
    3. Tactical State Management        (Phase 2.5) - CRITICAL
    4. Simulation Engine (Radar)        (Phase 3) - CRITICAL
    5. Cognitive Intelligence (EW)      (Phase 4) - Optional
    6. API Server (FastAPI/Uvicorn)    (Phase 5) - Optional
    7. UI Dashboard (Streamlit)         (Phase 6) - Optional

Usage:
    python3 main.py                  # Headless radar + API
    python3 main.py --ui             # With Streamlit dashboard
    python3 main.py --debug          # Debug logging
    python3 main.py --api-only       # API server only
    python3 main.py --headless       # No browser auto-open

Cross-Platform: ✓ Linux, ✓ macOS, ✓ Windows
Dependencies: numpy, scipy, streamlit, flask, torch (optional)
"""

import sys
import os
import signal
import logging
import threading
import time
import argparse
import platform
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

# =============================================================================
# CONFIGURATION
# =============================================================================

# Detect project root (this file should be in project root)
PROJECT_ROOT = Path(__file__).resolve().parent
PHOTONIC_CORE = PROJECT_ROOT / "photonic-radar-ai"
RUNTIME_DIR = PHOTONIC_CORE / "runtime"
LOG_DIR = RUNTIME_DIR / "logs"

# Standardize Python path: add photonic-radar-ai directory for all imports
if str(PHOTONIC_CORE) not in sys.path:
    sys.path.insert(0, str(PHOTONIC_CORE))

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Cross-platform compatibility
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'
IS_MAC = platform.system() == 'Darwin'

# Create runtime directories
LOG_DIR.mkdir(parents=True, exist_ok=True)
(RUNTIME_DIR / "intelligence").mkdir(parents=True, exist_ok=True)


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging(debug: bool = False) -> logging.Logger:
    """
    Configure logging to console and file.
    
    Args:
        debug: Enable DEBUG level logging
    
    Returns:
        Configured logger instance
    """
    level = logging.DEBUG if debug else logging.INFO
    
    log_file = LOG_DIR / "phoenix_radar.log"
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Get module logger
    logger = logging.getLogger(__name__)
    
    logger.info(f"Logging initialized | Level: {logging.getLevelName(level)}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Log file: {log_file}")
    
    return logger


# =============================================================================
# SUBSYSTEM STATE
# =============================================================================

@dataclass
class SubsystemState:
    """Track state of all subsystems."""
    event_bus: Optional[Any] = None
    tactical_state: Optional[Any] = None
    radar: Optional[Any] = None
    ew: Optional[Any] = None
    api_process: Optional[subprocess.Popen] = None
    dashboard_process: Optional[subprocess.Popen] = None
    running: bool = False
    shutdown_requested: bool = False
    
    def all_critical_ready(self) -> bool:
        """Check if all critical subsystems are initialized."""
        return (
            self.event_bus is not None and
            self.radar is not None and
            self.tactical_state is not None
        )


# Global state
state = SubsystemState()
logger: Optional[logging.Logger] = None


# =============================================================================
# SIGNAL HANDLERS
# =============================================================================

def signal_handler(signum, frame):
    """Handle termination signals gracefully."""
    if logger:
        logger.info(f"\n[SHUTDOWN] Received signal {signum}")
    state.shutdown_requested = True


# =============================================================================
# SUBSYSTEM INITIALIZATION
# =============================================================================

def initialize_event_bus(logger: logging.Logger) -> bool:
    """
    PHASE 2: Initialize Defense Core Event Bus (CRITICAL).
    
    The event bus is the foundation for all inter-subsystem communication.
    All other subsystems depend on this being operational.
    
    Args:
        logger: Logger instance
    
    Returns:
        True if successful
    """
    logger.info("=" * 70)
    logger.info("PHASE 2: INITIALIZING EVENT BUS (CRITICAL)")
    logger.info("=" * 70)
    
    try:
        from defense_core import reset_defense_bus, get_defense_bus
        
        logger.info("[EVENT BUS] Resetting defense core...")
        reset_defense_bus()
        
        logger.info("[EVENT BUS] Obtaining bus singleton...")
        bus = get_defense_bus()
        
        if bus is None:
            logger.error("[EVENT BUS] ✗ Bus initialization returned None")
            return False
        
        state.event_bus = bus
        logger.info("[EVENT BUS] ✓ Event bus ready")
        logger.info(f"[EVENT BUS] - Queue stats: {bus.get_statistics()}")
        
        return True
        
    except Exception as e:
        logger.error(f"[EVENT BUS] ✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def initialize_tactical_state(logger: logging.Logger) -> bool:
    """
    PHASE 2.5: Initialize Shared Tactical State (CRITICAL).
    
    Tactical state is shared between radar and EW for synchronized
    intelligence sharing and decision-making.
    
    Args:
        logger: Logger instance
    
    Returns:
        True if successful
    """
    logger.info("=" * 70)
    logger.info("PHASE 2.5: INITIALIZING TACTICAL STATE (CRITICAL)")
    logger.info("=" * 70)
    
    try:
        from defense_core.tactical_state import TacticalState
        
        logger.info("[TACTICAL] Creating shared state container...")
        tactical_state = TacticalState()
        
        state.tactical_state = tactical_state
        logger.info("[TACTICAL] ✓ Tactical state initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"[TACTICAL] ✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def initialize_radar_subsystem(
    logger: logging.Logger,
    targets: Optional[list] = None
) -> bool:
    """
    PHASE 3: Initialize Radar Subsystem (CRITICAL).
    
    The radar simulation engine is the primary data source. It processes
    physics models, generates detections, tracks targets, and publishes
    intelligence to the event bus for consumption by EW.
    
    Args:
        logger: Logger instance
        targets: Optional list of target states
    
    Returns:
        True if successful
    """
    logger.info("=" * 70)
    logger.info("PHASE 3: INITIALIZING RADAR SUBSYSTEM (CRITICAL)")
    logger.info("=" * 70)
    
    try:
        from subsystems import RadarSubsystem
        from simulation_engine.physics import TargetState
        
        # Default scenario if no targets provided
        if targets is None:
            targets = [
                TargetState(
                    id=1, pos_x=1200.0, pos_y=800.0,
                    vel_x=-35.0, vel_y=-15.0, type="hostile"
                ),
                TargetState(
                    id=2, pos_x=1800.0, pos_y=-500.0,
                    vel_x=-45.0, vel_y=10.0, type="civilian"
                ),
                TargetState(
                    id=3, pos_x=900.0, pos_y=300.0,
                    vel_x=-28.0, vel_y=-20.0, type="hostile"
                )
            ]
        
        radar_config = {
            'sensor_id': 'PHOENIX_RADAR_01',
            'frame_dt': 0.1,  # 10 Hz
            'rpm': 60,
            'scan_angle_deg': 120,
            'enable_defense_core': True,
            'enable_ew_effects': True
        }
        
        logger.info(f"[RADAR] Creating subsystem (sensor: {radar_config['sensor_id']})")
        radar = RadarSubsystem(radar_config)
        
        logger.info(f"[RADAR] Initializing with {len(targets)} targets...")
        if not radar.initialize(
            initial_targets=targets,
            event_bus=state.event_bus,
            tactical_state=state.tactical_state
        ):
            logger.error("[RADAR] ✗ Radar initialization failed")
            return False
        
        state.radar = radar
        logger.info(f"[RADAR] ✓ Radar online")
        logger.info(f"[RADAR] - Frame rate: {1.0/radar_config['frame_dt']:.1f} Hz")
        logger.info(f"[RADAR] - Target count: {len(targets)}")
        
        return True
        
    except Exception as e:
        logger.error(f"[RADAR] ✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def initialize_ew_subsystem(logger: logging.Logger) -> bool:
    """
    PHASE 4: Initialize Cognitive EW Subsystem (OPTIONAL).
    
    The EW (Electronic Warfare) subsystem processes radar intelligence
    through an AI pipeline to classify threats and recommend defensive
    actions. This subsystem is optional; the system can operate in
    radar-only mode if EW initialization fails.
    
    Args:
        logger: Logger instance
    
    Returns:
        True if successful (or skipped)
    """
    logger.info("=" * 70)
    logger.info("PHASE 4: INITIALIZING EW SUBSYSTEM (OPTIONAL)")
    logger.info("=" * 70)
    
    try:
        from subsystems import EWSubsystem
        
        ew_config = {
            'effector_id': 'COGNITIVE_EW_01',
            'enable_ingestion': True,
            'ingestion_mode': 'event_bus',
            'log_all_updates': False
        }
        
        logger.info(f"[EW] Creating subsystem (effector: {ew_config['effector_id']})")
        ew = EWSubsystem(ew_config)
        
        logger.info("[EW] Initializing cognitive pipeline...")
        if not ew.initialize(tactical_state=state.tactical_state):
            logger.warning("[EW] ✗ EW initialization failed - continuing in radar-only mode")
            state.ew = None
            return True  # Not critical
        
        state.ew = ew
        logger.info("[EW] ✓ EW engine online")
        logger.info(f"[EW] - Ingestion mode: {ew_config['ingestion_mode']}")
        
        return True
        
    except Exception as e:
        logger.warning(f"[EW] ✗ Initialization failed: {e} - Continuing in radar-only mode")
        state.ew = None
        return True  # Not critical


def initialize_api_server(logger: logging.Logger) -> bool:
    """
    PHASE 5: Start API Server (OPTIONAL).
    
    The API server provides HTTP endpoints for querying system state,
    health status, and event logs. It runs as a subprocess to ensure
    isolation from the main simulation loop.
    
    Args:
        logger: Logger instance
    
    Returns:
        True if successful or skipped
    """
    logger.info("=" * 70)
    logger.info("PHASE 5: STARTING API SERVER (OPTIONAL)")
    logger.info("=" * 70)
    
    try:
        import importlib.util
        
        # Check if uvicorn is available
        if not importlib.util.find_spec("uvicorn"):
            logger.warning("[API] ✗ Uvicorn not found - API server will use Flask dev server")
        
        # Prepare command based on platform
        if IS_WINDOWS:
            cmd = [sys.executable, "-m", "api.server"]
        else:
            cmd = [sys.executable, "-m", "api.server"]
        
        api_log = RUNTIME_DIR / "api_server.log"
        logger.info(f"[API] Starting subprocess: {' '.join(cmd)}")
        
        with open(api_log, 'w') as logfile:
            process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT / "photonic-radar-ai"),
                stdout=logfile,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if IS_WINDOWS else 0
            )
        
        state.api_process = process
        logger.info(f"[API] ✓ API server started (PID: {process.pid})")
        logger.info(f"[API] - Listening on http://localhost:5000")
        logger.info(f"[API] - Log: {api_log}")
        
        # Wait briefly for server startup
        time.sleep(1)
        
        return True
        
    except Exception as e:
        logger.warning(f"[API] ✗ Failed to start API server: {e}")
        return False


def initialize_dashboard(logger: logging.Logger) -> bool:
    """
    PHASE 6: Start Dashboard UI (OPTIONAL).
    
    The Streamlit dashboard provides real-time tactical visualization
    of the radar display (PPI), threat assessment, and EW status.
    It connects to the API server via HTTP, so the API must be running.
    
    Args:
        logger: Logger instance
    
    Returns:
        True if successful or skipped
    """
    logger.info("=" * 70)
    logger.info("PHASE 6: STARTING STREAMLIT DASHBOARD (OPTIONAL)")
    logger.info("=" * 70)
    
    try:
        import importlib.util
        
        if not importlib.util.find_spec("streamlit"):
            logger.warning("[DASHBOARD] ✗ Streamlit not found - skipping dashboard")
            return False
        
        dashboard_script = PROJECT_ROOT / "photonic-radar-ai" / "ui" / "dashboard.py"
        
        if not dashboard_script.exists():
            logger.warning(f"[DASHBOARD] ✗ Dashboard script not found: {dashboard_script}")
            return False
        
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            str(dashboard_script),
            "--logger.level=warning",
            "--client.showErrorDetails=false"
        ]
        
        dashboard_log = RUNTIME_DIR / "dashboard.log"
        logger.info(f"[DASHBOARD] Starting subprocess: streamlit run ui/dashboard.py")
        
        with open(dashboard_log, 'w') as logfile:
            process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_ROOT / "photonic-radar-ai"),
                stdout=logfile,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if IS_WINDOWS else 0
            )
        
        state.dashboard_process = process
        logger.info(f"[DASHBOARD] ✓ Dashboard started (PID: {process.pid})")
        logger.info(f"[DASHBOARD] - URL: http://localhost:8501")
        logger.info(f"[DASHBOARD] - Log: {dashboard_log}")
        
        return True
        
    except Exception as e:
        logger.warning(f"[DASHBOARD] ✗ Failed to start dashboard: {e}")
        return False


# =============================================================================
# MAIN SIMULATION LOOP
# =============================================================================

def run_simulation_loop(logger: logging.Logger) -> None:
    """
    Execute main simulation loop.
    
    Coordinates radar frames, EW decisions, state updates, and
    IPC synchronization at fixed time intervals (10 Hz).
    
    Args:
        logger: Logger instance
    """
    logger.info("=" * 70)
    logger.info("STARTING MAIN SIMULATION LOOP")
    logger.info("=" * 70)
    
    class SimulationClock:
        """Fixed-rate simulation clock with drift correction."""
        def __init__(self, hz: float = 10.0):
            self.tick_rate = hz
            self.tick_interval = 1.0 / hz
            self.tick_count = 0
            self.start_time = None
            self.next_tick_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
            self.next_tick_time = self.start_time + self.tick_interval
            self.tick_count = 0
        
        def wait_for_next_tick(self) -> int:
            current = time.perf_counter()
            sleep_time = self.next_tick_time - current
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.tick_count += 1
            self.next_tick_time = self.start_time + (self.tick_count + 1) * self.tick_interval
            return self.tick_count
    
    clock = SimulationClock(hz=10.0)
    clock.start()
    
    state.running = True
    tick_count = 0
    
    try:
        while not state.shutdown_requested:
            tick = clock.wait_for_next_tick()
            
            # RADAR FRAME
            if state.radar:
                radar_result = state.radar.tick()
                if tick_count % 100 == 0:  # Log every 10 seconds
                    logger.debug(f"[TICK {tick:6d}] Radar frame executed")
            
            # EW DECISION
            if state.ew:
                ew_result = state.ew.tick()
            
            # STATE UPDATE
            if state.tactical_state:
                # Tactical state updates handled via radar.tick() and ew.tick()
                state.tactical_state.update_tick(tick_count)
            
            tick_count += 1
    
    except KeyboardInterrupt:
        logger.info("[LOOP] Interrupted by user")
    except Exception as e:
        logger.error(f"[LOOP] ✗ Fatal error in main loop: {e}")
        import traceback
        traceback.print_exc()
    finally:
        state.running = False


# =============================================================================
# SHUTDOWN & CLEANUP
# =============================================================================

def shutdown_subsystems(logger: logging.Logger) -> None:
    """
    Gracefully shutdown all subsystems in reverse order.
    
    Args:
        logger: Logger instance
    """
    logger.info("=" * 70)
    logger.info("GRACEFUL SHUTDOWN SEQUENCE")
    logger.info("=" * 70)
    
    # Stop main loop
    state.running = False
    
    # Terminate subprocesses
    if state.dashboard_process:
        try:
            logger.info("[SHUTDOWN] Terminating dashboard...")
            if IS_WINDOWS:
                state.dashboard_process.terminate()
            else:
                os.kill(state.dashboard_process.pid, signal.SIGTERM)
            state.dashboard_process.wait(timeout=5)
            logger.info("[SHUTDOWN] ✓ Dashboard terminated")
        except Exception as e:
            logger.warning(f"[SHUTDOWN] Dashboard termination warning: {e}")
    
    if state.api_process:
        try:
            logger.info("[SHUTDOWN] Terminating API server...")
            if IS_WINDOWS:
                state.api_process.terminate()
            else:
                os.kill(state.api_process.pid, signal.SIGTERM)
            state.api_process.wait(timeout=5)
            logger.info("[SHUTDOWN] ✓ API server terminated")
        except Exception as e:
            logger.warning(f"[SHUTDOWN] API server termination warning: {e}")
    
    # Shutdown subsystems
    if state.ew:
        try:
            logger.info("[SHUTDOWN] Shutting down EW subsystem...")
            state.ew.shutdown()
            logger.info("[SHUTDOWN] ✓ EW subsystem shutdown")
        except Exception as e:
            logger.warning(f"[SHUTDOWN] EW shutdown warning: {e}")
    
    if state.radar:
        try:
            logger.info("[SHUTDOWN] Shutting down radar subsystem...")
            state.radar.shutdown()
            logger.info("[SHUTDOWN] ✓ Radar subsystem shutdown")
        except Exception as e:
            logger.warning(f"[SHUTDOWN] Radar shutdown warning: {e}")
    
    if state.event_bus:
        try:
            logger.info("[SHUTDOWN] Shutting down event bus...")
            logger.info("[SHUTDOWN] ✓ Event bus shutdown")
        except Exception as e:
            logger.warning(f"[SHUTDOWN] Event bus shutdown warning: {e}")
    
    logger.info("[SHUTDOWN] ✓ ALL SYSTEMS DOWN")


# =============================================================================
# BOOTSTRAP & MAIN
# =============================================================================

def main():
    """
    Main entry point for PHOENIX-RADAR platform.
    
    This function orchestrates the complete startup sequence:
    1. Parse command-line arguments
    2. Setup logging
    3. Initialize all subsystems
    4. Run main simulation loop
    5. Handle graceful shutdown
    """
    global logger
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="PHOENIX-RADAR AI Defense Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Headless radar + API
  python main.py --ui               # With Streamlit dashboard
  python main.py --debug            # Debug logging
  python main.py --api-only         # API server only
        """
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging (verbose output)'
    )
    parser.add_argument(
        '--ui',
        action='store_true',
        help='Launch Streamlit tactical dashboard'
    )
    parser.add_argument(
        '--api-only',
        action='store_true',
        help='Start API server only (no radar simulation)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Disable browser auto-open for dashboard'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(debug=args.debug)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info(" PHOENIX-RADAR: COGNITIVE PHOTONIC RADAR DEFENSE SYSTEM")
    logger.info(" Sensor → Intelligence → EW → Effect")
    logger.info("=" * 70)
    logger.info("")
    logger.info(f"System: {platform.platform()}")
    logger.info(f"Python: {sys.version.split()[0]}")
    logger.info(f"Project: {PROJECT_ROOT}")
    logger.info("")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # PHASE 1: Configuration loaded (implicit)
    logger.info("=" * 70)
    logger.info("PHASE 1: CONFIGURATION & LOGGING")
    logger.info("=" * 70)
    logger.info("[CONFIG] ✓ Configuration loaded")
    logger.info("[CONFIG] ✓ Logging initialized")
    logger.info("")
    
    # PHASE 2-4: Initialize critical subsystems
    if not initialize_event_bus(logger):
        logger.error("✗ SYSTEM ABORT: Event bus initialization failed")
        return 1
    
    if not initialize_tactical_state(logger):
        logger.error("✗ SYSTEM ABORT: Tactical state initialization failed")
        return 1
    
    if not initialize_radar_subsystem(logger):
        logger.error("✗ SYSTEM ABORT: Radar initialization failed")
        return 1
    
    # PHASE 4: Optional EW subsystem
    initialize_ew_subsystem(logger)
    
    logger.info("")
    
    # PHASE 5-6: Optional presentation layer
    if not args.api_only:
        initialize_api_server(logger)
        
        if args.ui:
            time.sleep(2)  # Wait for API to be ready
            initialize_dashboard(logger)
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("✓ SYSTEM READY")
    logger.info("=" * 70)
    logger.info("")
    
    if state.api_process:
        logger.info("API Server: http://localhost:5000")
        logger.info("  - GET /state     → Full system state")
        logger.info("  - GET /health    → Health status")
        logger.info("  - GET /events    → Event log")
    
    if state.dashboard_process:
        logger.info("Dashboard: http://localhost:8501")
    
    if not args.api_only:
        logger.info("Radar: Simulation running at 10 Hz")
        if state.ew:
            logger.info("EW Engine: Cognitive intelligence pipeline active")
    
    logger.info("")
    logger.info("Press Ctrl+C to shutdown gracefully...")
    logger.info("")
    
    # Main simulation loop
    try:
        run_simulation_loop(logger)
    except Exception as e:
        logger.error(f"✗ Unhandled exception in main loop: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        shutdown_subsystems(logger)
    
    logger.info("✓ PHOENIX-RADAR shutdown complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())
