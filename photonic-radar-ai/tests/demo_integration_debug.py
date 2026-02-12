"""
Integration Debug Mode Demo
===========================

Demonstrates the integration debugger with comprehensive
message tracking, packet monitoring, and latency display.
"""

import sys
import logging

sys.path.insert(0, '.')

from simulation_engine.synchronized_simulation import (
    SynchronizedRadarEWSimulation,
    create_test_scenario
)
from simulation_engine.physics import TargetState
from simulation_engine.integration_debugger import (
    IntegrationDebugger,
    create_debug_header,
    create_debug_footer
)
from defense_core import reset_defense_bus, get_defense_bus

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress normal logs to see debug output clearly
    format='%(message)s'
)


def demo_integration_debug():
    """Demonstrate integration debug mode."""
    
    # Create debugger
    debugger = IntegrationDebugger(
        enable_message_printing=True,
        enable_latency_tracking=True,
        enable_queue_monitoring=True,
        max_trace_history=100
    )
    
    # Print header
    create_debug_header()
    
    # Reset event bus
    reset_defense_bus()
    
    # Create scenario
    radar_config, ew_config, _ = create_test_scenario('single_hostile')
    radar_config['rpm'] = 0  # Stop scanning
    radar_config['debug_packets'] = False  # Disable radar's own debug output
    
    # Create target
    targets = [
        TargetState(
            id=1,
            pos_x=1000.0,
            pos_y=0.0,
            vel_x=-50.0,
            vel_y=0.0,
            type="hostile"
        )
    ]
    
    # Create simulation
    sim = SynchronizedRadarEWSimulation(
        radar_config=radar_config,
        ew_config=ew_config,
        targets=targets,
        max_frames=30,
        enable_cycle_logging=False  # Disable cycle logging to see debug output clearly
    )
    
    # Get event bus for monitoring
    bus = get_defense_bus()
    
    print("\nStarting simulation with debug monitoring...\n")
    
    # Run simulation with debug monitoring
    for frame in range(30):
        # Run tick
        result = sim.tick()
        
        # Monitor radar intelligence packets
        if sim.radar.packets_sent > debugger.stats.total_intel_sent:
            # New packet sent
            num_tracks = result.get('num_tracks', 0)
            num_threats = result.get('num_threats', 0)
            dropped = sim.radar.packets_dropped > debugger.stats.total_intel_dropped
            
            # Get queue size from bus
            bus_stats = bus.get_statistics()
            intel_queue_size = bus_stats.get('radar_to_ew_queue_size', 0)
            
            debugger.log_intelligence_sent(
                frame_id=frame,
                num_tracks=num_tracks,
                num_threats=num_threats,
                queue_size=intel_queue_size,
                dropped=dropped
            )
        
        # Monitor EW intelligence reception
        ew_stats = sim.ew_pipeline.get_statistics()
        if ew_stats.get('messages_processed', 0) > debugger.stats.total_intel_received:
            debugger.log_intelligence_received(
                frame_id=frame,
                num_tracks=result.get('num_tracks', 0),
                num_threats=result.get('num_threats', 0)
            )
        
        # Monitor EW attack packets
        if hasattr(sim.ew_pipeline, 'feedback_publisher'):
            ew_pub_stats = sim.ew_pipeline.feedback_publisher.get_statistics()
            if ew_pub_stats.get('packets_sent', 0) > debugger.stats.total_attack_sent:
                # New attack packet sent
                num_cms = len(sim.ew_pipeline.feedback_publisher.active_cms) if hasattr(sim.ew_pipeline.feedback_publisher, 'active_cms') else 0
                dropped = ew_pub_stats.get('packets_dropped', 0) > debugger.stats.total_attack_dropped
                
                # Get queue size
                bus_stats = bus.get_statistics()
                attack_queue_size = bus_stats.get('ew_to_radar_queue_size', 0)
                
                debugger.log_attack_sent(
                    frame_id=frame,
                    num_countermeasures=num_cms,
                    queue_size=attack_queue_size,
                    dropped=dropped
                )
        
        # Monitor radar attack reception
        if sim.radar.last_ew_packet and frame > 0:
            # Check if this is a new packet
            if len(sim.radar.last_ew_packet.active_countermeasures) > 0:
                debugger.log_attack_received(
                    frame_id=frame,
                    num_countermeasures=len(sim.radar.last_ew_packet.active_countermeasures)
                )
        
        # Print queue status every 10 frames
        if frame % 10 == 0 and frame > 0:
            bus_stats = bus.get_statistics()
            debugger.print_queue_status(
                intel_queue_size=bus_stats.get('radar_to_ew_queue_size', 0),
                attack_queue_size=bus_stats.get('ew_to_radar_queue_size', 0)
            )
    
    # Stop simulation
    sim.stop()
    
    # Print footer with summary
    create_debug_footer(debugger)
    
    return debugger


def demo_with_packet_drops():
    """Demonstrate debug mode with simulated packet drops."""
    print("\n" + "="*80)
    print("DEMO: Packet Drop Detection")
    print("="*80)
    print("Simulating high load scenario with potential packet drops...\n")
    
    # Create debugger
    debugger = IntegrationDebugger(
        enable_message_printing=True,
        enable_latency_tracking=True
    )
    
    # Simulate some messages with drops
    for i in range(20):
        # Intelligence packets
        dropped = (i % 7 == 0)  # Drop every 7th packet
        debugger.log_intelligence_sent(
            frame_id=i,
            num_tracks=2,
            num_threats=1,
            queue_size=i % 5,
            dropped=dropped
        )
        
        if not dropped:
            debugger.log_intelligence_received(
                frame_id=i,
                num_tracks=2,
                num_threats=1
            )
            
            # Attack packets (if threats detected)
            attack_dropped = (i % 11 == 0)  # Drop every 11th packet
            debugger.log_attack_sent(
                frame_id=i,
                num_countermeasures=1,
                queue_size=i % 3,
                dropped=attack_dropped
            )
            
            if not attack_dropped:
                debugger.log_attack_received(
                    frame_id=i,
                    num_countermeasures=1
                )
    
    # Print summary
    debugger.print_statistics()
    debugger.print_message_flow_diagram(last_n=15)


if __name__ == '__main__':
    print("\n" + "="*80)
    print("INTEGRATION DEBUG MODE DEMONSTRATION")
    print("="*80)
    
    # Demo 1: Real simulation with debug monitoring
    print("\n[DEMO 1] Real Simulation with Debug Monitoring")
    debugger1 = demo_integration_debug()
    
    # Demo 2: Packet drop detection
    print("\n[DEMO 2] Packet Drop Detection")
    demo_with_packet_drops()
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nIntegration debug mode provides:")
    print("  ✓ Real-time message tracking")
    print("  ✓ Packet drop detection and highlighting")
    print("  ✓ Queue size monitoring")
    print("  ✓ Latency measurement (radar ↔ EW)")
    print("  ✓ Comprehensive statistics")
    print("  ✓ Visual message flow diagrams")
    print("="*80 + "\n")
