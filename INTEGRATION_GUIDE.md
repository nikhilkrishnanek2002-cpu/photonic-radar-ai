# Integration Guide
## Using Research Framework with Photonic Radar AI

This guide shows how to integrate the research-grade evaluation framework with your production radar detection system.

---

## 🔗 Integration Points

### 1. Detection Pipeline Integration

**File:** `photonic-radar-ai/main.py` (or your main detection loop)

```python
from research.latency_profiler import LatencyProfiler, LatencyContext
from research.metrics_logger import SimulationMetrics, MetricsLogger
from datetime import datetime

# Initialize profiler and logger
profiler = LatencyProfiler(experiment_name="production_run")
metrics_logger = MetricsLogger(
    output_dir="results",
    experiment_name="production_radar"
)

# In your detection loop:
for frame_id, signal in enumerate(incoming_signals):
    # Stage 1: Signal Acquisition
    with LatencyContext(profiler, "signal_acquisition", frame_id):
        acquired_signal = acquire_signal(signal)
    
    # Stage 2: Signal Processing
    with LatencyContext(profiler, "signal_processing", frame_id):
        processed = apply_filters(acquired_signal)
        fft_result = compute_fft(processed)
    
    # Stage 3: Detection
    with LatencyContext(profiler, "detection", frame_id):
        detections = detect_targets(fft_result)
    
    # Stage 4: Tracking
    with LatencyContext(profiler, "tracking", frame_id):
        tracked_targets = kalman_filter.update(detections)
    
    # Calculate metrics
    accuracy = evaluate_accuracy(tracked_targets, ground_truth)
    
    # Log metrics
    metrics = SimulationMetrics(
        timestamp=datetime.now().isoformat(),
        experiment_id="production_run",
        trial_num=frame_id,
        detections_count=len(tracked_targets),
        accuracy=accuracy,
        precision=calculate_precision(tracked_targets, ground_truth),
        recall=calculate_recall(tracked_targets, ground_truth),
        f1_score=calculate_f1(tracked_targets, ground_truth),
        frame_rate=10.0,  # Your actual frame rate
        cpu_usage_percent=get_cpu_usage(),
        memory_usage_mb=get_memory_usage(),
    )
    metrics_logger.log_metrics(metrics)
```

---

### 2. Benchmark Your System

After integration, benchmark your production system:

```bash
cd research
python benchmark.py --experiment-name "production_v1"
```

**Expected Results:**
```
Trial 0: 10.2 fps, 12.3ms avg latency, 0.89 accuracy
Trial 1: 10.1 fps, 12.1ms avg latency, 0.88 accuracy
Trial 2: 9.9 fps, 12.8ms avg latency, 0.89 accuracy
```

---

### 3. SNR Sensitivity Testing

Test detection performance across varying noise conditions:

```bash
cd research
python noise_experiment.py
```

**This generates:**
- Optimal SNR thresholds for deployment
- False alarm rates at different noise levels
- Recommended operating points

---

### 4. Continuous Performance Monitoring

Create a monitoring loop in production:

```python
# periodic_monitoring.py
import time
from research.metrics_logger import MetricsLogger
from pathlib import Path

class ProductionMonitor:
    def __init__(self):
        self.logger = MetricsLogger(
            output_dir="results",
            experiment_name="production_monitoring"
        )
        self.start_time = time.time()
    
    def check_performance(self, metrics):
        """Log metrics and alert if degraded."""
        # Log to CSV
        self.logger.log_metrics(metrics)
        
        # Check thresholds
        if metrics.frame_rate < 8.0:  # Below minimum
            print("WARNING: Throughput degradation")
        
        if metrics.detection_latency_ms > 20:  # High latency
            print("WARNING: Latency spike")
        
        # Every 1000 frames, generate report
        if metrics.trial_num % 1000 == 0:
            summary = self.logger.get_session_summary()
            print(f"Performance at {metrics.trial_num}:")
            print(f"  Avg latency: {summary['avg_latency_ms']:.2f} ms")
            print(f"  Avg accuracy: {summary['avg_accuracy']:.2%}")

# In your main loop:
monitor = ProductionMonitor()
for frame_id, signal in enumerate(signals):
    # ... detection code ...
    metrics = SimulationMetrics(...)
    monitor.check_performance(metrics)
```

---

### 5. Generate Performance Reports

After running experiments, generate comprehensive reports:

```bash
cd research
python report_generator.py
```

**Report includes:**
- Throughput analysis
- Latency characterization  
- Accuracy metrics
- Resource utilization
- Recommendations for optimization

---

## 🎯 Key Measurements

### What We Measure

```python
# Temporal metrics
detection_latency_ms        # End-to-end latency
frame_rate                  # Throughput (fps)
processing_time_ms          # Total processing

# Accuracy metrics
accuracy                    # (TP+TN)/(TP+TN+FP+FN)
precision                   # TP/(TP+FP)
recall                      # TP/(TP+FN)
f1_score                    # 2*(precision*recall)/(precision+recall)

# Detection quality
true_positives              # Correctly detected targets
false_positives             # Incorrectly detected targets
true_negatives              # Correctly rejected clutter
false_negatives             # Missed targets

# Resource metrics
cpu_usage_percent           # CPU utilization
memory_usage_mb             # Memory consumption

# Signal metrics
snr_db                      # Signal-to-noise ratio
noise_power                 # Estimated noise level
signal_power                # Estimated signal level

# Radar-specific
azimuth_error_deg           # Angle estimation error
range_error_m               # Distance estimation error
velocity_error_mps          # Speed estimation error
```

---

## 📊 Example: Complete Workflow

### Step 1: Baseline Benchmark
```bash
cd research
python benchmark.py --num-trials 100 --experiment-name baseline_v1
```

### Step 2: Noise Analysis
```bash
python noise_experiment.py --snr-range 0 30 --snr-step 2
```

### Step 3: Generate Report
```bash
python report_generator.py
cat ../results/evaluation_report_*.md
```

### Step 4: Review Recommendations
The report will recommend:
- Optimal SNR threshold for deployment
- CPU/memory allocation
- Acceptable latency bounds
- Performance targets

---

## 🔄 Continuous Integration

### Jenkins/GitHub Actions Integration

```yaml
# .github/workflows/benchmark.yml
name: Performance Benchmark
on: [push]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run benchmark
        run: cd research && python benchmark.py
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: benchmark-results
          path: results/
```

---

## 🐳 Docker Integration

### Running in Docker

```dockerfile
# Dockerfile.research
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY . .

# Run orchestrator
CMD ["python", "research/orchestrate.py", "--all"]
```

```bash
# Build and run
docker build -f Dockerfile.research -t photonic-radar:research .
docker run -v $(pwd)/results:/app/results photonic-radar:research
```

---

## 📈 Performance Targets

**Recommended Thresholds:**

```python
PERFORMANCE_TARGETS = {
    'throughput': {
        'minimum': 8.0,      # fps
        'target': 10.0,      # fps
        'optimal': 15.0,     # fps
    },
    'latency': {
        'maximum': 20.0,     # ms
        'target': 10.0,      # ms
        'optimal': 5.0,      # ms
    },
    'accuracy': {
        'minimum': 0.75,     # score
        'target': 0.85,      # score
        'optimal': 0.95,     # score
    },
    'resources': {
        'cpu_max': 80.0,     # percent
        'memory_max': 512.0, # MB
    }
}
```

---

## 🔧 Troubleshooting

### Issue: Import errors
```python
# Solution: Add to path
import sys
sys.path.insert(0, '/path/to/research')
```

### Issue: Metrics not appearing in CSV
```python
# Check path
from research.metrics_logger import MetricsLogger
logger = MetricsLogger()
print(logger.csv_path)
print(logger.output_dir)
```

### Issue: High latency spikes
```python
# Use latency profiler to identify bottleneck
profiler = LatencyProfiler()
stats = profiler.get_pipeline_latencies()
bottlenecks = profiler.identify_bottlenecks()
```

---

## 📊 Analysis Examples

### Finding Optimal SNR Threshold

```python
from research.noise_experiment import NoiseExperimentGenerator

generator = NoiseExperimentGenerator(config)
results = generator.run_sweep()

thresholds = generator.find_optimal_threshold()
print(f"Recommended SNR: {thresholds['recommended_snr_db']} dB")
print(f"90% Detection at: {thresholds['threshold_90_percent_detection']} dB")
```

### Identifying Performance Bottlenecks

```python
from research.latency_profiler import LatencyProfiler

profiler = LatencyProfiler()
# ... run detection pipeline ...

bottlenecks = profiler.identify_bottlenecks(threshold_percentile=75)
for stage, latency in bottlenecks:
    print(f"Bottleneck: {stage} - {latency:.2f} ms")
```

### Generating Comparison Reports

```python
from research.report_generator import ReportGenerator

generator = ReportGenerator()
comparison = generator.generate_comparison_report({
    'baseline': {'key_metric': 'latency', 'result': '12.3ms'},
    'optimized': {'key_metric': 'latency', 'result': '8.1ms'},
})
```

---

## 🎓 Next Steps

1. **Integrate latency profiling** into your detection pipeline
2. **Start collecting metrics** from your production system
3. **Run baseline benchmark** to establish performance baseline
4. **Execute noise experiments** to find optimal SNR thresholds
5. **Generate reports** to inform optimization efforts
6. **Monitor continuously** to track performance over time

---

## 📚 Related Documentation

- [Research Framework README](./research/README.md)
- [metrics_logger.py](./research/metrics_logger.py) - Detailed implementation
- [Benchmark Configuration](./configs/benchmark_config.yaml)
- [Master Experiment Config](./configs/master_experiment_config.yaml)

---

## 💡 Best Practices

1. **Always establish baseline** before optimization
2. **Use consistent configurations** across experiments
3. **Run multiple trials** to account for variability
4. **Monitor resource usage** for deployment planning
5. **Archive results** for historical comparison
6. **Automate experiments** for continuous monitoring
7. **Review reports regularly** to identify trends

---

## 🆘 Support

For issues or questions:
1. Check the research framework README
2. Review example scripts in each module
3. Check logs in `orchestrator.log`
4. Generate detailed reports for analysis
