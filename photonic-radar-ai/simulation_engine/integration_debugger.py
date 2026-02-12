"""
Integration Debug Mode
======================

Comprehensive debugging utilities for radar-EW closed-loop simulation.

Features:
- Print all exchanged messages
- Highlight dropped packets
- Show queue sizes
- Display latency between radar and EW
- Track message flow
- Visualize system state

Author: Integration Debug Team
"""

import logging
import time
from typing import Dict, List, Optional, Any
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MessageTrace:
    """Trace record for a single message."""
    frame_id: int
    timestamp: float
    message_type: str  # 'intelligence' or 'attack'
    direction: str  # 'radar->ew' or 'ew->radar'
    num_tracks: int
    num_threats: int
    num_countermeasures: int
    latency_ms: Optional[float] = None
    dropped: bool = False
    queue_size: int = 0


@dataclass
class DebugStatistics:
    """Debug statistics for monitoring."""
    total_intel_sent: int = 0
    total_intel_received: int = 0
    total_intel_dropped: int = 0
    total_attack_sent: int = 0
    total_attack_received: int = 0
    total_attack_dropped: int = 0
    mean_intel_latency_ms: float = 0.0
    mean_attack_latency_ms: float = 0.0
    max_queue_size_intel: int = 0
    max_queue_size_attack: int = 0
    intel_latencies: List[float] = field(default_factory=list)
    attack_latencies: List[float] = field(default_factory=list)


class IntegrationDebugger:
    """
    Integration debugger for radar-EW simulation.
    
    Provides comprehensive debugging capabilities:
    - Message tracing
    - Packet drop detection
    - Queue monitoring
    - Latency tracking
    """
    
    def __init__(self, 
                 enable_message_printing: bool = True,
                 enable_latency_tracking: bool = True,
                 enable_queue_monitoring: bool = True,
                 max_trace_history: int = 100):
        """
        Initialize integration debugger.
        
        Args:
            enable_message_printing: Print all messages
            enable_latency_tracking: Track message latencies
            enable_queue_monitoring: Monitor queue sizes
            max_trace_history: Maximum trace records to keep
        """
        self.enable_message_printing = enable_message_printing
        self.enable_latency_tracking = enable_latency_tracking
        self.enable_queue_monitoring = enable_queue_monitoring
        
        # Message traces
        self.message_traces = deque(maxlen=max_trace_history)
        
        # Statistics
        self.stats = DebugStatistics()
        
        # Timing tracking
        self.intel_send_times = {}  # frame_id -> timestamp
        self.attack_send_times = {}  # frame_id -> timestamp
        
        logger.info("[DEBUG-MODE] Integration debugger initialized")
    
    def log_intelligence_sent(self, 
                              frame_id: int,
                              num_tracks: int,
                              num_threats: int,
                              queue_size: int = 0,
                              dropped: bool = False):
        """Log intelligence packet sent from radar."""
        timestamp = time.time()
        
        # Record send time for latency tracking
        if self.enable_latency_tracking:
            self.intel_send_times[frame_id] = timestamp
        
        # Update statistics
        self.stats.total_intel_sent += 1
        if dropped:
            self.stats.total_intel_dropped += 1
        if queue_size > self.stats.max_queue_size_intel:
            self.stats.max_queue_size_intel = queue_size
        
        # Create trace
        trace = MessageTrace(
            frame_id=frame_id,
            timestamp=timestamp,
            message_type='intelligence',
            direction='radar->ew',
            num_tracks=num_tracks,
            num_threats=num_threats,
            num_countermeasures=0,
            dropped=dropped,
            queue_size=queue_size
        )
        self.message_traces.append(trace)
        
        # Print message
        if self.enable_message_printing:
            status = "❌ DROPPED" if dropped else "✓ SENT"
            color = "\033[91m" if dropped else "\033[92m"
            reset = "\033[0m"
            
            print(f"{color}[MSG-INTEL] Frame {frame_id:3d} | "
                  f"{status:12s} | "
                  f"Tracks={num_tracks:2d} | "
                  f"Threats={num_threats:2d} | "
                  f"Queue={queue_size:2d}{reset}")
    
    def log_intelligence_received(self,
                                  frame_id: int,
                                  num_tracks: int,
                                  num_threats: int):
        """Log intelligence packet received by EW."""
        timestamp = time.time()
        
        # Update statistics
        self.stats.total_intel_received += 1
        
        # Calculate latency
        latency_ms = None
        if self.enable_latency_tracking and frame_id in self.intel_send_times:
            latency_ms = (timestamp - self.intel_send_times[frame_id]) * 1000
            self.stats.intel_latencies.append(latency_ms)
            if self.stats.intel_latencies:
                self.stats.mean_intel_latency_ms = sum(self.stats.intel_latencies) / len(self.stats.intel_latencies)
        
        # Print message
        if self.enable_message_printing:
            latency_str = f"{latency_ms:.2f}ms" if latency_ms else "N/A"
            print(f"\033[94m[MSG-INTEL] Frame {frame_id:3d} | "
                  f"RECEIVED     | "
                  f"Tracks={num_tracks:2d} | "
                  f"Threats={num_threats:2d} | "
                  f"Latency={latency_str:8s}\033[0m")
    
    def log_attack_sent(self,
                       frame_id: int,
                       num_countermeasures: int,
                       queue_size: int = 0,
                       dropped: bool = False):
        """Log attack packet sent from EW."""
        timestamp = time.time()
        
        # Record send time for latency tracking
        if self.enable_latency_tracking:
            self.attack_send_times[frame_id] = timestamp
        
        # Update statistics
        self.stats.total_attack_sent += 1
        if dropped:
            self.stats.total_attack_dropped += 1
        if queue_size > self.stats.max_queue_size_attack:
            self.stats.max_queue_size_attack = queue_size
        
        # Create trace
        trace = MessageTrace(
            frame_id=frame_id,
            timestamp=timestamp,
            message_type='attack',
            direction='ew->radar',
            num_tracks=0,
            num_threats=0,
            num_countermeasures=num_countermeasures,
            dropped=dropped,
            queue_size=queue_size
        )
        self.message_traces.append(trace)
        
        # Print message
        if self.enable_message_printing:
            status = "❌ DROPPED" if dropped else "✓ SENT"
            color = "\033[91m" if dropped else "\033[93m"
            reset = "\033[0m"
            
            print(f"{color}[MSG-ATTACK] Frame {frame_id:3d} | "
                  f"{status:12s} | "
                  f"CMs={num_countermeasures:2d} | "
                  f"Queue={queue_size:2d}{reset}")
    
    def log_attack_received(self,
                           frame_id: int,
                           num_countermeasures: int):
        """Log attack packet received by radar."""
        timestamp = time.time()
        
        # Update statistics
        self.stats.total_attack_received += 1
        
        # Calculate latency
        latency_ms = None
        if self.enable_latency_tracking and frame_id in self.attack_send_times:
            latency_ms = (timestamp - self.attack_send_times[frame_id]) * 1000
            self.stats.attack_latencies.append(latency_ms)
            if self.stats.attack_latencies:
                self.stats.mean_attack_latency_ms = sum(self.stats.attack_latencies) / len(self.stats.attack_latencies)
        
        # Print message
        if self.enable_message_printing:
            latency_str = f"{latency_ms:.2f}ms" if latency_ms else "N/A"
            print(f"\033[95m[MSG-ATTACK] Frame {frame_id:3d} | "
                  f"RECEIVED     | "
                  f"CMs={num_countermeasures:2d} | "
                  f"Latency={latency_str:8s}\033[0m")
    
    def print_queue_status(self, intel_queue_size: int, attack_queue_size: int):
        """Print current queue sizes."""
        if self.enable_queue_monitoring:
            print(f"\n[QUEUE-STATUS] Intel={intel_queue_size:2d} | Attack={attack_queue_size:2d}")
    
    def print_latency_summary(self):
        """Print latency summary."""
        if not self.enable_latency_tracking:
            return
        
        print(f"\n{'='*80}")
        print(f"LATENCY SUMMARY")
        print(f"{'='*80}")
        
        if self.stats.intel_latencies:
            print(f"Intelligence Packets:")
            print(f"  Mean latency: {self.stats.mean_intel_latency_ms:.2f}ms")
            print(f"  Min latency:  {min(self.stats.intel_latencies):.2f}ms")
            print(f"  Max latency:  {max(self.stats.intel_latencies):.2f}ms")
        else:
            print(f"Intelligence Packets: No data")
        
        if self.stats.attack_latencies:
            print(f"\nAttack Packets:")
            print(f"  Mean latency: {self.stats.mean_attack_latency_ms:.2f}ms")
            print(f"  Min latency:  {min(self.stats.attack_latencies):.2f}ms")
            print(f"  Max latency:  {max(self.stats.attack_latencies):.2f}ms")
        else:
            print(f"\nAttack Packets: No data")
        
        print(f"{'='*80}\n")
    
    def print_statistics(self):
        """Print comprehensive statistics."""
        print(f"\n{'='*80}")
        print(f"DEBUG STATISTICS")
        print(f"{'='*80}")
        
        print(f"\nIntelligence Packets (Radar → EW):")
        print(f"  Sent:     {self.stats.total_intel_sent:4d}")
        print(f"  Received: {self.stats.total_intel_received:4d}")
        print(f"  Dropped:  {self.stats.total_intel_dropped:4d}")
        if self.stats.total_intel_sent > 0:
            drop_rate = (self.stats.total_intel_dropped / self.stats.total_intel_sent) * 100
            print(f"  Drop rate: {drop_rate:.1f}%")
        
        print(f"\nAttack Packets (EW → Radar):")
        print(f"  Sent:     {self.stats.total_attack_sent:4d}")
        print(f"  Received: {self.stats.total_attack_received:4d}")
        print(f"  Dropped:  {self.stats.total_attack_dropped:4d}")
        if self.stats.total_attack_sent > 0:
            drop_rate = (self.stats.total_attack_dropped / self.stats.total_attack_sent) * 100
            print(f"  Drop rate: {drop_rate:.1f}%")
        
        print(f"\nQueue Sizes:")
        print(f"  Max intel queue:  {self.stats.max_queue_size_intel:4d}")
        print(f"  Max attack queue: {self.stats.max_queue_size_attack:4d}")
        
        if self.enable_latency_tracking:
            print(f"\nLatencies:")
            if self.stats.intel_latencies:
                print(f"  Intel mean:  {self.stats.mean_intel_latency_ms:.2f}ms")
            if self.stats.attack_latencies:
                print(f"  Attack mean: {self.stats.mean_attack_latency_ms:.2f}ms")
        
        print(f"{'='*80}\n")
    
    def print_message_flow_diagram(self, last_n: int = 10):
        """Print visual diagram of recent message flow."""
        print(f"\n{'='*80}")
        print(f"MESSAGE FLOW (Last {last_n} messages)")
        print(f"{'='*80}")
        
        recent_traces = list(self.message_traces)[-last_n:]
        
        for trace in recent_traces:
            if trace.message_type == 'intelligence':
                arrow = "RADAR ──→ EW  "
                color = "\033[94m"
                info = f"Tracks={trace.num_tracks}, Threats={trace.num_threats}"
            else:
                arrow = "RADAR ←── EW  "
                color = "\033[95m"
                info = f"CMs={trace.num_countermeasures}"
            
            status = "❌" if trace.dropped else "✓"
            latency = f"{trace.latency_ms:.1f}ms" if trace.latency_ms else "N/A"
            
            print(f"{color}Frame {trace.frame_id:3d} | {arrow} | {status} | "
                  f"{info:30s} | Latency={latency:8s}\033[0m")
        
        print(f"{'='*80}\n")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics as dictionary."""
        return {
            'intel_sent': self.stats.total_intel_sent,
            'intel_received': self.stats.total_intel_received,
            'intel_dropped': self.stats.total_intel_dropped,
            'attack_sent': self.stats.total_attack_sent,
            'attack_received': self.stats.total_attack_received,
            'attack_dropped': self.stats.total_attack_dropped,
            'mean_intel_latency_ms': self.stats.mean_intel_latency_ms,
            'mean_attack_latency_ms': self.stats.mean_attack_latency_ms,
            'max_queue_size_intel': self.stats.max_queue_size_intel,
            'max_queue_size_attack': self.stats.max_queue_size_attack
        }
    
    def reset(self):
        """Reset all statistics and traces."""
        self.message_traces.clear()
        self.stats = DebugStatistics()
        self.intel_send_times.clear()
        self.attack_send_times.clear()
        logger.info("[DEBUG-MODE] Statistics reset")


def create_debug_header():
    """Create debug mode header."""
    print("\n" + "="*80)
    print("INTEGRATION DEBUG MODE ENABLED")
    print("="*80)
    print("Legend:")
    print("  \033[92m✓ SENT\033[0m      - Message successfully sent")
    print("  \033[91m❌ DROPPED\033[0m  - Message dropped (queue full)")
    print("  \033[94m[MSG-INTEL]\033[0m  - Intelligence packet (Radar → EW)")
    print("  \033[95m[MSG-ATTACK]\033[0m - Attack packet (EW → Radar)")
    print("="*80 + "\n")


def create_debug_footer(debugger: IntegrationDebugger):
    """Create debug mode footer with summary."""
    print("\n" + "="*80)
    print("DEBUG MODE SUMMARY")
    print("="*80)
    debugger.print_statistics()
    debugger.print_latency_summary()
    debugger.print_message_flow_diagram(last_n=20)
