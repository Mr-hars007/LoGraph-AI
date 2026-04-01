# LoGraph-AI

Day 1 Progress(Mr-hars007):
- FastAPI backend setup
- File upload endpoint
- CSV to graph conversion using NetworkX

Current GNN-Service Pipeline (Harsha):
- File: gnn-service/graph_builder.py
	- Loads real RPC maps like data/compose_ms_rpc_map.csv
	- Normalizes raw trace labels to canonical service names
	- Builds directed interaction graph with call_count edge weights
- File: gnn-service/feature_extractor.py
	- Loads CPU metric files named *_container_cpu_usage_seconds_total
	- Computes node features: cpu_last, cpu_mean, cpu_rate
	- Attaches features to graph nodes with safe defaults for missing metrics
- File: gnn-service/main.py
	- Combines graph + features into GNN-ready structures:
		- node_to_index map
		- edge_index as [2, E]
		- node_features as [N, 3]

Run from project root:
- python gnn-service/main.py

Backend integration update:
- New endpoint: GET /prepare-graph
	- Runs gnn-service pipeline on selected RPC map + metrics directory
	- Returns graph stats, edge count, feature dimension, and sample nodes

Environment setup:
- Backend deps: pip install -r backend/requirements.txt
- GNN deps: pip install -r gnn-service/requirements.txt

Temporary model trainer (current iteration):
- File: gnn-service/model_trainer.py
	- Trains a lightweight baseline link predictor on current graph data
	- Automatically uses all data/*_ms_rpc_map.csv files and data/sample.csv if present
	- Uses balanced positive/negative edge samples
	- Exports model artifact to models/link_predictor_baseline.json

Run trainer:
- python gnn-service/model_trainer.py

Note:
- This is a temporary baseline trainer for current static data.
- Next iteration can replace the data source with OpenTelemetry traces/metrics while keeping the same training flow.

UI-compatible training:
- File: gnn-service/ui_preview.py
	- Train Model button runs the trainer directly from UI
	- RPC map input supports comma-separated files for training
	- Training metrics and model save path are shown in the UI panel

Deploy-and-use automation tool:
- Files:
	- lograph.py (single entry command)
	- lograph_tool/cli.py
	- lograph_tool/gui.py
	- lograph_tool/otel_ingest.py
	- lograph_tool/graph_model.py
	- lograph_tool/automation.py

Tool workflow:
- Fetch telemetry logs from OpenTelemetry HTTP endpoint or JSONL stream
- Build service graph snapshot from logs
- Train a message-passing GNN-style link model automatically
- Detect low-probability links as triggers
- Execute configured programs with dynamic parameters

Quickstart:
- Initialize config:
	- python lograph.py init
- One-shot run:
	- python lograph.py run
- Continuous monitor:
	- python lograph.py monitor
- Open GUI control panel:
	- python lograph.py gui

Default config file:
- lograph-tool.json
	- telemetry.mode: jsonl or http
	- telemetry.endpoint: OTel logs endpoint for mode=http
	- telemetry.jsonl_path: local stream file for mode=jsonl
	- actions: trigger rules and executable commands