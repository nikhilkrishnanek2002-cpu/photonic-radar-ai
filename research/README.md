# Research-Grade Evaluation Framework
## Photonic Radar AI - Performance Benchmarking & Analysis

Comprehensive evaluation suite for production-grade radar detection system benchmarking, latency profiling, noise sensitivity analysis, and automated report generation.

---

## 📋 Overview

This framework provides research-grade tools for:
- **Performance Benchmarking** - Throughput, latency, accuracy measurement
- **Latency Profiling** - Stage-by-stage pipeline latency analysis
- **Noise Experiments** - SNR sensitivity and optimal threshold discovery
- **Report Generation** - Automated analysis and recommendations

**Key Features:**
- CSV-based metrics logging with real-time statistics
- End-to-end and per-stage latency measurement
- SNR sweep experiments with accuracy curves
- Comprehensive markdown reports
- Configuration-driven workflow
- Reproducible results with session tracking

---

## 🗂️ Project Structure

```
research/
├── metrics_logger.py         # Core metrics logging (290+ lines)
├── latency_profiler.py       # Pipeline latency measurement
├── benchmark.py              # Performance benchmarking script
├── noise_experiment.py        # SNR sensitivity experiments
├── report_generator.py        # Automated report generation
└── README.md                 # This file

configs/
├── benchmark_config.yaml      # Benchmark parameters
├── noise_experiment_config.yaml  # Noise experiment setup
└── master_experiment_config.yaml # End-to-end orchestration

results/
├── *.csv                      # Metrics data
├── *.json                     # Summary statistics
└── *.md                       # Generated reports

experiments/
└── *.yaml                     # Experiment definitions
```

---

## 🚀 Quick Start

### 1. Basic Benchmarking

```bash
cd research
python benchmark.py
```

**Output:**
- `results/benchmark_summary_*.json` - Performance summary
- `results/benchmark_trials_*.json` - Per-trial details
- `results/metrics_summary_*.json` - Aggregated metrics
- CSV with raw data for analysis

### 2. Noise Sensitivity Analysis

```bash
python noise_experiment.py
```

**Output:**
- `results/noise_experiment_*.json` - SNR vs accuracy curves
- `results/noise_experiment_*.csv` - Tabular results
- Detection rate, precision, recall at each SNR level
- Optimal operating point discovery

### 3. Latency Profiling

Automatically integrated with benchmarking and noise experiments.

**Profiles:**
- Signal acquisition latency
- Signal processing latency
- Detection latency
- Tracking latency
- End-to-end latency

### 4. Generate Reports

```bash
python report_generator.py
```

**Output:**
- `results/evaluation_report_*.md` - Comprehensive analysis
- Performance analysis
- Recommendations
- Comparison across experiments

---

## 📊 Core Components

### metrics_logger.py

**Purpose:** Production-grade metrics logging to CSV with real-time statistics

**Classes:**
- `SimulationMetrics` - Dataclass with 20+ metric fields
- `MetricsLogger` - Write to CSV, track statistics, export JSON
- `MetricsAnalyzer` - Load, analyze, generate reports

**Key Methods:**
```python
# Log a single measurement
metrics = SimulationMetrics(...)
logger.log_metrics(metrics)

# Get session statistics
summary = logger.get_session_summary()
# Returns: mean/max latency, average accuracy, etc.

# Export results
logger.export_metrics_to_json()
logger.save_summary()
```

**Metric Fields:**
- Detection: count, TP/FP/TN/FN
- Performance: latency, processing time, frame rate, CPU%, memory
- Accuracy: accuracy, precision, recall, F1 score
- Signal: SNR (dB), noise power, signal power
- Radar: azimuth/range/velocity errors
- Status: system health, errors

---

### latency_profiler.py

**Purpose:** Measure latency across pipeline stages

**Classes:**
- `LatencyProfiler` - Track stage-level timing
- `LatencyContext` - Context manager for automatic measurement

**Usage:**
```python
profiler = LatencyProfiler()

for frame_id in range(100):
    # Automatic timing with context manager
    with LatencyContext(profiler, "stage_name", frame_id):
        do_work()

# Get statistics
stats = profiler.get_stage_statistics("stage_name")
# Returns: mean, std, min, max, p50, p95, p99

# Identify bottlenecks
bottlenecks = profiler.identify_bottlenecks(threshold_percentile=75)

# Generate report
report = profiler.generate_latency_report()
profiler.save_report("results")
```

**Output:**
- JSON report with per-stage percentiles (p50, p95, p99)
- Bottleneck identification
- End-to-end latency statistics

---

### benchmark.py

**Purpose:** Comprehensive performance benchmarking

**Classes:**
- `BenchmarkConfig` - Configuration dataclass
- `BenchmarkRunner` - Execute benchmark trials

**Usage:**
```python
from benchmark import BenchmarkConfig, BenchmarkRunner

config = BenchmarkConfig(
    experiment_name="production_test",
    num_trials=100,
    target_frame_rate=10,
)

runner = BenchmarkRunner(config)
summary = runner.run_benchmark(num_trials=5)
```

**Metrics Collected:**
- Throughput (frames/sec)
- Latency (avg, p95, p99)
- Accuracy, precision, recall, F1 score
- CPU usage, memory usage
- TP/FP/TN/FN counts

**Output Files:**
- `benchmark_summary_*.json` - Performance summary
- `benchmark_trials_*.json` - Per-trial details
- `metrics_summary_*.json` - Aggregated stats
- `latency_report_*.json` - Per-stage latency

---

### noise_experiment.py

**Purpose:** SNR sensitivity analysis and threshold discovery

**Classes:**
- `NoiseExperimentConfig` - Configuration with SNR range
- `NoiseExperimentGenerator` - Run SNR sweep

**Usage:**
```python
from noise_experiment import NoiseExperimentConfig, NoiseExperimentGenerator

config = NoiseExperimentConfig(
    experiment_name="snr_sweep",
    snr_db_range=(0.0, 30.0),
    snr_db_step=2.0,
    frames_per_snr=50,
)

generator = NoiseExperimentGenerator(config)
results = generator.run_sweep()

# Find optimal SNR
thresholds = generator.find_optimal_threshold()
# Returns: 90% detection SNR, optimal F1 SNR, low false alarm SNR
```

**Outputs:**
- Performance vs SNR curves
- Optimal operating point
- Detection rate thresholds
- False alarm rate analysis

**Generated:**
- `noise_experiment_*.json` - Full results with curves
- `noise_experiment_*.csv` - Tabular format

---

### report_generator.py

**Purpose:** Automated analysis and reporting

**Classes:**
- `ReportGenerator` - Parse results and generate reports

**Usage:**
```python
from report_generator import ReportGenerator

generator = ReportGenerator()

# Analyze benchmark results
benchmark_analysis = generator.analyze_benchmark_results("results/benchmark_summary_*.json")

# Analyze noise experiment
noise_analysis = generator.analyze_noise_experiment("results/noise_experiment_*.json")

# Generate markdown report
report_path = generator.save_markdown_report(
    "results/benchmark_summary_*.json",
    "results/noise_experiment_*.json"
)
```

**Report Includes:**
- Throughput analysis (mean, std, consistency)
- Latency performance (categorization)
- Accuracy metrics
- Resource utilization
- SNR thresholds
- Recommendations

---

## ⚙️ Configuration Files

### benchmark_config.yaml
Controls benchmarking behavior:
- Trial count and duration
- Target frame rate
- Number of targets
- Performance thresholds
- Pipeline stages to profile

### noise_experiment_config.yaml
Configures SNR sweep:
- SNR range and step size
- Frames per SNR level
- Target detection probability
- False alarm rate
- Analysis parameters

### master_experiment_config.yaml
Orchestrates complete workflow:
- Experiment schedule
- Dependencies between tests
- Evaluation criteria (PASS/FAIL thresholds)
- Reporting configuration
- Recovery settings

---

## 📈 Performance Metrics

### Throughput Metrics
- **fps** - Frames processed per second
- **consistency** - Coefficient of variation (lower = better)

### Latency Metrics
- **mean_ms** - Average latency
- **p95_ms** - 95th percentile latency
- **p99_ms** - 99th percentile latency
- **bottlenecks** - Stages with highest latency

### Accuracy Metrics
- **accuracy** - (TP + TN) / Total
- **precision** - TP / (TP + FP)
- **recall** - TP / (TP + FN)
- **f1_score** - Harmonic mean of precision/recall

### Resource Metrics
- **cpu_percent** - CPU utilization
- **memory_mb** - Memory usage in MB

---

## 🔍 Example Workflow

### 1. Run Baseline Benchmark
```bash
python benchmark.py
# Statistics at 10 fps, 100 trials
```

### 2. Analyze SNR Sensitivity
```bash
python noise_experiment.py
# SNR from 0-30 dB in 2 dB steps
```

### 3. Generate Report
```bash
python report_generator.py
# Analyzes both experiments, creates markdown report
```

### Output Summary
```
BENCHMARK SUMMARY
====================
Throughput: 10.2 ± 0.3 fps
Latency:    12.5 ± 1.2 ms
Accuracy:   0.88 ± 0.02
CPU:        32.5%
Memory:     245 MB

NOISE ANALYSIS
====================
SNR for 90% detection: 8.5 dB
Optimal F1 SNR: 10.2 dB
Maximum F1: 0.89
```

---

## 🧪 Advanced Usage

### Custom Metrics Logging
```python
from research.metrics_logger import SimulationMetrics, MetricsLogger

logger = MetricsLogger("results", "custom_experiment")

# Log custom metrics
metrics = SimulationMetrics(
    timestamp="2024-01-01T12:00:00",
    experiment_id="custom_exp",
    trial_num=1,
    accuracy=0.92,
    # ... other fields
)
logger.log_metrics(metrics)

# Export results
summary = logger.get_session_summary()
logger.export_metrics_to_json()
```

### Latency Context Manager
```python
from research.latency_profiler import LatencyProfiler, LatencyContext

profiler = LatencyProfiler()

with LatencyContext(profiler, "my_stage", frame_id=0):
    # Automatically measures duration
    expensive_operation()

# Get detailed stats
stats = profiler.get_stage_statistics("my_stage")
print(stats)  # {'mean_ms': 15.3, 'p95_ms': 18.2, ...}
```

### Multi-Trial Benchmarking
```python
runner = BenchmarkRunner(config)

# Run multiple trials
for trial_id in range(10):
    result = runner.run_single_trial(trial_id)
    print(f"Trial {trial_id}: {result.throughput_fps:.1f} fps")

# Generate summary across trials
summary = runner.generate_summary()
runner.save_results()
```

---

## 📝 Output Formats

### CSV Files
- **metrics_*.csv** - Raw metrics with all fields
- **noise_experiment_*.csv** - SNR vs accuracy data
- **benchmark_trials_*.csv** - Per-trial performance

Each CSV includes:
- Timestamp
- Experiment/trial ID
- All metric values
- Status indicators

### JSON Files
- **benchmark_summary_*.json** - Aggregated statistics
- **noise_experiment_*.json** - Full results with curves
- **latency_report_*.json** - Per-stage latency percentiles
- **metrics_summary_*.json** - Session summary statistics

### Markdown Reports
- **evaluation_report_*.md** - Comprehensive analysis
- Sections for each experiment type
- Performance categorization
- Recommendations

---

## 🔧 Troubleshooting

### ImportError: No module named metrics_logger
**Solution:** Ensure all research files are in the same directory or add to Python path:
```python
import sys
sys.path.insert(0, '/path/to/research')
```

### No output files generated
**Solution:** Check results directory permissions:
```bash
mkdir -p results
chmod 755 results
```

### Metrics not logging
**Solution:** Verify MetricsLogger initialization:
```python
logger = MetricsLogger(output_dir="results", experiment_name="test")
print(logger.csv_path)  # Check path
```

---

## 📚 Integration with Production System

### Step 1: Add to Pipeline
```python
from research.latency_profiler import LatencyContext

# In detection pipeline
with LatencyContext(profiler, "detection_stage", frame_id):
    detections = detector.process(signal)
```

### Step 2: Collect Metrics
```python
from research.metrics_logger import SimulationMetrics

metrics = SimulationMetrics(
    timestamp=datetime.now().isoformat(),
    experiment_id="production_run",
    trial_num=frame_id,
    accuracy=calculate_accuracy(detections),
    # ... populate other fields
)
logger.log_metrics(metrics)
```

### Step 3: Generate Reports
```python
# Periodically run report generation
python research/report_generator.py

# Review results
cat results/evaluation_report_*.md
```

---

## 📊 Performance Targets

**Recommended Thresholds:**

| Metric | Target | Acceptable | Critical |
|--------|--------|-----------|----------|
| Throughput | > 10 fps | > 8 fps | < 5 fps |
| Latency | < 10 ms | < 20 ms | > 50 ms |
| Accuracy | > 0.90 | > 0.80 | < 0.70 |
| CPU | < 50% | < 75% | > 90% |
| Memory | < 256 MB | < 512 MB | > 1 GB |

---

## 📄 License & Citation

Part of the Photonic Radar AI research stack.

For questions or contributions, refer to project documentation.

---

## 🔗 Related Files

- [metrics_logger.py](metrics_logger.py) - Core logging framework
- [latency_profiler.py](latency_profiler.py) - Timing analysis
- [benchmark.py](benchmark.py) - Performance benchmarking
- [noise_experiment.py](noise_experiment.py) - SNR analysis
- [report_generator.py](report_generator.py) - Report generation
- [../configs/](../configs/) - Configuration files
