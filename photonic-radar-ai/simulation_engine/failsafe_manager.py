"""
Fail-Safe Subsystem Manager
===========================

Provides fault-tolerant wrappers for radar and EW subsystems.

Features:
- Subsystem isolation (failures don't cascade)
- Automatic recovery attempts
- Graceful degradation
- Comprehensive failure logging

Author: Fail-Safe Systems Team
"""

import logging
import traceback
from typing import Optional, Callable, Any, Dict
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class SubsystemState(Enum):
    """Subsystem operational state."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    PAUSED = "PAUSED"


@dataclass
class SubsystemStatus:
    """Status information for a subsystem."""
    name: str
    state: SubsystemState
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    failure_count: int = 0
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    recovery_attempts: int = 0


class FailSafeWrapper:
    """
    Fail-safe wrapper for subsystem operations.
    
    Provides:
    - Exception handling
    - Failure logging
    - State tracking
    - Recovery attempts
    """
    
    def __init__(self,
                 subsystem_name: str,
                 max_consecutive_failures: int = 3,
                 enable_auto_recovery: bool = True,
                 recovery_delay_s: float = 1.0):
        """
        Initialize fail-safe wrapper.
        
        Args:
            subsystem_name: Name of subsystem
            max_consecutive_failures: Max failures before marking as FAILED
            enable_auto_recovery: Enable automatic recovery attempts
            recovery_delay_s: Delay between recovery attempts
        """
        self.subsystem_name = subsystem_name
        self.max_consecutive_failures = max_consecutive_failures
        self.enable_auto_recovery = enable_auto_recovery
        self.recovery_delay_s = recovery_delay_s
        
        self.status = SubsystemStatus(
            name=subsystem_name,
            state=SubsystemState.HEALTHY
        )
        
        logger.info(f"[FAILSAFE] {subsystem_name} wrapper initialized")
    
    def execute(self,
                operation: Callable,
                operation_name: str,
                *args,
                **kwargs) -> tuple[bool, Any]:
        """
        Execute operation with fail-safe protection.
        
        Args:
            operation: Function to execute
            operation_name: Name of operation (for logging)
            *args, **kwargs: Arguments to pass to operation
            
        Returns:
            (success: bool, result: Any)
        """
        import time
        
        try:
            # Execute operation
            result = operation(*args, **kwargs)
            
            # Mark success
            self.status.last_success_time = time.time()
            self.status.consecutive_failures = 0
            
            # Recover from degraded state
            if self.status.state in [SubsystemState.DEGRADED, SubsystemState.RECOVERING]:
                logger.info(f"[FAILSAFE] ✓ {self.subsystem_name} recovered from {self.status.state.value}")
                self.status.state = SubsystemState.HEALTHY
            
            return True, result
            
        except Exception as e:
            # Log failure
            self._log_failure(operation_name, e)
            
            # Update state
            self._update_state_on_failure()
            
            return False, None
    
    def _log_failure(self, operation_name: str, error: Exception):
        """Log subsystem failure."""
        import time
        
        self.status.last_failure_time = time.time()
        self.status.failure_count += 1
        self.status.consecutive_failures += 1
        self.status.last_error = str(error)
        
        # Get traceback
        tb = traceback.format_exc()
        
        # Log with severity based on consecutive failures
        if self.status.consecutive_failures == 1:
            logger.warning(
                f"[FAILSAFE] ⚠️  {self.subsystem_name} failure in {operation_name}\n"
                f"Error: {error}\n"
                f"Consecutive failures: {self.status.consecutive_failures}"
            )
        elif self.status.consecutive_failures < self.max_consecutive_failures:
            logger.error(
                f"[FAILSAFE] ❌ {self.subsystem_name} repeated failure in {operation_name}\n"
                f"Error: {error}\n"
                f"Consecutive failures: {self.status.consecutive_failures}/{self.max_consecutive_failures}\n"
                f"Traceback:\n{tb}"
            )
        else:
            logger.critical(
                f"[FAILSAFE] 🔥 {self.subsystem_name} CRITICAL FAILURE in {operation_name}\n"
                f"Error: {error}\n"
                f"Consecutive failures: {self.status.consecutive_failures}\n"
                f"Subsystem marked as FAILED\n"
                f"Traceback:\n{tb}"
            )
    
    def _update_state_on_failure(self):
        """Update subsystem state based on failure count."""
        if self.status.consecutive_failures >= self.max_consecutive_failures:
            self.status.state = SubsystemState.FAILED
        elif self.status.consecutive_failures > 1:
            self.status.state = SubsystemState.DEGRADED
    
    def is_healthy(self) -> bool:
        """Check if subsystem is healthy."""
        return self.status.state == SubsystemState.HEALTHY
    
    def is_operational(self) -> bool:
        """Check if subsystem can operate (healthy or degraded)."""
        return self.status.state in [SubsystemState.HEALTHY, SubsystemState.DEGRADED]
    
    def is_failed(self) -> bool:
        """Check if subsystem has failed."""
        return self.status.state == SubsystemState.FAILED
    
    def pause(self):
        """Pause subsystem."""
        logger.warning(f"[FAILSAFE] ⏸️  {self.subsystem_name} PAUSED")
        self.status.state = SubsystemState.PAUSED
    
    def resume(self):
        """Resume subsystem."""
        if self.status.state == SubsystemState.PAUSED:
            logger.info(f"[FAILSAFE] ▶️  {self.subsystem_name} RESUMED")
            self.status.state = SubsystemState.HEALTHY
            self.status.consecutive_failures = 0
    
    def reset(self):
        """Reset failure counters."""
        logger.info(f"[FAILSAFE] 🔄 {self.subsystem_name} reset")
        self.status.consecutive_failures = 0
        self.status.state = SubsystemState.HEALTHY
    
    def get_status(self) -> SubsystemStatus:
        """Get current status."""
        return self.status


class FailSafeSimulationManager:
    """
    Manages fail-safe behavior for radar-EW simulation.
    
    Rules:
    - If EW crashes → Radar continues normally
    - If Radar fails → EW pauses safely
    - Never allow one subsystem to kill the other
    """
    
    def __init__(self):
        """Initialize fail-safe manager."""
        self.radar_wrapper = FailSafeWrapper(
            subsystem_name="RADAR",
            max_consecutive_failures=5,
            enable_auto_recovery=False  # Radar is critical, don't auto-recover
        )
        
        self.ew_wrapper = FailSafeWrapper(
            subsystem_name="EW",
            max_consecutive_failures=3,
            enable_auto_recovery=True
        )
        
        logger.info("[FAILSAFE] Simulation manager initialized")
    
    def execute_radar_tick(self, radar_tick_fn: Callable, *args, **kwargs) -> tuple[bool, Any]:
        """
        Execute radar tick with fail-safe protection.
        
        If radar fails:
        - Log failure
        - Pause EW subsystem
        - Return failure status
        
        Returns:
            (success: bool, result: Any)
        """
        success, result = self.radar_wrapper.execute(
            radar_tick_fn,
            "radar_tick",
            *args,
            **kwargs
        )
        
        if not success:
            # Radar failed - pause EW
            if self.ew_wrapper.is_operational():
                logger.warning("[FAILSAFE] Radar failed → Pausing EW subsystem")
                self.ew_wrapper.pause()
        else:
            # Radar succeeded - resume EW if paused due to radar failure
            if self.ew_wrapper.status.state == SubsystemState.PAUSED:
                logger.info("[FAILSAFE] Radar recovered → Resuming EW subsystem")
                self.ew_wrapper.resume()
        
        return success, result
    
    def execute_ew_processing(self, ew_process_fn: Callable, *args, **kwargs) -> tuple[bool, Any]:
        """
        Execute EW processing with fail-safe protection.
        
        If EW fails:
        - Log failure
        - Radar continues normally
        - Return failure status
        
        Returns:
            (success: bool, result: Any)
        """
        # Check if EW is paused (due to radar failure)
        if self.ew_wrapper.status.state == SubsystemState.PAUSED:
            logger.debug("[FAILSAFE] EW paused, skipping processing")
            return False, None
        
        success, result = self.ew_wrapper.execute(
            ew_process_fn,
            "ew_processing",
            *args,
            **kwargs
        )
        
        if not success:
            # EW failed - radar continues normally
            logger.info("[FAILSAFE] EW failed → Radar continues normally")
        
        return success, result
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            'radar': {
                'state': self.radar_wrapper.status.state.value,
                'failure_count': self.radar_wrapper.status.failure_count,
                'consecutive_failures': self.radar_wrapper.status.consecutive_failures,
                'last_error': self.radar_wrapper.status.last_error
            },
            'ew': {
                'state': self.ew_wrapper.status.state.value,
                'failure_count': self.ew_wrapper.status.failure_count,
                'consecutive_failures': self.ew_wrapper.status.consecutive_failures,
                'last_error': self.ew_wrapper.status.last_error
            },
            'overall_health': self._get_overall_health()
        }
    
    def _get_overall_health(self) -> str:
        """Get overall system health."""
        if self.radar_wrapper.is_failed():
            return "CRITICAL - Radar failed"
        elif self.ew_wrapper.is_failed():
            return "DEGRADED - EW failed, radar operational"
        elif not self.radar_wrapper.is_healthy() or not self.ew_wrapper.is_healthy():
            return "DEGRADED - Subsystem issues"
        else:
            return "HEALTHY"
    
    def print_status(self):
        """Print comprehensive status."""
        status = self.get_system_status()
        
        print("\n" + "="*80)
        print("FAIL-SAFE SYSTEM STATUS")
        print("="*80)
        
        # Radar status
        radar_state = status['radar']['state']
        radar_icon = self._get_state_icon(radar_state)
        print(f"\nRADAR: {radar_icon} {radar_state}")
        print(f"  Failures: {status['radar']['failure_count']} "
              f"(consecutive: {status['radar']['consecutive_failures']})")
        if status['radar']['last_error']:
            print(f"  Last error: {status['radar']['last_error']}")
        
        # EW status
        ew_state = status['ew']['state']
        ew_icon = self._get_state_icon(ew_state)
        print(f"\nEW: {ew_icon} {ew_state}")
        print(f"  Failures: {status['ew']['failure_count']} "
              f"(consecutive: {status['ew']['consecutive_failures']})")
        if status['ew']['last_error']:
            print(f"  Last error: {status['ew']['last_error']}")
        
        # Overall health
        print(f"\nOverall Health: {status['overall_health']}")
        print("="*80 + "\n")
    
    def _get_state_icon(self, state: str) -> str:
        """Get icon for state."""
        icons = {
            'HEALTHY': '✓',
            'DEGRADED': '⚠️',
            'FAILED': '❌',
            'RECOVERING': '🔄',
            'PAUSED': '⏸️'
        }
        return icons.get(state, '?')
