#!/usr/bin/env python3
"""
Noise Experiment Generator
===========================

Investigates detection accuracy as a function of SNR (Signal-to-Noise Ratio).
Sweeps across noise levels and measures:
  - Detection rate vs SNR
  - Precision/recall curves
  - F1 score optimization
  - False positive/negative trends
  - Optimal threshold discovery

Outputs:
  - CSV with noise vs accuracy metrics
  - JSON experiment configuration
  - Summary statistics and thresholds
"""

import time
import logging
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict, field
import statistics
import random


try:
    from metrics_logger import SimulationMetrics, MetricsLogger
    from latency_profiler import LatencyProfiler, LatencyContext
except ImportError:
    print("Warning: Could not import helpers")


@dataclass
class NoiseExperimentConfig:
    """Configuration for noise experiment."""
    experiment_name: str = "noise_sensitivity"
    snr_db_range: Tuple[float, float] = (0.0, 30.0)
    snr_db_step: float = 2.0
    frames_per_snr: int = 50
    num_targets: int = 3
    target_detection_prob: float = 0.85
    false_alarm_rate: float = 0.05
    output_dir: str = "results"
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NoiseExperimentConfig':
        """Create from dictionary."""
        return cls(**data)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class NoiseExperimentResult:
    """Result for a single SNR level."""
    snr_db: float
    frame_count: int
    detection_count: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    detection_rate: float = 0.0
    false_alarm_rate: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    avg_latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def compute_metrics(self):
        """Calculate derived metrics."""
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        
        if total > 0:
            self.accuracy = (self.true_positives + self.true_negatives) / total
        
        if self.true_positives + self.false_positives > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        
        if self.true_positives + self.false_negatives > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        
        if self.true_negatives + self.false_positives > 0:
            self.false_alarm_rate = self.false_positives / (self.true_negatives + self.false_positives)
        
        self.detection_rate = self.recall


class NoiseExperimentGenerator:
    """Generate and run noise sensitivity experiments."""
    
    def __init__(self, config: NoiseExperimentConfig, metrics_logger: Optional[MetricsLogger] = None):
        """Initialize noise experiment generator."""
        self.config = config
        self.logger = logging.getLogger("NoiseExperimentGenerator")
        
        self.metrics_logger = metrics_logger
        if self.metrics_logger is None:
            self.metrics_logger = MetricsLogger(
                output_dir=config.output_dir,
                experiment_name=config.experiment_name
            )
        
        self.results: List[NoiseExperimentResult] = []
        self.latency_profiler = LatencyProfiler(experiment_name=config.experiment_name)
        
        self.logger.info(f"NoiseExperimentGenerator initialized: {config.experiment_name}")
    
    def simulate_detection_at_snr(self, snr_db: float, frame_id: int) -> Dict:
        """
        Simulate detection performance at given SNR.
        
        SNR affects detection probability and false alarm rate.
        """
        detections = []
        
        with LatencyContext(self.latency_profiler, "signal_acquisition", frame_id):
            time.sleep(0.001)
        
        with LatencyContext(self.latency_profiler, "signal_processing", frame_id):
            time.sleep(0.002)
        
        with LatencyContext(self.latency_profiler, "detection", frame_id):
            time.sleep(0.002)
        
        # SNR-dependent detection probability (sigmoid-like curve)
        # At SNR=0dB, ~50% detection; at SNR=15dB, ~90% detection
        snr_normalized = max(0, min(1, (snr_db - 0) / 20.0))
        detection_prob = min(
            self.config.target_detection_prob + (snr_normalized * 0.15),
            0.99
        )
        
        # SNR-dependent false alarm rate (inverse relationship)
        # At SNR=0dB, ~5% false alarms; at SNR=20dB, ~1% false alarms
        far_scaled = self.config.false_alarm_rate * (1 - snr_normalized * 0.7)
        
        # Expected detections (ground truth)
        expected_targets = self.config.num_targets
        background_cells = 1000  # Number of cells that could trigger false alarm
        
        # Simulate detections
        for target_id in range(expected_targets):
            if random.random() < detection_prob:
                detections.append({
                    'target_id': target_id,
                    'type': 'true_positive',
                    'snr_db': snr_db,
                })
        
        # Simulate false alarms
        false_alarms = int(background_cells * far_scaled)
        for i in range(false_alarms):
            if random.random() < 0.01:  # Stochastic false alarm generation
                detections.append({
                    'target_id': f"fa_{i}",
                    'type': 'false_positive',
                    'snr_db': snr_db,
                })
        
        return detections
    
    def run_experiment_at_snr(self, snr_db: float) -> NoiseExperimentResult:
        """Run experiment at a specific SNR level."""
        self.logger.info(f"Running experiment at SNR={snr_db:.1f} dB")
        
        latencies = []
        detections_per_frame = []
        
        tp = fp = tn = fn = 0
        
        for frame_id in range(self.config.frames_per_snr):
            detections = self.simulate_detection_at_snr(snr_db, frame_id)
            latency = self.latency_profiler.get_end_to_end_latency(frame_id)
            latencies.append(latency)
            
            # Count detection results
            true_pos = sum(1 for d in detections if d.get('type') == 'true_positive')
            false_pos = sum(1 for d in detections if d.get('type') == 'false_positive')
            
            tp += true_pos
            fp += false_pos
            
            # Simulate true negatives and false negatives
            actual_targets = self.config.num_targets
            fn += actual_targets - true_pos
            tn += max(0, 1000 - false_pos)  # Background cells without false alarm
            
            detections_per_frame.append(len(detections))
        
        avg_latency = statistics.mean(latencies) if latencies else 0
        
        result = NoiseExperimentResult(
            snr_db=snr_db,
            frame_count=self.config.frames_per_snr,
            detection_count=tp + fp,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            avg_latency_ms=avg_latency,
        )
        
        result.compute_metrics()
        
        # Log to metrics logger
        self._log_result(result)
        
        self.logger.info(
            f"SNR={snr_db:.1f}dB: Det.Rate={result.detection_rate:.2%}, "
            f"Precision={result.precision:.2%}, FAR={result.false_alarm_rate:.4f}"
        )
        
        return result
    
    def _log_result(self, result: NoiseExperimentResult):
        """Log experiment result to metrics logger."""
        try:
            metrics = SimulationMetrics(
                timestamp=result.timestamp,
                experiment_id=self.config.experiment_name,
                trial_num=int(result.snr_db * 10),  # Use SNR as trial identifier
                detections_count=result.detection_count,
                true_positives=result.true_positives,
                false_positives=result.false_positives,
                true_negatives=result.true_negatives,
                false_negatives=result.false_negatives,
                accuracy=result.accuracy,
                precision=result.precision,
                recall=result.recall,
                f1_score=result.f1_score,
                snr_db=result.snr_db,
                detection_latency_ms=result.avg_latency_ms,
                system_healthy=True,
            )
            self.metrics_logger.log_metrics(metrics)
        except Exception as e:
            self.logger.error(f"Failed to log metrics: {e}")
    
    def run_sweep(self) -> List[NoiseExperimentResult]:
        """Run complete SNR sweep."""
        snr_min, snr_max = self.config.snr_db_range
        snr_values = []
        
        current_snr = snr_min
        while current_snr <= snr_max:
            snr_values.append(current_snr)
            current_snr += self.config.snr_db_step
        
        self.logger.info(f"Running sweep over {len(snr_values)} SNR levels: {snr_min}-{snr_max} dB")
        
        for snr_db in snr_values:
            self.latency_profiler.reset()
            result = self.run_experiment_at_snr(snr_db)
            self.results.append(result)
        
        return self.results
    
    def find_optimal_threshold(self) -> Dict:
        """Find SNR threshold for acceptable performance."""
        if not self.results:
            return {}
        
        # Find SNR where detection rate exceeds 90%
        threshold_90_detection = None
        for result in self.results:
            if result.detection_rate >= 0.90:
                threshold_90_detection = result.snr_db
                break
        
        # Find SNR where F1 score is maximized
        max_f1 = max(r.f1_score for r in self.results)
        optimal_f1_snr = next(r.snr_db for r in self.results if r.f1_score == max_f1)
        
        # Find SNR where false alarm rate drops below 1%
        threshold_low_far = None
        for result in self.results:
            if result.false_alarm_rate < 0.01:
                threshold_low_far = result.snr_db
                break
        
        return {
            'threshold_90_percent_detection': threshold_90_detection,
            'optimal_f1_snr': optimal_f1_snr,
            'max_f1_score': max_f1,
            'threshold_low_false_alarms': threshold_low_far,
            'recommended_snr_db': optimal_f1_snr,
        }
    
    def generate_summary(self) -> Dict:
        """Generate experiment summary."""
        if not self.results:
            return {'error': 'No results collected'}
        
        summary = {
            'experiment': self.config.experiment_name,
            'timestamp': datetime.now().isoformat(),
            'config': self.config.to_dict(),
            'num_snr_levels': len(self.results),
            'snr_range': list(self.config.snr_db_range),
            'results': [asdict(r) for r in self.results],
            'thresholds': self.find_optimal_threshold(),
        }
        
        # Add performance curves
        snrs = [r.snr_db for r in self.results]
        detection_rates = [r.detection_rate for r in self.results]
        precisions = [r.precision for r in self.results]
        f1_scores = [r.f1_score for r in self.results]
        false_alarms = [r.false_alarm_rate for r in self.results]
        
        summary['performance_curves'] = {
            'snr_db': snrs,
            'detection_rate': detection_rates,
            'precision': precisions,
            'f1_score': f1_scores,
            'false_alarm_rate': false_alarms,
        }
        
        return summary
    
    def save_results(self) -> Tuple[str, str]:
        """Save experiment results to files."""
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary
        summary = self.generate_summary()
        summary_path = output_path / f"noise_experiment_{self.config.experiment_name}_{timestamp}.json"
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Experiment summary: {summary_path}")
        
        # Save as CSV for easy analysis
        csv_path = output_path / f"noise_experiment_{self.config.experiment_name}_{timestamp}.csv"
        import csv
        
        fieldnames = [
            'snr_db', 'frame_count', 'detection_count',
            'true_positives', 'false_positives', 'true_negatives', 'false_negatives',
            'detection_rate', 'false_alarm_rate', 'accuracy', 'precision', 'recall', 'f1_score',
            'avg_latency_ms'
        ]
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                writer.writerow(asdict(result))
        
        self.logger.info(f"Experiment CSV: {csv_path}")
        
        return str(summary_path), str(csv_path)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    config = NoiseExperimentConfig(
        experiment_name="noise_sensitivity_demo",
        snr_db_range=(0.0, 20.0),
        snr_db_step=2.0,
        frames_per_snr=20,
        num_targets=3,
    )
    
    # Run experiment
    generator = NoiseExperimentGenerator(config)
    results = generator.run_sweep()
    
    # Save results
    summary_path, csv_path = generator.save_results()
    
    # Print summary
    summary = generator.generate_summary()
    
    print("\n" + "=" * 60)
    print("NOISE EXPERIMENT SUMMARY")
    print("=" * 60)
    print(json.dumps(summary['thresholds'], indent=2))
    
    print("\n" + "=" * 60)
    print("PERFORMANCE CURVES")
    print("=" * 60)
    curves = summary['performance_curves']
    for i, snr in enumerate(curves['snr_db']):
        print(f"SNR={snr:5.1f}dB: DetRate={curves['detection_rate'][i]:.2%}, "
              f"Prec={curves['precision'][i]:.2%}, F1={curves['f1_score'][i]:.3f}, "
              f"FAR={curves['false_alarm_rate'][i]:.4f}")
