# LoGraph-AI: GNN-Based Link Prediction for Microservice Architectures

**Paper-Aligned Implementation** | [See Paper](PAPER_ALIGNMENT.md)

Research paper: "Utilizing Graph Neural Networks for Effective Link Prediction in Microservice Architectures" (ICPE 2025)

---

## 🎯 Core Features (Paper-Aligned)

### Data Pipeline (Sections 3.2-3.3)

#### 1. **Data Cleaning Phase (DCP)** → `graph_builder.py`
- Loads RPC maps: `data/*_ms_rpc_map.csv`
- Removes noisy/incomplete records
- Normalizes service names to canonical identifiers

#### 2. **Node Mapping Policy (NMP)** → `graph_builder.py::normalize_service_name()`
- Maps raw trace labels → graph node IDs
- Handles parentheses, underscores in service names
- Ensures consistent node representation

#### 3. **Time Window Adjustment (TWA)** → `lograph_tool/time_windows.py` ✨ NEW
- Segments events into fixed time intervals (default: 100ms windows)
- Paper Eq. 4: Tw = {Twj | Twj = {(f(si), f(di), ti) ∈ Tmap | ti ∈ wj}}
- Captures temporal evolution of microservice interactions
- Supports train/test split based on timestamp cutoff

#### 4. **Graph Construction** → `gnn-service/graph_builder.py`
- Builds directed ServiceGraph with weighted edges
- Paper: V = {nodes}, E = {(vs, vd) | edges with weights}
- Integration with CPU metrics for enriched features

---

### Model Architecture (Sections 3.4-3.5)

#### 5. **Advanced Negative Sampling (ANS)** → `lograph_tool/negative_sampling.py` ✨ NEW
- **Advanced Strategy**: Degree-weighted sampling
  - Paper Eq. 6: p(v) = dv^α / Σ(du^α)
  - Prioritizes connections from high-degree (hub) nodes
  - Reduces class imbalance from sparse positive edges
- **Simple Strategy**: Uniform random sampling (fallback)
- **No Sampling**: Option for balanced datasets

#### 6. **Graph Attention Network (GAT)** → `lograph_tool/gat_model.py` ✨ NEW
- **Two-Layer Architecture**:
  - Layer 1: 2-head attention with ELU activation
  - Layer 2: 1-head attention for consolidation
- **Attention Mechanism** (Paper Eq. 7-9):
  - Multi-head attention: αij = exp(LeakyReLU(a^T[Whi||Whj])) / Σk...
  - Feature aggregation: h'i = σ(Σj∈N(i) αij W hj)
- **Output**: Link probability via dot product + sigmoid

#### 7. **Training Framework** → `gnn-service/gat_trainer.py` ✨ NEW
- **Loss Function** (Paper Eq. 10):
  - Binary Cross-Entropy: L = -1/(|P|+|N|) * [Σlog(ŷuv) + Σlog(1-ŷuv)]
- **Link Prediction** (Paper Eq. 11-12):
  - sij = h^T_i · h_j
  - pij = σ(sij)
- **Threshold Optimization**:
  - Balances precision and recall
  - Automatic Best threshold search

---

### Evaluation & Visualization (Sections 4.2-4.3)

#### 8. **Metrics** → `lograph_tool/evaluation.py` ✨ NEW
- **Performance** (Table 1):
  - ✅ AUC (Area Under ROC Curve)
  - ✅ Accuracy
  - ✅ Precision
  - ✅ Recall
  - ✅ F1 Score
- **Interpretability**:
  - ✅ Confusion Matrix
  - ✅ ROC Curves (FPR vs TPR)
  - ✅ Precision-Recall Curves
  - ✅ Attention Heatmaps (weight evolution)

**Paper Target Performance**: AUC=0.89, F1=0.92, Precision=0.89, Recall=0.96

---

## 🌟 Additional Features (Beyond Paper)

### Real-Time Operational Capabilities

#### **CPU Metrics Integration** → `gnn-service/feature_extractor.py`
- Extracts actual system metrics: `cpu_last`, `cpu_mean`, `cpu_rate`
- Creates rich 13-dimensional node features (vs paper's 4-dimensional)
- Real performance data enriches predictions
- Files: `data/*_container_cpu_usage_seconds_total`

#### **OpenTelemetry Integration** → `lograph_tool/otel_ingest.py`
- Parses OTLP JSON logs from live services
- Dynamic event ingestion in addition to static batch data
- Extracts: service.name, peer.service, timestamps, RPC details
- Supports HTTP endpoints and JSONL file streams

#### **Deployment & Automation** → `lograph.py`

```bash
# One-shot training on snapshot data
python lograph.py run

# Continuous monitoring with periodic retraining
python lograph.py monitor

# Interactive GUI control panel
python lograph.py gui

# Initialize configuration
python lograph.py init
```

**Config**: `lograph-tool.json`
- `telemetry.mode`: jsonl or http
- `telemetry.endpoint`: OTel endpoint URL
- `model.algorithm`: gat | baseline
- `model.time_window_ms`: 100 (TWA parameter)
- `model.negative_sampling`: "advanced" | "simple" | "none"
- `actions`: Trigger rules and executable commands on detected anomalies

#### **FastAPI Backend** → `backend/main.py`
- `/prepare-graph`: Prepare and return graph statistics
- `/upload`: Upload RPC maps and metric files
- `/train`: Train model with configurable settings
- `/predict`: Predict links between service pairs
- `/preview`: Web UI with model visualization

#### **Baseline Comparison** → `gnn-service/model_trainer.py`
- Simple logistic regression for performance comparison
- Useful for validating GAT improvements
- Lightweight for rapid experimentation

#### **Message-Passing Embedded Baseline** → `lograph_tool/graph_model.py`
- Custom GNN-like aggregation (configurable weights)
- Self-weight: 0.7, Neighbor-weight: 0.3 (tunable)
- Quick baseline without neural network overhead

---

## 📊 Project Structure

```
lograph-tool/
├── time_windows.py          # TWA implementation (NEW)
├── negative_sampling.py       # ANS implementations (NEW)
├── gat_model.py             # GAT architecture (NEW)
├── evaluation.py            # Metrics & visualization (NEW)
├── otel_ingest.py          # OpenTelemetry integration
├── graph_model.py           # Baseline GNN approach
├── config.py               # Configuration management
├── cli.py                  # Command-line interface
├── gui.py                  # Web GUI
└── automation.py           # Action execution

gnn-service/
├── gat_trainer.py          # Paper-aligned training (NEW)
├── graph_builder.py        # Graph construction + NMP
├── feature_extractor.py    # CPU metrics loading
├── main.py                 # Pipeline orchestration
├── model_trainer.py        # Baseline trainer
└── ui_preview.py           # Web preview UI

backend/
├── main.py                 # FastAPI endpoints
└── requirements.txt

data/
├── *_ms_rpc_map.csv       # RPC interaction maps
├── *_container_cpu_usage_seconds_total  # CPU metrics
├── sample.csv              # Sample RPC data
└── otel_logs.jsonl         # OTel trace logs

models/
├── lograph_tool_model.json      # Saved GAT model
└── link_predictor_baseline.json  # Baseline model
```

---

## 🚀 Quick Start

### 1. Initialize Configuration
```bash
python lograph.py init
```

### 2. One-Shot Training (Batch Data)
```bash
# Trains GAT on all RPC maps in data/ directory
python lograph.py run
```

### 3. Continuous Monitoring (Real-Time)
```bash
# Fetches OTEL logs, trains periodically, checks for anomalies
python lograph.py monitor
```

### 4. Web Interface
```bash
# Open GUI at http://localhost:8000
python lograph.py gui
```

### 5. Using Backend API
```bash
# Terminal 1: Start FastAPI server
cd backend && python -m uvicorn main:app --reload

# Terminal 2: Upload data and predict
curl -X POST http://localhost:8000/upload \
  -F "rpc_maps=@data/compose_ms_rpc_map.csv" \
  -F "metrics_dir=@data/"

curl -X POST http://localhost:8000/train \
  -H "Content-Type: application/json" \
  -d '{"sampling_strategy": "advanced", "time_window_ms": 100}'

curl -X GET http://localhost:8000/predict?src=service-a&dst=service-b
```

---

## 📋 Configuration Example

```json
{
  "telemetry": {
    "mode": "http",
    "endpoint": "http://localhost:4318/v1/logs",
    "jsonl_path": "data/otel_logs.jsonl"
  },
  "model": {
    "algorithm": "gat",
    "time_window_ms": 100,
    "gat_hidden_dim": 32,
    "negative_sampling": "advanced",
    "negative_sampling_alpha": 0.1,
    "evaluation_metrics": ["auc", "f1", "precision", "recall"]
  },
  "actions": [
    {
      "name": "low_link_probability",
      "condition": "probability < 0.3",
      "trigger": "echo Alert: Missing critical link {src}->{dst}",
      "timeout_ms": 5000
    }
  ]
}
```

---

## 🧪 Training Example

```python
from lograph_tool.time_windows import create_fixed_windows, segment_events_by_windows
from lograph_tool.otel_ingest import fetch_from_otel_http
from gnn_service.gat_trainer import train_gat_model, TrainingConfig

# 1. Fetch OTel logs (or load batch data)
events = fetch_from_otel_http("http://localhost:4318/v1/logs")

# 2. Segment into time windows (TWA)
min_ts = min(e.timestamp for e in events)
max_ts = max(e.timestamp for e in events)
windows = create_fixed_windows(min_ts, max_ts, window_size_ms=100)
windowed = segment_events_by_windows(events, windows)

# 3. Train GAT with advanced negative sampling
config = TrainingConfig(
    negative_sampling_alpha=0.1,
    sampling_strategy="advanced",
    gat_hidden_dim=32,
    threshold_metric="f1",
)
result = train_gat_model(windowed, config)

print(f"F1 Score: {result.metrics['f1_score']:.4f}")
print(f"AUC: {result.metrics['auc']:.4f}")
print(f"Threshold: {result.threshold:.3f}")
```

---

## 📈 Expected Performance

Based on paper results on Alibaba microservice traces:

| Metric | Target | Notes |
|--------|--------|-------|
| **AUC** | 0.89 | Area under ROC curve |
| **F1 Score** | 0.92 | Harmonic mean of precision & recall |
| **Precision** | 0.89 | True positive rate among predictions |
| **Recall** | 0.96 | Coverage of actual positive links |
| **Accuracy** | 0.91 | Overall correctness |

Your implementation should achieve these with:
- Temporal segmentation (TWA) capturing evolving patterns
- Advanced negative sampling (ANS) handling class imbalance
- GAT attention mechanisms learning importance of connections
- CPU metrics providing operational context

---

## 🔗 Integration Points

### With Existing LoGraph Features
✅ **Preserved from Original**:
- FastAPI backend and web UI
- CSV upload and GraphML export
- CLI monitoring interface
- Config file management
- Action automation

✨ **Enhanced with Paper**:
- Time window-based training (vs. snapshot-only)
- GAT neural network (vs. logistic regression)
- Advanced negative sampling (vs. uniform)
- Comprehensive evaluation metrics
- Attention weight visualization

### Data Flow
```
[OTEL HTTP] or [RPC CSV] 
    ↓
[Data Cleaning - DCP]
    ↓
[Node Mapping - NMP]
    ↓
[Time Windows - TWA] ← NEW
    ↓
[Feature Extraction + CPU Metrics]
    ↓
[Advanced Sampling - ANS] ← NEW
    ↓
[GAT Model Training] ← NEW
    ↓
[Evaluation & Metrics] ← NEW
    ↓
[Predictions + Visualization]
```

---

## 📚 References

- Paper: arxiv version [2501.15019](https://arxiv.org/abs/2501.15019)
- Dataset: Alibaba 2022 Cluster Trace (20K microservices, 13-day trace)
- Framework Equations: See [PAPER_ALIGNMENT.md](PAPER_ALIGNMENT.md) for detailed references

---

## 🛠️ Development

Run tests:
```bash
python -m pytest tests/ -v
```

Check alignment with paper:
```bash
# See PAPER_ALIGNMENT.md verification checklist
```

Future enhancements:
- [ ] Torch/TensorFlow GAT for GPU acceleration
- [ ] Multi-graph temporal attention (TGAT variant)
- [ ] Anomaly detection triggers on low-probability links
- [ ] Online learning with streaming data
- [ ] Distributed training support