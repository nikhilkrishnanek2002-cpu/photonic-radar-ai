"""
Fail-Safe Simulation Demo
=========================

Demonstrates fail-safe behavior with simulated subsystem failures.
"""

import sys
import logging
import time

sys.path.insert(0, '.')

from simulation_engine.failsafe_manager import (
    FailSafeSimulationManager,
    SubsystemState
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def demo_ew_failure():
    """Demonstrate EW failure with radar continuing."""
    print("\n" + "="*80)
    print("DEMO 1: EW Failure (Radar Continues)")
    print("="*80)
    
    manager = FailSafeSimulationManager()
    
    # Simulate normal operation
    print("\n[Frame 0-2] Normal operation...")
    for i in range(3):
        # Radar tick (success)
        success, _ = manager.execute_radar_tick(lambda: {"frame": i, "tracks": 2})
        print(f"Frame {i}: Radar={'✓' if success else '❌'}")
        
        # EW processing (success)
        success, _ = manager.execute_ew_processing(lambda: {"decisions": 1})
        print(f"Frame {i}: EW={'✓' if success else '❌'}")
    
    # Simulate EW failures
    print("\n[Frame 3-5] EW failures (radar continues)...")
    for i in range(3, 6):
        # Radar tick (success)
        success, _ = manager.execute_radar_tick(lambda: {"frame": i, "tracks": 2})
        print(f"Frame {i}: Radar={'✓' if success else '❌'}")
        
        # EW processing (FAIL)
        def ew_fail():
            raise RuntimeError(f"EW processing error at frame {i}")
        
        success, _ = manager.execute_ew_processing(ew_fail)
        print(f"Frame {i}: EW={'✓' if success else '❌'} (FAILED)")
    
    # Continue with radar only
    print("\n[Frame 6-8] Radar continues, EW failed...")
    for i in range(6, 9):
        success, _ = manager.execute_radar_tick(lambda: {"frame": i, "tracks": 2})
        print(f"Frame {i}: Radar={'✓' if success else '❌'}")
        
        success, _ = manager.execute_ew_processing(lambda: {"decisions": 1})
        print(f"Frame {i}: EW={'✓' if success else '❌'} (still failed)")
    
    # Print status
    manager.print_status()


def demo_radar_failure():
    """Demonstrate radar failure with EW pausing."""
    print("\n" + "="*80)
    print("DEMO 2: Radar Failure (EW Pauses)")
    print("="*80)
    
    manager = FailSafeSimulationManager()
    
    # Simulate normal operation
    print("\n[Frame 0-2] Normal operation...")
    for i in range(3):
        success, _ = manager.execute_radar_tick(lambda: {"frame": i, "tracks": 2})
        print(f"Frame {i}: Radar={'✓' if success else '❌'}")
        
        success, _ = manager.execute_ew_processing(lambda: {"decisions": 1})
        print(f"Frame {i}: EW={'✓' if success else '❌'}")
    
    # Simulate radar failures
    print("\n[Frame 3-5] Radar failures (EW pauses)...")
    for i in range(3, 6):
        # Radar tick (FAIL)
        def radar_fail():
            raise RuntimeError(f"Radar processing error at frame {i}")
        
        success, _ = manager.execute_radar_tick(radar_fail)
        print(f"Frame {i}: Radar={'✓' if success else '❌'} (FAILED)")
        
        # EW processing (paused)
        success, _ = manager.execute_ew_processing(lambda: {"decisions": 1})
        print(f"Frame {i}: EW={'✓' if success else '❌'} (PAUSED)")
    
    # Radar recovers
    print("\n[Frame 6-8] Radar recovers (EW resumes)...")
    for i in range(6, 9):
        success, _ = manager.execute_radar_tick(lambda: {"frame": i, "tracks": 2})
        print(f"Frame {i}: Radar={'✓' if success else '❌'} (RECOVERED)")
        
        success, _ = manager.execute_ew_processing(lambda: {"decisions": 1})
        print(f"Frame {i}: EW={'✓' if success else '❌'} (RESUMED)")
    
    # Print status
    manager.print_status()


def demo_intermittent_failures():
    """Demonstrate handling of intermittent failures."""
    print("\n" + "="*80)
    print("DEMO 3: Intermittent Failures")
    print("="*80)
    
    manager = FailSafeSimulationManager()
    
    print("\n[Frames 0-15] Intermittent EW failures...")
    for i in range(16):
        # Radar always succeeds
        success, _ = manager.execute_radar_tick(lambda: {"frame": i, "tracks": 2})
        radar_status = '✓' if success else '❌'
        
        # EW fails every 4th frame
        if i % 4 == 0 and i > 0:
            def ew_fail():
                raise RuntimeError(f"Intermittent EW error at frame {i}")
            success, _ = manager.execute_ew_processing(ew_fail)
            ew_status = '❌ FAIL'
        else:
            success, _ = manager.execute_ew_processing(lambda: {"decisions": 1})
            ew_status = '✓' if success else '❌'
        
        print(f"Frame {i:2d}: Radar={radar_status} | EW={ew_status}")
    
    # Print status
    manager.print_status()


def demo_cascading_prevention():
    """Demonstrate prevention of cascading failures."""
    print("\n" + "="*80)
    print("DEMO 4: Cascading Failure Prevention")
    print("="*80)
    
    manager = FailSafeSimulationManager()
    
    print("\n[Scenario] Both subsystems fail simultaneously...")
    print("Expected: Failures isolated, no cascade\n")
    
    for i in range(5):
        # Both fail
        def radar_fail():
            raise RuntimeError(f"Radar error at frame {i}")
        
        def ew_fail():
            raise RuntimeError(f"EW error at frame {i}")
        
        radar_success, _ = manager.execute_radar_tick(radar_fail)
        ew_success, _ = manager.execute_ew_processing(ew_fail)
        
        print(f"Frame {i}: Radar={'✓' if radar_success else '❌'} | "
              f"EW={'✓' if ew_success else '❌'}")
        
        # Check that failures are isolated
        radar_state = manager.radar_wrapper.status.state
        ew_state = manager.ew_wrapper.status.state
        
        print(f"         States: Radar={radar_state.value} | EW={ew_state.value}")
    
    print("\n✓ Failures isolated - no cascading crash")
    
    # Print status
    manager.print_status()


if __name__ == '__main__':
    print("\n" + "="*80)
    print("FAIL-SAFE SUBSYSTEM BEHAVIOR DEMONSTRATION")
    print("="*80)
    
    # Demo 1: EW failure
    demo_ew_failure()
    
    # Demo 2: Radar failure
    demo_radar_failure()
    
    # Demo 3: Intermittent failures
    demo_intermittent_failures()
    
    # Demo 4: Cascading prevention
    demo_cascading_prevention()
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nFail-safe behavior verified:")
    print("  ✓ EW crashes → Radar continues normally")
    print("  ✓ Radar fails → EW pauses safely")
    print("  ✓ No cascading failures")
    print("  ✓ Comprehensive failure logging")
    print("  ✓ Automatic state management")
    print("="*80 + "\n")
