# Quick Start Guide
## Research-Grade Evaluation Framework for Photonic Radar AI

Get started with performance benchmarking, latency profiling, and noise analysis in 5 minutes.

---

## ⚡ 30-Second Setup

```bash
# Navigate to research directory
cd research

# Install dependencies
pip install -r ../requirements.txt

# Run complete workflow
python orchestrate.py --all
```

**Done!** Results saved in `results/` directory.

---

## 🚀 Run Individual Experiments

### Benchmark (Throughput & Latency)
```bash
python benchmark.py
```
**Output:** `results/benchmark_summary_*.json`
- Throughput (fps)
- Latency (avg, p95, p99)
- Accuracy metrics
- Resource usage

### Noise Sensitivity (SNR Analysis)
```bash
python noise_experiment.py
```
**Output:** `results/noise_experiment_*.json`
- Detection rate vs SNR
- Optimal operating point
- SNR thresholds

### Generate Reports
```bash
python report_generator.py
```
**Output:** `results/evaluation_report_*.md`
- Comprehensive analysis
- Performance categorization
- Recommendations

---

## 📊 Interpret Results

### Benchmark Results

```json
{
  "throughput": {
    "mean_fps": 10.2,
    "std_fps": 0.3,
    "min_fps": 9.5,
    "max_fps": 10.8
  },
  "latency": {
    "mean_ms": 12.3,
    "std_ms": 1.2,
    "min_ms": 10.5,
    "max_ms": 15.2
  },
  "accuracy": {
    "mean": 0.88,
    "std": 0.02,
    "min": 0.84,
    "max": 0.91
  }
}
```

**What it means:**
- ✅ **10.2 fps average** - Good throughput
- ✅ **12.3 ms latency** - Acceptable real-time
- ✅ **88% accuracy** - Good detection quality

### Noise Experiment Results

```
SNR=0.0dB:  Det.Rate=52%, Prec=71%, F1=0.599, FAR=0.0450
SNR=5.0dB:  Det.Rate=72%, Prec=82%, F1=0.768, FAR=0.0180
SNR=10.0dB: Det.Rate=88%, Prec=91%, F1=0.894, FAR=0.0085
SNR=15.0dB: Det.Rate=95%, Prec=96%, F1=0.956, FAR=0.0025
```

**What it means:**
- ✅ **90% detection at 10 dB** - Reasonable operating point
- ✅ **Best F1 at 15 dB** - Maximum accuracy
- ✅ **Low false alarm rate** - Reliable detection

---

## 🎯 Common Workflows

### Workflow 1: Optimize Performance

```bash
# Run baseline
python benchmark.py --experiment-name baseline

# Modify code to optimize
# ... apply optimization ...

# Run optimized version
python benchmark.py --experiment-name optimized

# Compare results
python report_generator.py
```

### Workflow 2: Determine Safe Operating Range

```bash
# Run noise experiment
python noise_experiment.py

# Review optimal SNR thresholds
cat results/noise_experiment_*.json | grep recommended_snr_db
```

**Result:** Deploy with SNR > [recommended value]

### Workflow 3: Monitor Production System

```bash
# Integrate metrics logger in production
# (See INTEGRATION_GUIDE.md)

# Periodically run reports
python report_generator.py

# Check evaluation_report_*.md for trends
cat results/evaluation_report_*.md
```

---

## 📁 File Structure

```
research/
├── metrics_logger.py      # Core logging (use this!)
├── latency_profiler.py    # Timing measurement
├── benchmark.py           # Performance test
├── noise_experiment.py    # SNR sensitivity
├── report_generator.py    # Generate reports
├── orchestrate.py         # Run all tests
└── README.md              # Full documentation

results/
├── benchmark_summary_*.json
├── noise_experiment_*.json
├── latency_report_*.json
├── metrics_summary_*.json
├── evaluation_report_*.md
└── orchestration_summary_*.json

configs/
├── benchmark_config.yaml
├── noise_experiment_config.yaml
└── master_experiment_config.yaml
```

---

## 💻 Code Examples

### Example 1: Log Metrics

```python
from research.metrics_logger import SimulationMetrics, MetricsLogger

# Create logger
logger = MetricsLogger("results", "my_experiment")

# Log a measurement
metrics = SimulationMetrics(
    timestamp="2024-01-01T12:00:00",
    experiment_id="my_experiment",
    trial_num=1,
    accuracy=0.92,
    precision=0.89,
    recall=0.95,
    frame_rate=10.0,
)
logger.log_metrics(metrics)

# Get summary
summary = logger.get_session_summary()
print(summary)  # {'mean_latency_ms': ..., 'avg_accuracy': ...}
```

### Example 2: Measure Latency

```python
from research.latency_profiler import LatencyProfiler, LatencyContext

# Create profiler
profiler = LatencyProfiler()

# Measure a stage
with LatencyContext(profiler, "my_stage", frame_id=0):
    expensive_operation()

# Get statistics
stats = profiler.get_stage_statistics("my_stage")
print(stats)  # {'mean_ms': 15.3, 'p95_ms': 18.2, ...}

# Save report
profiler.save_report("results")
```

### Example 3: Run Benchmark

```python
from research.benchmark import BenchmarkConfig, BenchmarkRunner

# Configure
config = BenchmarkConfig(
    experiment_name="my_benchmark",
    num_trials=50,
)

# Run
runner = BenchmarkRunner(config)
summary = runner.run_benchmark(num_trials=3)
print(summary)  # Performance summary
```

### Example 4: Analyze SNR

```python
from research.noise_experiment import NoiseExperimentConfig, NoiseExperimentGenerator

# Configure
config = NoiseExperimentConfig(
    experiment_name="snr_sweep",
    snr_db_range=(0.0, 30.0),
    snr_db_step=2.0,
)

# Run sweep
generator = NoiseExperimentGenerator(config)
results = generator.run_sweep()

# Find thresholds
thresholds = generator.find_optimal_threshold()
print(f"Recommended SNR: {thresholds['recommended_snr_db']} dB")
```

---

## 📈 Performance Interpretation

| Metric | Excellent | Good | Acceptable | Poor |
|--------|-----------|------|-----------|------|
| **Throughput (fps)** | > 15 | 10-15 | 8-10 | < 8 |
| **Latency (ms)** | < 5 | 5-10 | 10-20 | > 20 |
| **Accuracy** | > 0.95 | 0.90-0.95 | 0.80-0.90 | < 0.80 |
| **CPU (%)** | < 25 | 25-50 | 50-75 | > 75 |
| **Memory (MB)** | < 100 | 100-250 | 250-500 | > 500 |

---

## 🔍 Troubleshooting

### Q: "ImportError: No module named metrics_logger"
**A:** Ensure you're in the research directory:
```bash
cd research
python benchmark.py
```

### Q: "No output files generated"
**A:** Check results directory exists:
```bash
mkdir -p results
python benchmark.py
```

### Q: "Metrics CSV is empty"
**A:** Verify metrics are being logged:
```python
logger = MetricsLogger("results", "test")
print(logger.csv_path)  # Check path
print(logger.output_dir)  # Check directory
```

### Q: "How do I compare two experiments?"
**A:** Use the report generator:
```python
from research.report_generator import ReportGenerator
gen = ReportGenerator()
report = gen.generate_comparison_report({
    'exp1': {...},
    'exp2': {...}
})
```

---

## 📊 Example Results

### Benchmark Output
```
BENCHMARK SUMMARY
====================
num_trials: 3

throughput:
  mean_fps: 10.2
  std_fps: 0.3
  min_fps: 9.5
  max_fps: 10.8

latency:
  mean_ms: 12.3
  std_ms: 1.2
  min_ms: 10.5
  max_ms: 15.2

accuracy:
  mean: 0.88
  std: 0.02
  min: 0.84
  max: 0.91

resources:
  cpu_percent: 32.5
  memory_mb: 245.0
```

### Noise Experiment Output
```
SNR=10.0dB: Det.Rate=88%, Prec=91%, F1=0.894
SNR=15.0dB: Det.Rate=95%, Prec=96%, F1=0.956
SNR=20.0dB: Det.Rate=98%, Prec=99%, F1=0.987

THRESHOLDS
====================
90% detection at: 10.0 dB
Max F1 at: 20.0 dB
Low false alarms at: 15.0 dB
Recommended: 15.0 dB
```

---

## 🎓 Next Steps

1. ✅ Run `python orchestrate.py --all` to see it in action
2. 📖 Read [INTEGRATION_GUIDE.md](../INTEGRATION_GUIDE.md) to integrate with your code
3. 📚 Read [research/README.md](./research/README.md) for detailed documentation
4. 🔧 Modify configs in `configs/` for your system
5. 📊 Generate custom reports with `report_generator.py`

---

## 🚀 Advanced Usage

See [research/README.md](./research/README.md) for:
- Custom latency profiling
- Multi-experiment comparison
- Configuration-driven workflows
- Production integration
- Docker deployment

---

## 📞 For Help

1. Check `research/README.md` for detailed docs
2. Review example code in each Python file
3. Check `orchestrator.log` for error messages
4. Run with `--help` flag for command options

---

## 🎯 Key Takeaways

✅ **metrics_logger.py** → Log your measurements to CSV
✅ **latency_profiler.py** → Measure latency per stage
✅ **benchmark.py** → Automated performance testing
✅ **noise_experiment.py** → SNR sensitivity analysis
✅ **report_generator.py** → Generate comprehensive reports
✅ **orchestrate.py** → Run complete workflow automatically

**Start with:** `python orchestrate.py --all`
**Integrate with:** See `INTEGRATION_GUIDE.md`
**Learn more:** See `research/README.md`
