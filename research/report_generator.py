#!/usr/bin/env python3
"""
Automated Evaluation Report Generator
======================================

Comprehensive report generation for experimental results:
  - Parse metrics CSV and JSON files
  - Generate performance summaries
  - Create visualization-ready data
  - Produce markdown/HTML reports
  - Compare multiple experiments
  - Identify key findings and recommendations
"""

import json
import csv
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging


@dataclass
class ExperimentMetrics:
    """Aggregated metrics from an experiment."""
    experiment_name: str
    timestamp: str
    total_samples: int
    metrics: Dict
    thresholds: Dict = None


class ReportGenerator:
    """Generate comprehensive evaluation reports."""
    
    def __init__(self, output_dir: str = "results"):
        """Initialize report generator."""
        self.logger = logging.getLogger("ReportGenerator")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"ReportGenerator initialized: {output_dir}")
    
    def load_json_results(self, json_path: str) -> Dict:
        """Load results from JSON file."""
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load {json_path}: {e}")
            return {}
    
    def load_csv_results(self, csv_path: str) -> List[Dict]:
        """Load results from CSV file."""
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            self.logger.error(f"Failed to load {csv_path}: {e}")
            return []
    
    def analyze_benchmark_results(self, benchmark_json: str) -> Dict:
        """Analyze benchmark results from JSON file."""
        results = self.load_json_results(benchmark_json)
        
        if not results or 'error' in results:
            return {'error': 'Could not load benchmark results'}
        
        analysis = {
            'experiment': results.get('experiment'),
            'timestamp': results.get('timestamp'),
            'trial_count': results.get('num_trials', 0),
        }
        
        # Analyze throughput
        throughput_data = results.get('throughput', {})
        analysis['throughput_analysis'] = {
            'avg_fps': throughput_data.get('mean_fps'),
            'std_fps': throughput_data.get('std_fps'),
            'range_fps': f"{throughput_data.get('min_fps')}-{throughput_data.get('max_fps')}",
            'consistency': self._calculate_consistency(
                throughput_data.get('mean_fps', 1),
                throughput_data.get('std_fps', 0)
            ),
        }
        
        # Analyze latency
        latency_data = results.get('latency', {})
        analysis['latency_analysis'] = {
            'avg_ms': latency_data.get('mean_ms'),
            'std_ms': latency_data.get('std_ms'),
            'range_ms': f"{latency_data.get('min_ms')}-{latency_data.get('max_ms')}",
            'performance': self._categorize_latency(latency_data.get('mean_ms', 0)),
        }
        
        # Analyze accuracy
        accuracy_data = results.get('accuracy', {})
        analysis['accuracy_analysis'] = {
            'mean_accuracy': accuracy_data.get('mean'),
            'std_accuracy': accuracy_data.get('std'),
            'range': f"{accuracy_data.get('min')}-{accuracy_data.get('max')}",
            'quality': self._categorize_accuracy(accuracy_data.get('mean', 0)),
        }
        
        # Analyze resource usage
        resources = results.get('resources', {})
        analysis['resource_analysis'] = {
            'cpu_percent': resources.get('cpu_percent'),
            'cpu_category': self._categorize_cpu_usage(resources.get('cpu_percent', 0)),
            'memory_mb': resources.get('memory_mb'),
            'memory_category': self._categorize_memory(resources.get('memory_mb', 0)),
        }
        
        return analysis
    
    def analyze_noise_experiment(self, noise_json: str) -> Dict:
        """Analyze noise experiment results from JSON file."""
        results = self.load_json_results(noise_json)
        
        if not results or 'error' in results:
            return {'error': 'Could not load noise experiment results'}
        
        analysis = {
            'experiment': results.get('experiment'),
            'timestamp': results.get('timestamp'),
            'config': results.get('config', {}),
            'snr_range': results.get('snr_range'),
            'num_levels': results.get('num_snr_levels'),
            'thresholds': results.get('thresholds', {}),
        }
        
        # Analyze performance curves
        curves = results.get('performance_curves', {})
        if curves:
            snrs = curves.get('snr_db', [])
            det_rates = curves.get('detection_rate', [])
            
            analysis['detection_performance'] = {
                'min_snr_for_90_percent': self._find_threshold(snrs, det_rates, 0.90),
                'min_snr_for_80_percent': self._find_threshold(snrs, det_rates, 0.80),
                'best_detection_rate': max(det_rates) if det_rates else 0,
            }
            
            f1_scores = curves.get('f1_score', [])
            if f1_scores:
                max_f1_idx = f1_scores.index(max(f1_scores))
                analysis['optimal_operating_point'] = {
                    'snr_db': snrs[max_f1_idx] if max_f1_idx < len(snrs) else 0,
                    'f1_score': max(f1_scores),
                    'detection_rate': det_rates[max_f1_idx] if max_f1_idx < len(det_rates) else 0,
                }
        
        return analysis
    
    @staticmethod
    def _calculate_consistency(mean: float, std: float) -> str:
        """Categorize consistency from mean and std."""
        if mean == 0:
            return "unknown"
        cv = std / mean  # Coefficient of variation
        if cv < 0.05:
            return "excellent"
        elif cv < 0.10:
            return "good"
        elif cv < 0.20:
            return "fair"
        else:
            return "poor"
    
    @staticmethod
    def _categorize_latency(latency_ms: float) -> str:
        """Categorize latency performance."""
        if latency_ms < 5:
            return "excellent (near real-time)"
        elif latency_ms < 10:
            return "good (real-time)"
        elif latency_ms < 20:
            return "acceptable (near real-time)"
        elif latency_ms < 50:
            return "fair (not ideal for real-time)"
        else:
            return "poor (high latency)"
    
    @staticmethod
    def _categorize_accuracy(accuracy: float) -> str:
        """Categorize accuracy performance."""
        if accuracy >= 0.95:
            return "excellent"
        elif accuracy >= 0.90:
            return "very good"
        elif accuracy >= 0.80:
            return "good"
        elif accuracy >= 0.70:
            return "acceptable"
        else:
            return "poor"
    
    @staticmethod
    def _categorize_cpu_usage(cpu_percent: float) -> str:
        """Categorize CPU usage."""
        if cpu_percent < 25:
            return "light"
        elif cpu_percent < 50:
            return "moderate"
        elif cpu_percent < 75:
            return "heavy"
        else:
            return "critical"
    
    @staticmethod
    def _categorize_memory(memory_mb: float) -> str:
        """Categorize memory usage."""
        if memory_mb < 100:
            return "minimal"
        elif memory_mb < 500:
            return "light"
        elif memory_mb < 1000:
            return "moderate"
        elif memory_mb < 2000:
            return "substantial"
        else:
            return "heavy"
    
    @staticmethod
    def _find_threshold(snrs: List[float], values: List[float], target: float) -> Optional[float]:
        """Find SNR value where performance reaches target."""
        for snr, value in zip(snrs, values):
            if float(value) >= target:
                return snr
        return None
    
    def generate_markdown_report(self, benchmark_json: str, noise_json: str = None) -> str:
        """Generate comprehensive markdown report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = []
        
        report.append("# Evaluation Report\n")
        report.append(f"**Generated:** {datetime.now().isoformat()}\n\n")
        
        # Benchmark section
        report.append("## Benchmark Results\n")
        benchmark_analysis = self.analyze_benchmark_results(benchmark_json)
        
        if 'error' not in benchmark_analysis:
            report.append(f"**Experiment:** {benchmark_analysis.get('experiment')}\n")
            report.append(f"**Trials:** {benchmark_analysis.get('trial_count')}\n\n")
            
            # Throughput
            report.append("### Throughput Performance\n")
            tp = benchmark_analysis.get('throughput_analysis', {})
            report.append(f"- **Average:** {tp.get('avg_fps', 0):.2f} fps\n")
            report.append(f"- **Std Dev:** {tp.get('std_fps', 0):.2f} fps\n")
            report.append(f"- **Range:** {tp.get('range_fps')}\n")
            report.append(f"- **Consistency:** {tp.get('consistency')}\n\n")
            
            # Latency
            report.append("### Latency Performance\n")
            lat = benchmark_analysis.get('latency_analysis', {})
            report.append(f"- **Average:** {lat.get('avg_ms', 0):.3f} ms\n")
            report.append(f"- **Std Dev:** {lat.get('std_ms', 0):.3f} ms\n")
            report.append(f"- **Range:** {lat.get('range_ms')}\n")
            report.append(f"- **Category:** {lat.get('performance')}\n\n")
            
            # Accuracy
            report.append("### Accuracy Performance\n")
            acc = benchmark_analysis.get('accuracy_analysis', {})
            report.append(f"- **Mean:** {acc.get('mean_accuracy', 0):.4f}\n")
            report.append(f"- **Std Dev:** {acc.get('std_accuracy', 0):.4f}\n")
            report.append(f"- **Range:** {acc.get('range')}\n")
            report.append(f"- **Quality:** {acc.get('quality')}\n\n")
            
            # Resources
            report.append("### Resource Utilization\n")
            res = benchmark_analysis.get('resource_analysis', {})
            report.append(f"- **CPU:** {res.get('cpu_percent', 0):.2f}% ({res.get('cpu_category')})\n")
            report.append(f"- **Memory:** {res.get('memory_mb', 0):.2f} MB ({res.get('memory_category')})\n\n")
        else:
            report.append("*No benchmark data available*\n\n")
        
        # Noise experiment section
        if noise_json:
            report.append("## Noise Sensitivity Analysis\n")
            noise_analysis = self.analyze_noise_experiment(noise_json)
            
            if 'error' not in noise_analysis:
                report.append(f"**SNR Range:** {noise_analysis.get('snr_range')} dB\n")
                report.append(f"**Levels Tested:** {noise_analysis.get('num_levels')}\n\n")
                
                # Performance thresholds
                report.append("### Detection Performance Thresholds\n")
                det = noise_analysis.get('detection_performance', {})
                report.append(f"- **SNR for 80% Detection:** {det.get('min_snr_for_80_percent')} dB\n")
                report.append(f"- **SNR for 90% Detection:** {det.get('min_snr_for_90_percent')} dB\n")
                report.append(f"- **Best Detection Rate:** {det.get('best_detection_rate'):.2%}\n\n")
                
                # Optimal operating point
                report.append("### Optimal Operating Point\n")
                opt = noise_analysis.get('optimal_operating_point', {})
                report.append(f"- **Recommended SNR:** {opt.get('snr_db')} dB\n")
                report.append(f"- **F1 Score:** {opt.get('f1_score'):.4f}\n")
                report.append(f"- **Detection Rate:** {opt.get('detection_rate'):.2%}\n\n")
            else:
                report.append("*No noise experiment data available*\n\n")
        
        # Recommendations
        report.append("## Recommendations\n")
        report.append("1. Monitor latency consistency for production deployment\n")
        report.append("2. Validate accuracy across varied SNR conditions\n")
        report.append("3. Establish SNR thresholds for operational use\n")
        report.append("4. Scale resource capacity based on CPU/memory utilization\n\n")
        
        return "\n".join(report)
    
    def save_markdown_report(self, benchmark_json: str, noise_json: str = None) -> str:
        """Generate and save markdown report."""
        markdown = self.generate_markdown_report(benchmark_json, noise_json)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"evaluation_report_{timestamp}.md"
        
        with open(report_path, 'w') as f:
            f.write(markdown)
        
        self.logger.info(f"Markdown report saved: {report_path}")
        return str(report_path)
    
    def generate_comparison_report(self, experiments: Dict[str, Dict]) -> str:
        """Generate comparison report for multiple experiments."""
        report = []
        
        report.append("# Experiment Comparison Report\n")
        report.append(f"**Generated:** {datetime.now().isoformat()}\n\n")
        
        report.append("## Experiments Compared\n")
        report.append("| Experiment | Type | Key Metric | Result |\n")
        report.append("|---|---|---|---|\n")
        
        for exp_name, exp_data in experiments.items():
            exp_type = exp_data.get('type', 'unknown')
            metric = exp_data.get('key_metric', 'N/A')
            result = exp_data.get('result', 'N/A')
            report.append(f"| {exp_name} | {exp_type} | {metric} | {result} |\n")
        
        report.append("\n")
        return "\n".join(report)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    generator = ReportGenerator(output_dir="results")
    
    # Find example JSON files
    results_dir = Path("results")
    benchmark_files = list(results_dir.glob("benchmark_summary_*.json"))
    noise_files = list(results_dir.glob("noise_experiment_*.json"))
    
    if benchmark_files:
        benchmark_json = str(benchmark_files[0])
        noise_json = str(noise_files[0]) if noise_files else None
        
        # Generate and save report
        report_path = generator.save_markdown_report(benchmark_json, noise_json)
        print(f"Report saved to: {report_path}")
        
        # Also print to console
        report = generator.generate_markdown_report(benchmark_json, noise_json)
        print("\n" + report)
    else:
        print("No benchmark result files found in results directory")
