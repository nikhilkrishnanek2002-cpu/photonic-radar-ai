#!/usr/bin/env python3
"""
Performance Benchmarking Script
================================

Comprehensive benchmark suite for radar detection pipeline:
  - Throughput measurement (detections/sec)
  - Latency analysis (end-to-end, per-stage)
  - Resource utilization (CPU, memory)
  - Accuracy metrics (precision, recall, f1_score)
  - Scalability testing (varying load)

Integrates with MetricsLogger for persistent CSV logging
and LatencyProfiler for detailed timing analysis.
"""

import time
import logging
import json
import psutil
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics


# Import components we created
try:
    from metrics_logger import SimulationMetrics, MetricsLogger, MetricsAnalyzer
    from latency_profiler import LatencyProfiler, LatencyContext
except ImportError as e:
    print(f"Warning: Could not import helpers: {e}")
    print("Make sure metrics_logger.py and latency_profiler.py are in the same directory")


@dataclass
class BenchmarkConfig:
    """Benchmark configuration."""
    experiment_name: str = "radar_benchmark"
    num_trials: int = 100
    target_frame_rate: int = 10  # Hz
    num_targets: int = 3
    noise_level: float = 0.1
    output_dir: str = "results"
    enable_latency_profiling: bool = True
    enable_resource_monitoring: bool = True
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'BenchmarkConfig':
        """Load config from YAML file."""
        try:
            import yaml
            with open(yaml_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return cls(**config_dict)
        except Exception as e:
            logging.warning(f"Could not load YAML config: {e}, using defaults")
            return cls()


@dataclass
class TrialResult:
    """Result of a single benchmark trial."""
    trial_id: int
    timestamp: str
    frame_count: int
    total_time_sec: float
    throughput_fps: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cpu_percent: float
    memory_mb: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int


class BenchmarkRunner:
    """Execute comprehensive performance benchmarks."""
    
    def __init__(self, config: BenchmarkConfig, logger: Optional[MetricsLogger] = None):
        """Initialize benchmark runner."""
        self.config = config
        self.logger_obj = logging.getLogger("BenchmarkRunner")
        self.metrics_logger = logger
        
        # Create metrics logger if not provided
        if self.metrics_logger is None:
            self.metrics_logger = MetricsLogger(
                output_dir=config.output_dir,
                experiment_name=config.experiment_name
            )
        
        self.latency_profiler = LatencyProfiler(experiment_name=config.experiment_name)
        
        # Results tracking
        self.trials: List[TrialResult] = []
        self.process = psutil.Process(os.getpid())
        
        self.logger_obj.info(f"BenchmarkRunner initialized: {config.experiment_name}")
    
    def simulate_frame_processing(self, frame_id: int) -> Tuple[List[Dict], float]:
        """
        Simulate radar frame processing pipeline.
        
        Returns:
            (detections, total_latency_ms)
        """
        detections = []
        
        # Stage 1: Signal acquisition and digitization
        with LatencyContext(self.latency_profiler, "signal_acquisition", frame_id):
            time.sleep(0.002)  # 2ms typical
            raw_signal = self._simulate_signal_acquisition()
        
        # Stage 2: Signal processing (FFT, filtering)
        with LatencyContext(self.latency_profiler, "signal_processing", frame_id):
            time.sleep(0.005)  # 5ms typical
            processed = self._simulate_signal_processing(raw_signal)
        
        # Stage 3: Detection (CFAR, clustering)
        with LatencyContext(self.latency_profiler, "detection", frame_id):
            time.sleep(0.003)  # 3ms typical
            detections = self._simulate_detection(processed)
        
        # Stage 4: Tracking (Kalman filter)
        with LatencyContext(self.latency_profiler, "tracking", frame_id):
            time.sleep(0.001)  # 1ms typical
            detections = self._simulate_tracking(detections)
        
        total_latency = self.latency_profiler.get_end_to_end_latency(frame_id)
        return detections, total_latency
    
    def _simulate_signal_acquisition(self) -> Dict:
        """Simulate raw signal acquisition."""
        import random
        return {
            'samples': random.randint(1000, 2000),
            'power': random.uniform(0.1, 1.0)
        }
    
    def _simulate_signal_processing(self, raw_signal: Dict) -> Dict:
        """Simulate signal processing and filtering."""
        import random
        return {
            'fft_bins': raw_signal['samples'] // 2,
            'snr_db': random.uniform(5, 30),
            'noise_power': self.config.noise_level
        }
    
    def _simulate_detection(self, processed: Dict) -> List[Dict]:
        """Simulate target detection."""
        import random
        num_detections = random.randint(
            max(0, self.config.num_targets - 1),
            self.config.num_targets + 1
        )
        
        detections = []
        for i in range(num_detections):
            detections.append({
                'target_id': i,
                'range_m': random.uniform(100, 10000),
                'azimuth_deg': random.uniform(-180, 180),
                'velocity_mps': random.uniform(-100, 100),
                'snr_db': random.uniform(5, 30),
                'confidence': random.uniform(0.5, 1.0)
            })
        
        return detections
    
    def _simulate_tracking(self, detections: List[Dict]) -> List[Dict]:
        """Simulate Kalman filter tracking."""
        # In real implementation, would update tracked targets
        return detections
    
    def run_single_trial(self, trial_id: int) -> TrialResult:
        """Run a single benchmark trial."""
        trial_start = time.time()
        frame_count = 0
        latencies = []
        all_detections = []
        
        # Reset latency profiler for this trial
        self.latency_profiler.reset()
        
        # Monitor process resources
        cpu_samples = []
        memory_samples = []
        
        # Run frames for the trial duration
        frame_duration = 1.0 / self.config.target_frame_rate
        
        while time.time() - trial_start < 60:  # 60-second benchmark
            frame_start = time.time()
            frame_id = frame_count
            
            # Process frame
            detections, latency = self.simulate_frame_processing(frame_id)
            all_detections.append(detections)
            latencies.append(latency)
            
            # Collect resource metrics
            try:
                cpu_samples.append(self.process.cpu_percent())
                memory_samples.append(self.process.memory_info().rss / 1024 / 1024)  # MB
            except Exception as e:
                self.logger_obj.debug(f"Resource monitoring error: {e}")
            
            # Simulate frame pacing
            frame_elapsed = time.time() - frame_start
            if frame_elapsed < frame_duration:
                time.sleep(frame_duration - frame_elapsed)
            
            frame_count += 1
            
            if frame_count >= self.config.num_trials:
                break
        
        trial_time = time.time() - trial_start
        
        # Calculate metrics
        throughput_fps = frame_count / trial_time
        avg_latency = statistics.mean(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0
        
        avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0
        avg_memory = statistics.mean(memory_samples) if memory_samples else 0
        
        # Simulate accuracy metrics
        total_targets = self.config.num_targets * frame_count
        detected = sum(len(d) for d in all_detections)
        tp = detected
        fp = max(0, detected - total_targets)
        tn = total_targets - tp
        fn = total_targets - tp
        
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        result = TrialResult(
            trial_id=trial_id,
            timestamp=datetime.now().isoformat(),
            frame_count=frame_count,
            total_time_sec=trial_time,
            throughput_fps=throughput_fps,
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            cpu_percent=avg_cpu,
            memory_mb=avg_memory,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
        )
        
        # Log to metrics logger
        self._log_trial_result(result)
        
        self.logger_obj.info(
            f"Trial {trial_id}: {throughput_fps:.1f} fps, "
            f"{avg_latency:.2f}ms avg latency, "
            f"{accuracy:.2%} accuracy"
        )
        
        return result
    
    def _log_trial_result(self, result: TrialResult):
        """Log trial result to metrics logger."""
        try:
            metrics = SimulationMetrics(
                timestamp=result.timestamp,
                experiment_id=self.config.experiment_name,
                trial_num=result.trial_id,
                detections_count=result.true_positives + result.false_positives,
                true_positives=result.true_positives,
                false_positives=result.false_positives,
                true_negatives=result.true_negatives,
                false_negatives=result.false_negatives,
                detection_latency_ms=result.avg_latency_ms,
                processing_time_ms=result.total_time_sec * 1000,
                frame_rate=result.throughput_fps,
                cpu_usage_percent=result.cpu_percent,
                memory_usage_mb=result.memory_mb,
                accuracy=result.accuracy,
                precision=result.precision,
                recall=result.recall,
                f1_score=result.f1_score,
                system_healthy=True,
            )
            self.metrics_logger.log_metrics(metrics)
        except Exception as e:
            self.logger_obj.error(f"Failed to log metrics: {e}")
    
    def run_benchmark(self, num_trials: int = 5) -> Dict:
        """Run complete benchmark with multiple trials."""
        self.logger_obj.info(f"Starting benchmark: {num_trials} trials")
        
        for trial_id in range(num_trials):
            self.logger_obj.info(f"Running trial {trial_id + 1}/{num_trials}")
            result = self.run_single_trial(trial_id)
            self.trials.append(result)
        
        # Generate summary
        summary = self.generate_summary()
        
        # Save results
        self.save_results()
        
        return summary
    
    def generate_summary(self) -> Dict:
        """Generate benchmark summary."""
        if not self.trials:
            return {'error': 'No trials completed'}
        
        throughputs = [t.throughput_fps for t in self.trials]
        latencies = [t.avg_latency_ms for t in self.trials]
        accuracies = [t.accuracy for t in self.trials]
        cpu_usage = [t.cpu_percent for t in self.trials]
        memory_usage = [t.memory_mb for t in self.trials]
        
        summary = {
            'experiment': self.config.experiment_name,
            'timestamp': datetime.now().isoformat(),
            'num_trials': len(self.trials),
            'throughput': {
                'mean_fps': round(statistics.mean(throughputs), 2),
                'std_fps': round(statistics.stdev(throughputs), 2) if len(throughputs) > 1 else 0,
                'min_fps': round(min(throughputs), 2),
                'max_fps': round(max(throughputs), 2),
            },
            'latency': {
                'mean_ms': round(statistics.mean(latencies), 3),
                'std_ms': round(statistics.stdev(latencies), 3) if len(latencies) > 1 else 0,
                'min_ms': round(min(latencies), 3),
                'max_ms': round(max(latencies), 3),
            },
            'accuracy': {
                'mean': round(statistics.mean(accuracies), 4),
                'std': round(statistics.stdev(accuracies), 4) if len(accuracies) > 1 else 0,
                'min': round(min(accuracies), 4),
                'max': round(max(accuracies), 4),
            },
            'resources': {
                'cpu_percent': round(statistics.mean(cpu_usage), 2),
                'memory_mb': round(statistics.mean(memory_usage), 2),
            },
        }
        
        return summary
    
    def save_results(self):
        """Save benchmark results to files."""
        output_path = Path(self.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save summary
        summary = self.generate_summary()
        summary_path = output_path / f"benchmark_summary_{self.config.experiment_name}_{timestamp}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        self.logger_obj.info(f"Benchmark summary: {summary_path}")
        
        # Save trial details
        trials_data = [asdict(t) for t in self.trials]
        trials_path = output_path / f"benchmark_trials_{self.config.experiment_name}_{timestamp}.json"
        with open(trials_path, 'w') as f:
            json.dump(trials_data, f, indent=2)
        self.logger_obj.info(f"Trial details: {trials_path}")
        
        # Save latency profile
        if self.config.enable_latency_profiling:
            self.latency_profiler.save_report(self.config.output_dir)
        
        # Save metrics logger summary
        metrics_summary = self.metrics_logger.get_session_summary()
        metrics_summary_path = output_path / f"metrics_summary_{self.config.experiment_name}_{timestamp}.json"
        with open(metrics_summary_path, 'w') as f:
            json.dump(metrics_summary, f, indent=2)
        self.logger_obj.info(f"Metrics summary: {metrics_summary_path}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    config = BenchmarkConfig(
        experiment_name="radar_benchmark_demo",
        num_trials=50,
        target_frame_rate=10,
        num_targets=3,
        noise_level=0.1,
    )
    
    # Run benchmark
    runner = BenchmarkRunner(config)
    summary = runner.run_benchmark(num_trials=3)
    
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(json.dumps(summary, indent=2))
