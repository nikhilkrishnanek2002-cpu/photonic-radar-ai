#!/usr/bin/env python3
"""
Latency Profiler for Detection Pipeline
=========================================

Measures end-to-end latency of the radar detection pipeline
across all processing stages for performance analysis.

Features:
  - Stage-level latency tracking
  - End-to-end latency measurement
  - Percentile analysis (p50, p95, p99)
  - Performance bottleneck identification
"""

import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import json


@dataclass
class LatencyRecord:
    """Single latency measurement."""
    stage_name: str
    duration_ms: float
    timestamp: str
    frame_id: int = 0
    status: str = "success"


class LatencyProfiler:
    """Profile latency of detection pipeline stages."""
    
    def __init__(self, experiment_name: str = "latency_profile"):
        """Initialize latency profiler."""
        self.logger = logging.getLogger("LatencyProfiler")
        self.experiment_name = experiment_name
        
        # Stage tracking
        self.stages: Dict[str, List[float]] = defaultdict(list)  # stage -> [durations]
        self.records: List[LatencyRecord] = []
        self.stage_hierarchy: List[str] = []  # Order of stages
        
        # Current frame tracking
        self.frame_times: Dict[int, Dict[str, float]] = {}  # frame_id -> {stage -> time}
        self.current_frame_id = 0
        
        # Statistics cache
        self.stats_cache: Dict[str, Dict] = {}
    
    def start_stage(self, stage_name: str, frame_id: int = 0) -> float:
        """Mark stage start. Returns start timestamp."""
        self.current_frame_id = frame_id
        start_time = time.perf_counter()
        
        if frame_id not in self.frame_times:
            self.frame_times[frame_id] = {}
        
        self.frame_times[frame_id][f"{stage_name}_start"] = start_time
        return start_time
    
    def end_stage(self, stage_name: str, frame_id: int = 0, status: str = "success") -> float:
        """Mark stage end. Returns duration in milliseconds."""
        end_time = time.perf_counter()
        
        if frame_id not in self.frame_times:
            self.logger.warning(f"Frame {frame_id} not started, initializing")
            self.frame_times[frame_id] = {}
        
        start_key = f"{stage_name}_start"
        if start_key not in self.frame_times[frame_id]:
            self.logger.warning(f"Stage {stage_name} not started for frame {frame_id}")
            return 0.0
        
        start_time = self.frame_times[frame_id][start_key]
        duration_ms = (end_time - start_time) * 1000
        
        # Record stage timing
        self.stages[stage_name].append(duration_ms)
        
        # Create record
        record = LatencyRecord(
            stage_name=stage_name,
            duration_ms=duration_ms,
            timestamp=datetime.now().isoformat(),
            frame_id=frame_id,
            status=status,
        )
        self.records.append(record)
        
        # Add to hierarchy if new
        if stage_name not in self.stage_hierarchy:
            self.stage_hierarchy.append(stage_name)
        
        return duration_ms
    
    def get_end_to_end_latency(self, frame_id: int) -> float:
        """Calculate total end-to-end latency for a frame."""
        if frame_id not in self.frame_times:
            return 0.0
        
        times = self.frame_times[frame_id]
        start_times = [t for k, t in times.items() if k.endswith("_start")]
        
        if not start_times:
            return 0.0
        
        # Find earliest start and latest end
        min_start = min(start_times)
        max_end = time.perf_counter()
        
        # Calculate total from all recorded stages
        total_ms = 0.0
        for stage_name in self.stage_hierarchy:
            latencies = self.stages.get(stage_name, [])
            if latencies:
                total_ms += latencies[-1]  # Last measurement for this stage
        
        return total_ms
    
    def get_stage_statistics(self, stage_name: str) -> Dict[str, float]:
        """Get latency statistics for a stage."""
        if stage_name not in self.stages:
            return {}
        
        latencies = sorted(self.stages[stage_name])
        
        if not latencies:
            return {}
        
        import statistics
        
        def percentile(data, p):
            """Calculate pth percentile."""
            if not data:
                return 0
            index = int(len(data) * p / 100)
            return data[min(index, len(data) - 1)]
        
        return {
            'count': len(latencies),
            'mean_ms': round(statistics.mean(latencies), 3),
            'median_ms': round(statistics.median(latencies), 3),
            'std_ms': round(statistics.stdev(latencies), 3) if len(latencies) > 1 else 0.0,
            'min_ms': round(min(latencies), 3),
            'max_ms': round(max(latencies), 3),
            'p50_ms': round(percentile(latencies, 50), 3),
            'p95_ms': round(percentile(latencies, 95), 3),
            'p99_ms': round(percentile(latencies, 99), 3),
        }
    
    def get_pipeline_latencies(self) -> Dict[str, Dict[str, float]]:
        """Get latencies for all stages."""
        return {
            stage: self.get_stage_statistics(stage)
            for stage in self.stage_hierarchy
        }
    
    def identify_bottlenecks(self, threshold_percentile: float = 75) -> List[Tuple[str, float]]:
        """Identify stages with high latency."""
        bottlenecks = []
        
        for stage in self.stage_hierarchy:
            stats = self.get_stage_statistics(stage)
            if not stats:
                continue
            
            p75 = stats.get('p95_ms', 0)  # Use p95 as "slow" threshold
            if p75 > threshold_percentile:
                bottlenecks.append((stage, p75))
        
        return sorted(bottlenecks, key=lambda x: x[1], reverse=True)
    
    def generate_latency_report(self) -> Dict:
        """Generate comprehensive latency report."""
        total_samples = len(self.records)
        
        if total_samples == 0:
            return {'error': 'No latency data collected'}
        
        report = {
            'experiment': self.experiment_name,
            'timestamp': datetime.now().isoformat(),
            'total_samples': total_samples,
            'stages': self.get_pipeline_latencies(),
            'bottlenecks': [
                {'stage': s, 'p95_ms': l} for s, l in self.identify_bottlenecks()
            ],
        }
        
        # Add end-to-end statistics
        e2e_latencies = []
        for frame_id in self.frame_times:
            e2e = self.get_end_to_end_latency(frame_id)
            if e2e > 0:
                e2e_latencies.append(e2e)
        
        if e2e_latencies:
            import statistics
            report['end_to_end'] = {
                'mean_ms': round(statistics.mean(e2e_latencies), 3),
                'max_ms': round(max(e2e_latencies), 3),
                'min_ms': round(min(e2e_latencies), 3),
                'median_ms': round(statistics.median(e2e_latencies), 3),
            }
        
        return report
    
    def save_report(self, output_dir: str = "results") -> str:
        """Save latency report to JSON."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_path / f"latency_report_{self.experiment_name}_{timestamp}.json"
        
        try:
            report = self.generate_latency_report()
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            self.logger.info(f"Latency report saved: {report_path}")
            return str(report_path)
        except Exception as e:
            self.logger.error(f"Failed to save latency report: {e}")
            return ""
    
    def reset(self):
        """Reset all latency measurements."""
        self.stages.clear()
        self.records.clear()
        self.frame_times.clear()
        self.stats_cache.clear()
        self.stage_hierarchy.clear()


class LatencyContext:
    """Context manager for latency measurement."""
    
    def __init__(self, profiler: LatencyProfiler, stage_name: str, frame_id: int = 0):
        """Initialize context manager."""
        self.profiler = profiler
        self.stage_name = stage_name
        self.frame_id = frame_id
    
    def __enter__(self):
        """Start latency measurement."""
        self.profiler.start_stage(self.stage_name, self.frame_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End latency measurement."""
        status = "error" if exc_type else "success"
        self.profiler.end_stage(self.stage_name, self.frame_id, status)
        return False


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    profiler = LatencyProfiler(experiment_name="detection_pipeline")
    
    # Simulate pipeline stages
    for frame_id in range(10):
        # Stage 1: Signal acquisition
        with LatencyContext(profiler, "signal_acquisition", frame_id):
            time.sleep(0.005)  # 5ms
        
        # Stage 2: Signal processing
        with LatencyContext(profiler, "signal_processing", frame_id):
            time.sleep(0.010)  # 10ms
        
        # Stage 3: Detection
        with LatencyContext(profiler, "detection", frame_id):
            time.sleep(0.008)  # 8ms
        
        # Stage 4: Tracking
        with LatencyContext(profiler, "tracking", frame_id):
            time.sleep(0.003)  # 3ms
    
    # Generate report
    profiler.save_report()
    
    print(json.dumps(profiler.generate_latency_report(), indent=2))
