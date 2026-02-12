"""
Integration Debug Monitor
==========================

Debug mode for closed-loop simulation that:
- Prints all exchanged messages
- Visualizes data flow
- Flags dropped or delayed packets

Author: Debug Tools Team
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class MessageEvent:
    """Represents a message event in the system."""
    timestamp: float
    message_type: str  # 'INTEL_TX', 'INTEL_RX', 'FEEDBACK_TX', 'FEEDBACK_RX'
    message_id: str
    frame_id: int
    sender: str
    receiver: str
    payload_size: int
    latency_ms: Optional[float] = None
    dropped: bool = False
    delayed: bool = False


@dataclass
class DataFlowMetrics:
    """Metrics for data flow analysis."""
    messages_sent: int = 0
    messages_received: int = 0
    messages_dropped: int = 0
    messages_delayed: int = 0
    total_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')


class IntegrationDebugMonitor:
    """
    Debug monitor for closed-loop simulation.
    
    Tracks all message exchanges and flags issues.
    """
    
    def __init__(self,
                 enable_message_printing: bool = True,
                 enable_flow_visualization: bool = True,
                 latency_threshold_ms: float = 100.0,
                 log_directory: str = './debug_logs'):
        """
        Initialize debug monitor.
        
        Args:
            enable_message_printing: Print all messages
            enable_flow_visualization: Generate flow diagrams
            latency_threshold_ms: Threshold for delayed packets
            log_directory: Directory for debug logs
        """
        self.enable_printing = enable_message_printing
        self.enable_visualization = enable_flow_visualization
        self.latency_threshold = latency_threshold_ms
        self.log_dir = Path(log_directory)
        
        if self.enable_visualization:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Message tracking
        self.message_events: List[MessageEvent] = []
        self.pending_messages: Dict[str, MessageEvent] = {}
        
        # Metrics by type
        self.metrics: Dict[str, DataFlowMetrics] = defaultdict(DataFlowMetrics)
        
        # Frame tracking
        self.frame_messages: Dict[int, List[MessageEvent]] = defaultdict(list)
        
        logger.info(f"Integration debug monitor initialized: latency_threshold={latency_threshold_ms}ms")
    
    def log_message_sent(self,
                        message_type: str,
                        message_id: str,
                        frame_id: int,
                        sender: str,
                        receiver: str,
                        payload_size: int):
        """Log a message being sent."""
        event = MessageEvent(
            timestamp=time.time(),
            message_type=message_type,
            message_id=message_id,
            frame_id=frame_id,
            sender=sender,
            receiver=receiver,
            payload_size=payload_size
        )
        
        self.message_events.append(event)
        self.pending_messages[message_id] = event
        self.frame_messages[frame_id].append(event)
        
        self.metrics[message_type].messages_sent += 1
        
        if self.enable_printing:
            self._print_message_sent(event)
    
    def log_message_received(self,
                            message_type: str,
                            message_id: str,
                            frame_id: int,
                            receiver: str):
        """Log a message being received."""
        receive_time = time.time()
        
        # Find corresponding sent message
        if message_id in self.pending_messages:
            sent_event = self.pending_messages.pop(message_id)
            latency_ms = (receive_time - sent_event.timestamp) * 1000
            
            # Check if delayed
            delayed = latency_ms > self.latency_threshold
            
            # Create receive event
            event = MessageEvent(
                timestamp=receive_time,
                message_type=message_type,
                message_id=message_id,
                frame_id=frame_id,
                sender=sent_event.sender,
                receiver=receiver,
                payload_size=sent_event.payload_size,
                latency_ms=latency_ms,
                delayed=delayed
            )
            
            self.message_events.append(event)
            self.frame_messages[frame_id].append(event)
            
            # Update metrics
            metrics = self.metrics[message_type]
            metrics.messages_received += 1
            metrics.total_latency_ms += latency_ms
            metrics.max_latency_ms = max(metrics.max_latency_ms, latency_ms)
            metrics.min_latency_ms = min(metrics.min_latency_ms, latency_ms)
            
            if delayed:
                metrics.messages_delayed += 1
            
            if self.enable_printing:
                self._print_message_received(event)
        else:
            logger.warning(f"Received message {message_id} without corresponding send event")
    
    def log_message_dropped(self, message_type: str, message_id: str, reason: str):
        """Log a dropped message."""
        if message_id in self.pending_messages:
            sent_event = self.pending_messages.pop(message_id)
            sent_event.dropped = True
            
            self.metrics[message_type].messages_dropped += 1
            
            if self.enable_printing:
                self._print_message_dropped(sent_event, reason)
    
    def _print_message_sent(self, event: MessageEvent):
        """Print message sent event."""
        print(f"\n{'='*70}")
        print(f"📤 MESSAGE SENT")
        print(f"{'='*70}")
        print(f"  Type:      {event.message_type}")
        print(f"  ID:        {event.message_id[:16]}...")
        print(f"  Frame:     {event.frame_id}")
        print(f"  Route:     {event.sender} → {event.receiver}")
        print(f"  Size:      {event.payload_size} bytes")
        print(f"  Time:      {event.timestamp:.3f}s")
    
    def _print_message_received(self, event: MessageEvent):
        """Print message received event."""
        status = "⚠️  DELAYED" if event.delayed else "✓ OK"
        
        print(f"\n{'='*70}")
        print(f"📥 MESSAGE RECEIVED {status}")
        print(f"{'='*70}")
        print(f"  Type:      {event.message_type}")
        print(f"  ID:        {event.message_id[:16]}...")
        print(f"  Frame:     {event.frame_id}")
        print(f"  Route:     {event.sender} → {event.receiver}")
        print(f"  Latency:   {event.latency_ms:.1f} ms")
        print(f"  Time:      {event.timestamp:.3f}s")
        
        if event.delayed:
            print(f"  ⚠️  WARNING: Latency exceeds threshold ({self.latency_threshold}ms)")
    
    def _print_message_dropped(self, event: MessageEvent, reason: str):
        """Print message dropped event."""
        print(f"\n{'='*70}")
        print(f"❌ MESSAGE DROPPED")
        print(f"{'='*70}")
        print(f"  Type:      {event.message_type}")
        print(f"  ID:        {event.message_id[:16]}...")
        print(f"  Frame:     {event.frame_id}")
        print(f"  Route:     {event.sender} → {event.receiver}")
        print(f"  Reason:    {reason}")
    
    def visualize_data_flow(self, frame_id: Optional[int] = None):
        """
        Visualize data flow for a frame or entire simulation.
        
        Args:
            frame_id: Specific frame to visualize, or None for all
        """
        if not self.enable_visualization:
            return
        
        if frame_id is not None:
            self._visualize_frame_flow(frame_id)
        else:
            self._visualize_complete_flow()
    
    def _visualize_frame_flow(self, frame_id: int):
        """Visualize data flow for a specific frame."""
        events = self.frame_messages.get(frame_id, [])
        
        print(f"\n{'='*70}")
        print(f"DATA FLOW VISUALIZATION - FRAME {frame_id}")
        print(f"{'='*70}\n")
        
        # Group by message type
        intel_tx = [e for e in events if 'INTEL_TX' in e.message_type]
        intel_rx = [e for e in events if 'INTEL_RX' in e.message_type]
        feedback_tx = [e for e in events if 'FEEDBACK_TX' in e.message_type]
        feedback_rx = [e for e in events if 'FEEDBACK_RX' in e.message_type]
        
        # ASCII diagram
        print("  ┌─────────────┐                    ┌─────────────┐")
        print("  │    RADAR    │                    │     EW      │")
        print("  └─────────────┘                    └─────────────┘")
        print("        │                                    │")
        
        if intel_tx:
            latency = intel_rx[0].latency_ms if intel_rx else 0
            status = "⚠️ " if latency > self.latency_threshold else "✓ "
            print(f"        │ {status}Intelligence ({latency:.1f}ms)")
            print("        ├────────────────────────────────>│")
        
        if feedback_tx:
            latency = feedback_rx[0].latency_ms if feedback_rx else 0
            status = "⚠️ " if latency > self.latency_threshold else "✓ "
            print(f"        │<────────────────────────────────┤ {status}Feedback ({latency:.1f}ms)")
        
        print("        │                                    │")
        print()
    
    def _visualize_complete_flow(self):
        """Visualize complete data flow."""
        print(f"\n{'='*70}")
        print(f"COMPLETE DATA FLOW VISUALIZATION")
        print(f"{'='*70}\n")
        
        # Timeline
        print("Timeline:")
        print("-" * 70)
        
        for event in sorted(self.message_events, key=lambda e: e.timestamp):
            time_str = f"{event.timestamp:.3f}s"
            
            if 'TX' in event.message_type:
                arrow = "→"
                status = "📤"
            else:
                arrow = "←"
                status = "📥"
                if event.delayed:
                    status = "⚠️ "
                elif event.dropped:
                    status = "❌"
            
            print(f"{time_str:>10} {status} Frame {event.frame_id:3d}: "
                  f"{event.sender:10} {arrow} {event.receiver:10} "
                  f"({event.message_type})")
        
        print()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get debug statistics."""
        stats = {}
        
        for msg_type, metrics in self.metrics.items():
            avg_latency = (metrics.total_latency_ms / metrics.messages_received 
                          if metrics.messages_received > 0 else 0)
            
            stats[msg_type] = {
                'sent': metrics.messages_sent,
                'received': metrics.messages_received,
                'dropped': metrics.messages_dropped,
                'delayed': metrics.messages_delayed,
                'avg_latency_ms': avg_latency,
                'max_latency_ms': metrics.max_latency_ms if metrics.max_latency_ms > 0 else 0,
                'min_latency_ms': metrics.min_latency_ms if metrics.min_latency_ms < float('inf') else 0,
                'drop_rate': metrics.messages_dropped / metrics.messages_sent if metrics.messages_sent > 0 else 0,
                'delay_rate': metrics.messages_delayed / metrics.messages_received if metrics.messages_received > 0 else 0
            }
        
        return stats
    
    def print_summary(self):
        """Print debug summary."""
        print(f"\n{'='*70}")
        print(f"INTEGRATION DEBUG SUMMARY")
        print(f"{'='*70}\n")
        
        stats = self.get_statistics()
        
        for msg_type, metrics in stats.items():
            print(f"{msg_type}:")
            print(f"  Sent:     {metrics['sent']}")
            print(f"  Received: {metrics['received']}")
            print(f"  Dropped:  {metrics['dropped']} ({metrics['drop_rate']:.1%})")
            print(f"  Delayed:  {metrics['delayed']} ({metrics['delay_rate']:.1%})")
            print(f"  Latency:  avg={metrics['avg_latency_ms']:.1f}ms, "
                  f"min={metrics['min_latency_ms']:.1f}ms, "
                  f"max={metrics['max_latency_ms']:.1f}ms")
            print()
        
        # Check for pending messages
        if self.pending_messages:
            print(f"⚠️  WARNING: {len(self.pending_messages)} messages never received:")
            for msg_id in list(self.pending_messages.keys())[:5]:
                event = self.pending_messages[msg_id]
                print(f"  - {event.message_type} (Frame {event.frame_id})")
            print()
    
    def save_debug_log(self, filename: str = 'debug_log.json'):
        """Save debug log to file."""
        if not self.enable_visualization:
            return
        
        filepath = self.log_dir / filename
        
        debug_data = {
            'statistics': self.get_statistics(),
            'events': [
                {
                    'timestamp': e.timestamp,
                    'type': e.message_type,
                    'id': e.message_id,
                    'frame': e.frame_id,
                    'sender': e.sender,
                    'receiver': e.receiver,
                    'latency_ms': e.latency_ms,
                    'dropped': e.dropped,
                    'delayed': e.delayed
                }
                for e in self.message_events
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(debug_data, f, indent=2)
        
        logger.info(f"Debug log saved: {filepath}")
