#!/usr/bin/env python3
"""
Research-Grade Metrics Logger
=============================

Logs simulation metrics to CSV for analysis and reproducibility.
Provides structured performance tracking for defense AI systems.

Features:
  - Real-time CSV logging
  - Automatic session tracking
  - Statistical computation
  - Performance aggregation
"""

import csv
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class SimulationMetrics:
    """Container for simulation performance metrics."""
    
    # Identifiers
    timestamp: str
    experiment_id: str
    trial_num: int = 0
    
    # Detection metrics
    detections_count: int = 0
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    
    # Performance metrics
    detection_latency_ms: float = 0.0  # milliseconds
    processing_time_ms: float = 0.0
    frame_rate: float = 0.0
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Accuracy metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    
    # Signal metrics
    snr_db: float = 0.0
    noise_power: float = 0.0
    signal_power: float = 0.0
    
    # Radar metrics
    azimuth_error_deg: float = 0.0
    range_error_m: float = 0.0
    velocity_error_mps: float = 0.0
    
    # System status
    system_healthy: bool = True
    errors: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class MetricsLogger:
    """Production-grade metrics logging system."""
    
    def __init__(self, output_dir: str = "results", experiment_name: str = "default"):
        """
        Initialize metrics logger.
        
        Args:
            output_dir: Directory to store CSV files
            experiment_name: Name of experiment for file prefixing
        """
        self.output_dir = Path(output_dir)
        self.experiment_name = experiment_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(f"MetricsLogger.{experiment_name}")
        
        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = self.output_dir / f"{experiment_name}_{self.session_id}.csv"
        self.summary_path = self.output_dir / f"{experiment_name}_{self.session_id}_summary.json"
        self.metrics_buffer: List[SimulationMetrics] = []
        
        # Statistics
        self.stats = {
            'total_frames': 0,
            'total_detections': 0,
            'avg_latency': 0.0,
            'max_latency': 0.0,
            'min_latency': float('inf'),
            'avg_accuracy': 0.0,
        }
        
        self._init_csv()
    
    def _init_csv(self):
        """Initialize CSV file with headers."""
        try:
            # Get field names from dataclass
            sample = SimulationMetrics(
                timestamp="",
                experiment_id="",
            )
            fieldnames = list(asdict(sample).keys())
            
            # Write header
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            
            self.logger.info(f"CSV initialized: {self.csv_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize CSV: {e}")
    
    def log_metrics(self, metrics: SimulationMetrics):
        """Log metrics to CSV and buffer."""
        try:
            # Add to buffer
            self.metrics_buffer.append(metrics)
            
            # Write to CSV
            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(metrics).keys())
                writer.writerow(asdict(metrics))
            
            # Update statistics
            self._update_stats(metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to log metrics: {e}")
    
    def _update_stats(self, metrics: SimulationMetrics):
        """Update running statistics."""
        self.stats['total_frames'] += 1
        self.stats['total_detections'] += metrics.detections_count
        
        if metrics.detection_latency_ms > 0:
            if self.stats['total_frames'] == 1:
                self.stats['avg_latency'] = metrics.detection_latency_ms
                self.stats['max_latency'] = metrics.detection_latency_ms
                self.stats['min_latency'] = metrics.detection_latency_ms
            else:
                self.stats['avg_latency'] = (
                    (self.stats['avg_latency'] * (self.stats['total_frames'] - 1) + 
                     metrics.detection_latency_ms) / self.stats['total_frames']
                )
                self.stats['max_latency'] = max(self.stats['max_latency'], 
                                               metrics.detection_latency_ms)
                self.stats['min_latency'] = min(self.stats['min_latency'], 
                                               metrics.detection_latency_ms)
        
        if metrics.accuracy > 0:
            self.stats['avg_accuracy'] = (
                (self.stats['avg_accuracy'] * (self.stats['total_frames'] - 1) + 
                 metrics.accuracy) / self.stats['total_frames']
            )
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary statistics for session."""
        return {
            'session_id': self.session_id,
            'experiment_name': self.experiment_name,
            'start_time': self.session_id,
            'end_time': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'total_frames_logged': self.stats['total_frames'],
            'total_detections': self.stats['total_detections'],
            'detection_latency': {
                'avg_ms': round(self.stats['avg_latency'], 2),
                'max_ms': round(self.stats['max_latency'], 2),
                'min_ms': round(self.stats['min_latency'], 2),
            },
            'accuracy': {
                'avg': round(self.stats['avg_accuracy'], 4),
            },
            'csv_file': str(self.csv_path),
        }
    
    def save_summary(self):
        """Save summary statistics to JSON."""
        try:
            summary = self.get_session_summary()
            with open(self.summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            self.logger.info(f"Summary saved: {self.summary_path}")
            return summary
        except Exception as e:
            self.logger.error(f"Failed to save summary: {e}")
            return {}
    
    def get_buffer_stats(self) -> Dict[str, Any]:
        """Get statistics from buffered metrics."""
        if not self.metrics_buffer:
            return {}
        
        latencies = [m.detection_latency_ms for m in self.metrics_buffer if m.detection_latency_ms > 0]
        accuracies = [m.accuracy for m in self.metrics_buffer if m.accuracy > 0]
        
        return {
            'buffer_size': len(self.metrics_buffer),
            'latency_stats': {
                'mean_ms': round(sum(latencies) / len(latencies), 2) if latencies else 0,
                'max_ms': round(max(latencies), 2) if latencies else 0,
                'min_ms': round(min(latencies), 2) if latencies else 0,
            },
            'accuracy_stats': {
                'mean': round(sum(accuracies) / len(accuracies), 4) if accuracies else 0,
                'max': round(max(accuracies), 4) if accuracies else 0,
                'min': round(min(accuracies), 4) if accuracies else 0,
            }
        }
    
    def export_metrics_to_json(self, filepath: Optional[str] = None) -> str:
        """Export all metrics to JSON."""
        if filepath is None:
            filepath = self.output_dir / f"{self.experiment_name}_{self.session_id}_metrics.json"
        
        try:
            data = {
                'session_id': self.session_id,
                'experiment': self.experiment_name,
                'metrics': [asdict(m) for m in self.metrics_buffer],
                'summary': self.get_session_summary(),
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Metrics exported to JSON: {filepath}")
            return str(filepath)
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
            return ""


class MetricsAnalyzer:
    """Analyze logged metrics from CSV files."""
    
    @staticmethod
    def load_metrics(csv_path: str) -> List[Dict[str, Any]]:
        """Load metrics from CSV file."""
        metrics = []
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    for key in row:
                        try:
                            if '.' in str(row[key]):
                                row[key] = float(row[key])
                            elif row[key].isdigit():
                                row[key] = int(row[key])
                        except (ValueError, AttributeError):
                            pass
                    metrics.append(row)
            return metrics
        except Exception as e:
            logging.error(f"Failed to load metrics from {csv_path}: {e}")
            return []
    
    @staticmethod
    def compute_statistics(metrics: List[Dict[str, Any]], field: str) -> Dict[str, float]:
        """Compute statistics for a field."""
        values = []
        for m in metrics:
            try:
                val = float(m.get(field, 0))
                if val > 0:
                    values.append(val)
            except (ValueError, TypeError):
                pass
        
        if not values:
            return {'mean': 0, 'std': 0, 'max': 0, 'min': 0}
        
        import statistics
        return {
            'mean': round(statistics.mean(values), 4),
            'std': round(statistics.stdev(values), 4) if len(values) > 1 else 0,
            'max': round(max(values), 4),
            'min': round(min(values), 4),
            'count': len(values),
        }
    
    @staticmethod
    def get_performance_report(csv_path: str) -> Dict[str, Any]:
        """Generate performance report from metrics."""
        metrics = MetricsAnalyzer.load_metrics(csv_path)
        
        if not metrics:
            return {}
        
        return {
            'total_samples': len(metrics),
            'latency_ms': MetricsAnalyzer.compute_statistics(metrics, 'detection_latency_ms'),
            'accuracy': MetricsAnalyzer.compute_statistics(metrics, 'accuracy'),
            'cpu_usage': MetricsAnalyzer.compute_statistics(metrics, 'cpu_usage_percent'),
            'memory_usage_mb': MetricsAnalyzer.compute_statistics(metrics, 'memory_usage_mb'),
        }


if __name__ == "__main__":
    # Example usage
    logger = MetricsLogger(output_dir="results", experiment_name="test_experiment")
    
    # Log sample metrics
    for i in range(5):
        metrics = SimulationMetrics(
            timestamp=datetime.now().isoformat(),
            experiment_id="test",
            trial_num=i,
            detections_count=2,
            true_positives=2,
            detection_latency_ms=15.5 + i,
            accuracy=0.95 + (i * 0.01),
        )
        logger.log_metrics(metrics)
    
    # Save summary
    logger.save_summary()
    
    # Print stats
    print("Buffer Statistics:", logger.get_buffer_stats())
    print("Session Summary:", logger.get_session_summary())
    print("CSV Path:", logger.csv_path)
