
import logging
import time
import sys
import unittest
from subsystems.radar_subsystem import RadarSubsystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRadarTelemetry(unittest.TestCase):
    def setUp(self):
        self.config = {
            'sensor_id': 'TEST_RADAR',
            'frame_dt': 0.1,
            'rpm': 12.0,
            'enable_defense_core': False,
            'enable_ew_effects': False,
            'enable_intelligence_export': False,
            'noise_level_db': -50
        }
        self.radar = RadarSubsystem(self.config)
        self.radar.initialize([]) # No initial targets

    def tearDown(self):
        if self.radar.initialized:
            self.radar.shutdown()

    def test_telemetry_collection(self):
        """Verify telemetry data is collected and exposed."""
        logger.info("Running radar tick...")
        
        # Run a few ticks
        for i in range(5):
            result = self.radar.tick()
            self.assertNotIn('error', result)
            self.assertIn('telemetry', result, "Telemetry missing from tick result")
            
            telemetry = result['telemetry']
            self.assertIn('peak_signal_power', telemetry)
            self.assertIn('mean_snr_db', telemetry)
            self.assertIn('track_confidence', telemetry)
            
            logger.info(f"Tick {i}: SNR={telemetry['mean_snr_db']:.2f}dB")
            time.sleep(0.01)

        # Check stats
        stats = self.radar.get_stats()
        self.assertIn('telemetry', stats)
        
        telemetry_stats = stats['telemetry']
        self.assertIn('history', telemetry_stats)
        self.assertIn('current', telemetry_stats)
        
        history = telemetry_stats['history']
        self.assertEqual(len(history), 5, "History length mismatch")
        
        logger.info("✓ Telemetry collection verified")

if __name__ == '__main__':
    unittest.main()
