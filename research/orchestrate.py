#!/usr/bin/env python3
"""
Master Experiment Orchestrator
===============================

Coordinates comprehensive evaluation workflow:
1. Run performance benchmark
2. Execute noise sensitivity experiments
3. Generate latency profile
4. Produce evaluation reports
5. Save final summary

Integrates all research tools into single workflow.
"""

import sys
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Orchestrator")


class ExperimentOrchestrator:
    """Master coordinator for research experiments."""
    
    def __init__(self, config_path: str = None):
        """Initialize orchestrator."""
        self.config_path = config_path
        self.results = {}
        self.start_time = datetime.now()
        self.logger = logging.getLogger("ExperimentOrchestrator")
        self.logger.info("ExperimentOrchestrator initialized")
    
    def run_benchmark(self) -> Dict:
        """Execute performance benchmark."""
        self.logger.info("=" * 60)
        self.logger.info("STARTING BENCHMARK")
        self.logger.info("=" * 60)
        
        try:
            from benchmark import BenchmarkConfig, BenchmarkRunner
            
            config = BenchmarkConfig(
                experiment_name="orchestrated_benchmark",
                num_trials=50,
                target_frame_rate=10,
                num_targets=3,
                noise_level=0.1,
            )
            
            runner = BenchmarkRunner(config)
            summary = runner.run_benchmark(num_trials=3)
            
            self.logger.info(f"Benchmark completed: {summary}")
            self.results['benchmark'] = summary
            return summary
            
        except Exception as e:
            self.logger.error(f"Benchmark failed: {e}", exc_info=True)
            return {'error': str(e)}
    
    def run_noise_experiment(self) -> Dict:
        """Execute noise sensitivity experiments."""
        self.logger.info("=" * 60)
        self.logger.info("STARTING NOISE SENSITIVITY EXPERIMENT")
        self.logger.info("=" * 60)
        
        try:
            from noise_experiment import NoiseExperimentConfig, NoiseExperimentGenerator
            
            config = NoiseExperimentConfig(
                experiment_name="orchestrated_noise_exp",
                snr_db_range=(0.0, 20.0),
                snr_db_step=2.0,
                frames_per_snr=30,
                num_targets=3,
            )
            
            generator = NoiseExperimentGenerator(config)
            results = generator.run_sweep()
            
            summary = generator.generate_summary()
            self.logger.info(f"Noise experiment completed: {len(results)} SNR levels")
            
            self.results['noise_experiment'] = summary
            return summary
            
        except Exception as e:
            self.logger.error(f"Noise experiment failed: {e}", exc_info=True)
            return {'error': str(e)}
    
    def generate_reports(self) -> Dict:
        """Generate evaluation reports."""
        self.logger.info("=" * 60)
        self.logger.info("GENERATING REPORTS")
        self.logger.info("=" * 60)
        
        try:
            from report_generator import ReportGenerator
            
            generator = ReportGenerator()
            
            # Find latest benchmark and noise files
            results_path = Path("results")
            benchmark_files = sorted(results_path.glob("benchmark_summary_*.json"), 
                                    key=lambda x: x.stat().st_mtime, reverse=True)
            noise_files = sorted(results_path.glob("noise_experiment_*.json"),
                                key=lambda x: x.stat().st_mtime, reverse=True)
            
            if benchmark_files:
                benchmark_json = str(benchmark_files[0])
                noise_json = str(noise_files[0]) if noise_files else None
                
                # Generate and save report
                report_path = generator.save_markdown_report(benchmark_json, noise_json)
                self.logger.info(f"Report saved: {report_path}")
                
                # Also print preview
                report = generator.generate_markdown_report(benchmark_json, noise_json)
                self.logger.info("Report preview:\n" + report[:500] + "\n...")
                
                return {'report_path': str(report_path), 'status': 'success'}
            else:
                self.logger.warning("No benchmark files found for report generation")
                return {'error': 'No benchmark files found', 'status': 'failed'}
                
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}", exc_info=True)
            return {'error': str(e)}
    
    def save_orchestration_summary(self):
        """Save orchestration summary to JSON."""
        output_path = Path("results")
        output_path.mkdir(parents=True, exist_ok=True)
        
        end_time = datetime.now()
        duration_sec = (end_time - self.start_time).total_seconds()
        
        summary = {
            'orchestration_status': 'completed',
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_sec': duration_sec,
            'results': self.results,
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = output_path / f"orchestration_summary_{timestamp}.json"
        
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Orchestration summary saved: {summary_path}")
        return str(summary_path)
    
    def run_complete_workflow(self, steps: List[str] = None):
        """Run complete workflow."""
        if steps is None:
            steps = ['benchmark', 'noise', 'reports']
        
        self.logger.info("=" * 70)
        self.logger.info("STARTING COMPLETE EVALUATION WORKFLOW")
        self.logger.info("=" * 70)
        self.logger.info(f"Steps: {', '.join(steps)}")
        self.logger.info(f"Start time: {self.start_time.isoformat()}")
        
        # Run selected steps
        if 'benchmark' in steps:
            self.run_benchmark()
        
        if 'noise' in steps:
            self.run_noise_experiment()
        
        if 'reports' in steps or 'report' in steps:
            self.generate_reports()
        
        # Save summary
        summary_path = self.save_orchestration_summary()
        
        self.logger.info("=" * 70)
        self.logger.info("WORKFLOW COMPLETED")
        self.logger.info("=" * 70)
        self.logger.info(f"Summary: {summary_path}")
        
        return self.results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Research Experiment Orchestrator')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmark')
    parser.add_argument('--noise', action='store_true', help='Run noise experiment')
    parser.add_argument('--reports', action='store_true', help='Generate reports')
    parser.add_argument('--all', action='store_true', help='Run all experiments')
    parser.add_argument('--config', type=str, help='Config file path')
    
    args = parser.parse_args()
    
    # Determine which steps to run
    if args.all:
        steps = ['benchmark', 'noise', 'reports']
    else:
        steps = []
        if args.benchmark:
            steps.append('benchmark')
        if args.noise:
            steps.append('noise')
        if args.reports:
            steps.append('reports')
    
    # Default to all if nothing specified
    if not steps:
        steps = ['benchmark', 'noise', 'reports']
    
    # Run orchestrator
    orchestrator = ExperimentOrchestrator(args.config)
    results = orchestrator.run_complete_workflow(steps)
    
    # Print final summary
    print("\n" + "=" * 70)
    print("FINAL RESULTS SUMMARY")
    print("=" * 70)
    print(json.dumps(results, indent=2, default=str))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
