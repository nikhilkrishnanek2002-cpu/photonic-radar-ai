
import unittest
import threading
import time
from defense_core.tactical_state import TacticalState
from subsystems.radar_subsystem import RadarSubsystem

class MockOrchestrator:
    def tick(self):
        return {
            'tracks': [{'id': 1}, {'id': 2}],
            'timestamp': time.time(),
            'telemetry': {'mean_snr_db': 15.0}
        }

class TestTacticalStateIntegration(unittest.TestCase):
    def test_radar_updates_state(self):
        # 1. Setup Shared State
        tactical_state = TacticalState()
        
        # 2. Setup Radar with State
        config = {'sensor_id': 'TEST_RADAR', 'frame_dt': 0.1}
        radar = RadarSubsystem(config)
        
        # Mock orchestrator to avoid physics dependency
        radar.initialized = True
        radar.orchestrator = MockOrchestrator()
        
        # Manually link state (simulating initialize)
        radar.tactical_state = tactical_state
        
        # 3. Run Radar Tick
        radar.tick()
        
        # 4. Verify State Update
        snapshot = tactical_state.get_snapshot()
        
        self.assertEqual(snapshot['radar']['status'], "ONLINE")
        self.assertEqual(len(snapshot['radar']['tracks']), 2)
        self.assertEqual(len(snapshot['radar']['telemetry_history']), 1)
        self.assertEqual(snapshot['radar']['telemetry_history'][0]['mean_snr_db'], 15.0)
        
    def test_state_snapshot_structure(self):
        ts = TacticalState()
        snapshot = ts.get_snapshot()
        
        self.assertIn('radar', snapshot)
        self.assertIn('ew', snapshot)
        self.assertIn('queues', snapshot)
        self.assertIn('tick', snapshot)
        self.assertIn('uptime', snapshot)

if __name__ == '__main__':
    unittest.main()
