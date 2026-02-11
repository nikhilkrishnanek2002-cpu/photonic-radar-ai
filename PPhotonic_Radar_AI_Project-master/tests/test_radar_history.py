
import unittest
from collections import deque
from subsystems.radar_subsystem import RadarSubsystem

class MockOrchestrator:
    def tick(self):
        return {
            'tracks': [{'id': 1}, {'id': 2}],
            'timestamp': 1234567890
        }

class TestRadarHistory(unittest.TestCase):
    def test_rolling_buffer(self):
        config = {'sensor_id': 'TEST_RADAR', 'frame_dt': 0.1}
        radar = RadarSubsystem(config)
        radar.initialized = True
        radar.orchestrator = MockOrchestrator()
        
        # 1. Test Limit
        # Simulate 600 ticks
        for i in range(600):
            radar.tick()
            
        # Verify length is capped at 500
        self.assertEqual(len(radar.detection_history), 500)
        
        # Verify content of last item
        last_item = radar.detection_history[-1]
        self.assertEqual(last_item['frame'], 600)
        self.assertEqual(last_item['count'], 2)
        
        # Verify stats exposure
        stats = radar.get_stats()
        self.assertIn('detection_history', stats)
        self.assertEqual(len(stats['detection_history']), 500)
        
if __name__ == '__main__':
    unittest.main()
