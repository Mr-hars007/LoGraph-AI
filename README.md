# Logoph AI - GNN Self-Healing Operations MVP

Logoph AI is an autonomous self-healing operational MVP that monitors, predicts, and remediates managed service failures using a real trainable Graph Neural Network (GNN) and convolutional models.

The system is completely self-contained, requiring no real infrastructure, and runs entirely inside Docker Compose.

---

## 1. Logical Architecture & Data Flow

```text
                    OBSERVE
                       │
                       ▼
               Mock Backend
                       │
                     LGCA
                       │
                       ▼
                   TELEMETRY
                       │
                       ▼
              CLEAN & CONVERT
                       │
                       ▼
                    ANALYZE
                       │
                       ▼
                REAL ML MODEL
                 ┌─────┴─────┐
                 │           │
                GNN        Conv Model
                 │           │
                 └─────┬─────┘
                       ▼
              PREDICTION + SCORE
                       │
                       ▼
                 VALIDATION
                       │
             ┌─────────┴─────────┐
             │                   │
        AUTOMATED           USER-DEFINED
             │                   │
             └─────────┬─────────┘
                       ▼
                USER-CREATED
               APPROVED SCRIPT
                       │
                       ▼
                     LGCA
                       │
                       ▼
                  SANDBOXED
                  EXECUTION
                       │
                       ▼
                 MOCK BACKEND
                       │
                       ▼
                   RECOVERY
                       │
                       └──────────► TELEMETRY
```

### Components:
1. **Mock Backends (1, 2, 3)**: Three independent services exposing performance metrics and simulating traffic.
2. **LGCA (Logoph Guard & Control Agent)**: One agent per mock backend. Transmits telemetry and executes sandboxed recovery actions.
3. **Central Backend**: FastAPI application that logs telemetry, runs the rule engine, and coordinates actions.
4. **AI Service**: Manages PyTorch GNN and Convolutional models. Runs live inference over temporal windows.
5. **Script Sandbox**: Runs user scripts as a non-root user under strict CPU/memory limits and timeout parameters.
6. **Frontend**: React-style interactive UI displaying telemetry, graph topology, model version/metrics, rule setup, and execution log.
7. **Database**: PostgreSQL storing telemetry, model metadata, scripts, rules, and logs.

---

## 2. GNN Graph Topology

The three mock backends are represented as graph nodes connected in a cyclic triangle loop:

```text
       mock-be-1 (BE1)
        /          \
       /            \
mock-be-3 (BE3) ── mock-be-2 (BE2)
```

### GNN Structure:
- **Node features**: Telemetry window $X \in \mathbb{R}^{3 \times 5 \times 7}$ containing the last 5 ticks of normalized CPU, memory, request rate, latency, error rate, active requests, and queue depth.
- **Adjacency Matrix**:
  $$A = \begin{pmatrix} 0 & 1 & 1 \\ 1 & 0 & 1 \\ 1 & 1 & 0 \end{pmatrix}$$
- **Normalization**: Computed inside the PyTorch GNN layer as $\tilde{D}^{-1/2} \tilde{A} \tilde{D}^{-1/2} = \frac{1}{3} \tilde{A}$ (including self loops).
- **Classification Output**: The GNN outputs classification scores for each of the 3 backend nodes separately (`NORMAL`, `DEGRADED`, `HIGH_LOAD`).

---

## 3. Training & Labeled Target Generation

The training pipeline does **not** rely on static thresholds or pre-programmed decisions. It uses a **trainable ML pipeline**.

### Target Label Generation Strategy:
Operational states are labeled using a combination of the active stress state and telemetry response:
- **`NORMAL` (0)**: Baseline normal operations (CPU 20-40%, latency 20-80ms, no active stress).
- **`DEGRADED` (1)**: Moderate resource/traffic stress (CPU 50-70%, health status "DEGRADED").
- **`HIGH_LOAD` (2)**: Severe stress (CPU >= 75%, health status "DEGRADED").

To make training instantly runnable, the training script checks if the database is empty, and automatically bootstraps a dataset representing realistic incident cycles (normal workload, load spikes on BE1/BE2/BE3, recovery states).

---

## 4. Security Containment & Sandboxing

User-submitted scripts run inside an isolated runner container (`script-sandbox`):
- **User Permission**: Runs as `sandbox` (UID/GID 10001), a non-root, non-privileged user.
- **Resource Constraints**: Container CPU limited to `0.25` cores, memory limited to `64M` via Docker Compose.
- **Execution Limits**: Hard timeout of 10s enforced by python subprocess controller, truncating output buffer size to 50KB.
- **Isolation**: No host directory mappings, no Docker socket access, no access to external networks.
- **Interaction**: The script interacts with the target mock backend solely via HTTP request over the Docker network (using the target backend's URL passed dynamically via `MOCK_BACKEND_URL`).

---

## 5. Getting Started

### Prerequisites:
- Docker and Docker Compose installed.

### Step 1: Start the services
From the root of the project, build and run the services:
```bash
docker compose up --build -d
```
Verify that all 11 containers are running:
```bash
docker compose ps
```

### Step 2: Access the Dashboard
Open your browser and navigate to:
- **Frontend Dashboard**: `http://localhost:8080`
- **Backend Swagger APIs**: `http://localhost:8000/docs`
- **AI Service Swagger APIs**: `http://localhost:8004/docs`

### Step 3: Run the Model Training
The GNN model must be trained to perform predictions. You can do this by clicking the **Retrain** button on the dashboard navbar or by running this command inside the `ai-service` container:
```bash
docker compose exec ai-service python -m training.train --model-type gnn --epochs 30
```
This script will:
1. Connect to PostgreSQL.
2. Bootstrap 200 synthetic telemetry points with normal and degraded cycles.
3. Align snapshots and construct sliding temporal windows.
4. Train the GNN model, saving the PyTorch weights `.pt` to the shared artifacts volume.
5. Log model validation metrics (accuracy, F1-score) into the DB.
6. Activate the model for live inference.

### Step 4: Run E2E Integration Test
To run the automated integration test covering the entire GNN self-healing loop:
```bash
# On the host machine (requires pip install requests)
python test_e2e.py
```
This test script will verify service health, trigger training, stress `mock-be-2`, monitor the GNN prediction, assert the rule matches and schedules the sandboxed recovery script, and confirm the backend successfully recovers back to a `NORMAL` state.

---

## 6. Project Structure

```text
.
├── frontend/
│   ├── index.html
│   ├── nginx.conf
│   └── Dockerfile
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── ai-service/
│   ├── models/
│   │   ├── gnn/
│   │   │   └── model.py
│   │   └── conv/
│   │       └── model.py
│   ├── training/
│   │   └── train.py
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
├── lgca/
│   ├── agent.py
│   ├── requirements.txt
│   └── Dockerfile
├── mock-backends/
│   ├── backend-1/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── backend-2/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── backend-3/
│       ├── app.py
│       ├── requirements.txt
│       └── Dockerfile
├── script-sandbox/
│   ├── server.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── test_e2e.py
└── README.md
```
