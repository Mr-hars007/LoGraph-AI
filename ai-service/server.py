import os
import sys
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import torch
import torch.nn as nn
import torch.nn.functional as F
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict

# Import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models.gnn.model import GNNModel
from models.conv.model import ConvModel

app = FastAPI(title="Logoph AI Service")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@database:5432/logoph")
ARTIFACTS_DIR = os.environ.get("ARTIFACTS_DIR", "/app/artifacts")

# Feature scaling parameters (identical to train.py)
SCALES = {
    "cpu": 100.0,
    "memory": 100.0,
    "request_rate": 150.0,
    "latency": 500.0,
    "error_rate": 20.0,
    "active_requests": 40.0,
    "queue_depth": 20.0
}

CLASSES = {0: "NORMAL", 1: "DEGRADED", 2: "HIGH_LOAD"}

# In-memory cache for loaded model
class LoadedModelCache:
    def __init__(self):
        self.model_id = None
        self.model_type = None
        self.model = None

model_cache = LoadedModelCache()

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def get_active_model_meta():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM models WHERE active = TRUE LIMIT 1")
            return cur.fetchone()
    except Exception as e:
        print(f"Error fetching active model: {e}")
        return None
    finally:
        conn.close()

def load_active_model():
    meta = get_active_model_meta()
    if not meta:
        return None, None, None

    model_id = meta["model_id"]
    model_type = meta["model_type"]
    artifact_path = meta["artifact_path"]

    # If already cached, return it
    if model_cache.model_id == model_id and model_cache.model is not None:
        return model_cache.model, model_type, model_id

    # Load from disk
    if not os.path.exists(artifact_path):
        print(f"Model file not found at {artifact_path}")
        return None, None, None

    print(f"Loading active model: {model_id} ({model_type})")
    
    in_features = 7
    window_size = 5
    hidden_features = 16
    num_classes = 3

    if model_type.lower() == "gnn":
        model = GNNModel(in_features=in_features * window_size, hidden_features=hidden_features, num_classes=num_classes)
    else:
        model = ConvModel(in_features=in_features, window_size=window_size, hidden_features=hidden_features, num_classes=num_classes)

    try:
        model.load_state_dict(torch.load(artifact_path))
        model.eval()
        
        # Cache it
        model_cache.model_id = model_id
        model_cache.model_type = model_type
        model_cache.model = model
        
        return model, model_type, model_id
    except Exception as e:
        print(f"Error loading model state dict: {e}")
        return None, None, None

# Pydantic schemas for /predict
class TelemetryItem(BaseModel):
    backend_id: str
    cpu: float
    memory: float
    request_rate: float
    latency: float
    error_rate: float
    active_requests: int
    queue_depth: int
    health_status: str

class PredictRequest(BaseModel):
    # Expects a list of 5 snapshots, where each snapshot is a list of 3 backend metrics
    # Sorted chronologically (oldest to newest)
    window: List[List[TelemetryItem]]

class PredictResponseItem(BaseModel):
    backend_id: str
    prediction: str
    score: float

class PredictResponse(BaseModel):
    model_id: str
    model_type: str
    predictions: List[PredictResponseItem]
    fallback: bool

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    window = req.window
    if len(window) != 5:
        raise HTTPException(status_code=400, detail="Window size must be exactly 5")
        
    # Check that each step contains exactly 3 backend items
    for step_idx, step in enumerate(window):
        if len(step) != 3:
            raise HTTPException(status_code=400, detail=f"Each window step must contain exactly 3 nodes, got {len(step)} at step {step_idx}")

    # Step 1: Clean & Convert & Build Graph features
    # Input shape needed: [1, 3, 5, 7]
    try:
        # Align nodes: make sure node 0 is mock-be-1, node 1 is mock-be-2, node 2 is mock-be-3
        node_order = ["mock-be-1", "mock-be-2", "mock-be-3"]
        
        sample_x = [] # [3, 5, 7]
        for node_id in node_order:
            node_window = []
            for step in window:
                # Find the telemetry item for this node
                item = next((item for item in step if item.backend_id == node_id), None)
                if not item:
                    raise HTTPException(status_code=400, detail=f"Missing telemetry for {node_id} in temporal window")
                
                # Extract and scale features
                feats = [
                    item.cpu / SCALES["cpu"],
                    item.memory / SCALES["memory"],
                    item.request_rate / SCALES["request_rate"],
                    item.latency / SCALES["latency"],
                    item.error_rate / SCALES["error_rate"],
                    item.active_requests / SCALES["active_requests"],
                    item.queue_depth / SCALES["queue_depth"]
                ]
                node_window.append(feats)
            sample_x.append(node_window)
            
        # Convert to tensor and add batch dimension -> [1, 3, 5, 7]
        x_tensor = torch.tensor([sample_x], dtype=torch.float32)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error preprocessing input features: {str(e)}")

    # Step 2: Load trained model & run inference
    model, model_type, model_id = load_active_model()
    
    if model is None:
        # Fallback mechanism (Requirement 5)
        print("No trained model active. Using fallback rule-based inference.")
        predictions = []
        # Get latest metrics (the last step of the window)
        latest_step = window[-1]
        for node_id in node_order:
            item = next(item for item in latest_step if item.backend_id == node_id)
            # Rule based fallback:
            if item.health_status == "DEGRADED":
                if item.cpu >= 75.0:
                    pred_state = "HIGH_LOAD"
                    score = 0.90
                else:
                    pred_state = "DEGRADED"
                    score = 0.85
            else:
                pred_state = "NORMAL"
                score = 0.95
                
            predictions.append(PredictResponseItem(
                backend_id=node_id,
                prediction=pred_state,
                score=score
            ))
            
        return PredictResponse(
            model_id="fallback-rules",
            model_type="fallback",
            predictions=predictions,
            fallback=True
        )

    # Run actual ML inference
    try:
        with torch.no_grad():
            logits = model(x_tensor) # [1, 3, 3]
            probs = F.softmax(logits, dim=2) # [1, 3, 3]
            
            predictions = []
            for idx, node_id in enumerate(node_order):
                node_probs = probs[0, idx]
                max_cls = torch.argmax(node_probs).item()
                score = node_probs[max_cls].item()
                pred_state = CLASSES[max_cls]
                
                predictions.append(PredictResponseItem(
                    backend_id=node_id,
                    prediction=pred_state,
                    score=round(score, 4)
                ))
                
            return PredictResponse(
                model_id=model_id,
                model_type=model_type,
                predictions=predictions,
                fallback=False
            )
    except Exception as e:
        print(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

class TrainRequest(BaseModel):
    model_type: str = "gnn"
    epochs: int = 30

def run_training_background(model_type: str, epochs: int):
    # Runs the train script programmatically using a subprocess
    try:
        print(f"Triggering background training for {model_type}...")
        # Get absolute path to train.py
        train_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training", "train.py")
        subprocess_cmd = [sys.executable, train_path, "--model-type", model_type, "--epochs", str(epochs)]
        
        import subprocess
        res = subprocess.run(subprocess_cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print("Background training completed successfully.")
            print(res.stdout)
        else:
            print(f"Background training failed with return code {res.returncode}")
            print("Stdout:", res.stdout)
            print("Stderr:", res.stderr)
    except Exception as e:
        print(f"Error during background training: {e}")

@app.post("/train")
def trigger_training(req: TrainRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_training_background, req.model_type, req.epochs)
    return {"status": "Training triggered in background", "model_type": req.model_type}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
