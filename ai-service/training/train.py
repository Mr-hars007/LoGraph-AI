import os
import sys
import time
import json
import argparse
import random
import psycopg2
from psycopg2.extras import RealDictCursor
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# Import models (ensure correct relative/absolute import path)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.gnn.model import GNNModel
from models.conv.model import ConvModel

# Configurations
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@database:5432/logoph")
ARTIFACTS_DIR = os.environ.get("ARTIFACTS_DIR", "/app/artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Feature scaling parameters
SCALES = {
    "cpu": 100.0,
    "memory": 100.0,
    "request_rate": 150.0,
    "latency": 500.0,
    "error_rate": 20.0,
    "active_requests": 40.0,
    "queue_depth": 20.0
}

def get_db_connection():
    # Wait for database to be ready
    for i in range(10):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except psycopg2.OperationalError:
            time.sleep(2)
    raise Exception("Could not connect to database")

def init_db_schema(conn):
    with conn.cursor() as cur:
        # Telemetry table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id SERIAL PRIMARY KEY,
                timestamp DOUBLE PRECISION NOT NULL,
                backend_id VARCHAR(50) NOT NULL,
                cpu REAL NOT NULL,
                memory REAL NOT NULL,
                request_rate REAL NOT NULL,
                latency REAL NOT NULL,
                error_rate REAL NOT NULL,
                active_requests INT NOT NULL,
                queue_depth INT NOT NULL,
                health_status VARCHAR(50) NOT NULL
            );
        """)
        # Models table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS models (
                model_id VARCHAR(100) PRIMARY KEY,
                model_type VARCHAR(50) NOT NULL,
                training_timestamp DOUBLE PRECISION NOT NULL,
                dataset_version VARCHAR(50) NOT NULL,
                training_samples INT NOT NULL,
                validation_samples INT NOT NULL,
                metrics TEXT NOT NULL,
                artifact_path VARCHAR(255) NOT NULL,
                active BOOLEAN DEFAULT FALSE
            );
        """)
        # Scripts table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                script_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                target_backend VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                version INT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT FALSE,
                created_by VARCHAR(50),
                created_at DOUBLE PRECISION NOT NULL,
                updated_at DOUBLE PRECISION NOT NULL
            );
        """)
        # Rules table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id SERIAL PRIMARY KEY,
                prediction VARCHAR(50) NOT NULL,
                minimum_score REAL NOT NULL,
                target_backend VARCHAR(50) NOT NULL,
                script_id VARCHAR(100) REFERENCES scripts(script_id),
                enabled BOOLEAN NOT NULL DEFAULT FALSE
            );
        """)
        # Actions log table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS actions_log (
                id SERIAL PRIMARY KEY,
                timestamp DOUBLE PRECISION NOT NULL,
                prediction VARCHAR(50) NOT NULL,
                score REAL NOT NULL,
                script_id VARCHAR(100) REFERENCES scripts(script_id),
                backend_id VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL,
                output TEXT,
                error TEXT
            );
        """)
        conn.commit()

def bootstrap_telemetry(conn):
    """
    Inserts synthetic telemetry representing NORMAL, DEGRADED, and HIGH_LOAD states
    if there are fewer than 100 entries.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM telemetry")
        count = cur.fetchone()[0]
        if count >= 100:
            print(f"Database already has {count} telemetry records. Skipping bootstrap.")
            return

        print("Bootstrapping synthetic telemetry for training...")
        
        # We generate 200 timestamps (1 second apart)
        start_time = time.time() - 3600 # 1 hour ago
        backends = ["mock-be-1", "mock-be-2", "mock-be-3"]
        
        # State helper to generate realistic numbers
        def gen_metrics(state_name):
            if state_name == "HIGH_LOAD":
                return {
                    "cpu": random.uniform(80.0, 95.0),
                    "memory": random.uniform(75.0, 90.0),
                    "request_rate": random.uniform(100.0, 150.0),
                    "latency": random.uniform(250.0, 500.0),
                    "error_rate": random.uniform(10.0, 20.0),
                    "active_requests": int(random.uniform(25.0, 40.0)),
                    "queue_depth": int(random.uniform(10.0, 20.0)),
                    "health_status": "DEGRADED"
                }
            elif state_name == "DEGRADED":
                return {
                    "cpu": random.uniform(50.0, 70.0),
                    "memory": random.uniform(55.0, 70.0),
                    "request_rate": random.uniform(50.0, 80.0),
                    "latency": random.uniform(100.0, 220.0),
                    "error_rate": random.uniform(3.0, 8.0),
                    "active_requests": int(random.uniform(12.0, 22.0)),
                    "queue_depth": int(random.uniform(3.0, 8.0)),
                    "health_status": "DEGRADED"
                }
            else: # NORMAL
                return {
                    "cpu": random.uniform(15.0, 35.0),
                    "memory": random.uniform(25.0, 45.0),
                    "request_rate": random.uniform(10.0, 25.0),
                    "latency": random.uniform(20.0, 60.0),
                    "error_rate": random.uniform(0.1, 0.8),
                    "active_requests": int(random.uniform(2.0, 6.0)),
                    "queue_depth": 0,
                    "health_status": "NORMAL"
                }

        # Cycles:
        # 1. 0-60: All NORMAL
        # 2. 60-100: BE1 Stressed (HIGH_LOAD), others NORMAL
        # 3. 100-140: BE2 Stressed (DEGRADED), others NORMAL
        # 4. 140-180: BE3 Stressed (HIGH_LOAD), BE1 Stressed (DEGRADED), BE2 NORMAL
        # 5. 180-200: All NORMAL (recovery)
        for step in range(200):
            ts = start_time + step
            
            if step < 60:
                states = ["NORMAL", "NORMAL", "NORMAL"]
            elif step < 100:
                states = ["HIGH_LOAD", "NORMAL", "NORMAL"]
            elif step < 140:
                states = ["NORMAL", "DEGRADED", "NORMAL"]
            elif step < 180:
                states = ["DEGRADED", "NORMAL", "HIGH_LOAD"]
            else:
                states = ["NORMAL", "NORMAL", "NORMAL"]
                
            for idx, be in enumerate(backends):
                m = gen_metrics(states[idx])
                cur.execute("""
                    INSERT INTO telemetry (timestamp, backend_id, cpu, memory, request_rate, latency, error_rate, active_requests, queue_depth, health_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (ts, be, m["cpu"], m["memory"], m["request_rate"], m["latency"], m["error_rate"], m["active_requests"], m["queue_depth"], m["health_status"]))
                
        conn.commit()
        print("Telemetry bootstrapped successfully.")

def get_label(cpu, health_status):
    # Calculate training label:
    # 0 = NORMAL, 1 = DEGRADED, 2 = HIGH_LOAD
    if health_status == "DEGRADED":
        if cpu >= 75.0:
            return 2 # HIGH_LOAD
        return 1 # DEGRADED
    return 0 # NORMAL

def load_and_align_data(conn, window_size=5):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM telemetry ORDER BY timestamp ASC")
        rows = cur.fetchall()

    # Separate by backend
    be_data = {"mock-be-1": [], "mock-be-2": [], "mock-be-3": []}
    for row in rows:
        be_id = row["backend_id"]
        if be_id in be_data:
            be_data[be_id].append(row)

    # Align snapshots by matching close timestamps
    snapshots = []
    be1_list = be_data["mock-be-1"]
    be2_list = be_data["mock-be-2"]
    be3_list = be_data["mock-be-3"]
    
    # We loop through be1 and find closest in be2 and be3 within 2 seconds
    for r1 in be1_list:
        t1 = r1["timestamp"]
        # Find closest r2
        r2 = min(be2_list, key=lambda x: abs(x["timestamp"] - t1), default=None)
        r3 = min(be3_list, key=lambda x: abs(x["timestamp"] - t1), default=None)
        
        if r2 and abs(r2["timestamp"] - t1) <= 2.0 and r3 and abs(r3["timestamp"] - t1) <= 2.0:
            snapshots.append({
                "timestamp": t1,
                "nodes": [r1, r2, r3]
            })

    print(f"Aligned {len(snapshots)} snapshots.")
    
    if len(snapshots) < window_size:
        raise ValueError(f"Insufficient aligned snapshots: {len(snapshots)}. Need at least {window_size}.")

    # Build sliding windows
    X = [] # feature windows: [N, num_nodes, window_size, num_features]
    Y = [] # target states at end of window: [N, num_nodes]
    
    feature_keys = ["cpu", "memory", "request_rate", "latency", "error_rate", "active_requests", "queue_depth"]
    
    for i in range(window_size - 1, len(snapshots)):
        window_snapshots = snapshots[i - (window_size - 1): i + 1]
        
        # Feature matrix for this sample
        sample_x = [] # [num_nodes, window_size, num_features]
        
        for node_idx in range(3): # 3 backends
            node_window_feats = []
            for snap in window_snapshots:
                node_data = snap["nodes"][node_idx]
                # Extract and scale features
                feats = [node_data[k] / SCALES[k] for k in feature_keys]
                node_window_feats.append(feats)
            sample_x.append(node_window_feats)
            
        # Target label for this sample (the state of each node at the end of the window)
        target_snap = window_snapshots[-1]
        sample_y = []
        for node_idx in range(3):
            node_data = target_snap["nodes"][node_idx]
            label = get_label(node_data["cpu"], node_data["health_status"])
            sample_y.append(label)
            
        X.append(sample_x)
        Y.append(sample_y)
        
    return torch.tensor(X, dtype=torch.float32), torch.tensor(Y, dtype=torch.long)

class TelemetryDataset(Dataset):
    def __init__(self, X, Y):
        self.X = X
        self.Y = Y
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.Y[idx]

def train_model(model_type, X, Y, epochs=30, batch_size=16):
    # Train/Validation split
    dataset_size = len(X)
    train_size = int(dataset_size * 0.8)
    val_size = dataset_size - train_size
    
    indices = list(range(dataset_size))
    # Standard seed for reproducibility
    random.seed(42)
    random.shuffle(indices)
    
    train_indices = indices[:train_size]
    val_indices = indices[train_size:]
    
    train_dataset = TelemetryDataset(X[train_indices], Y[train_indices])
    val_dataset = TelemetryDataset(X[val_indices], Y[val_indices])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Model instantiation
    # Features: 7 (cpu, memory, request_rate, latency, error_rate, active_requests, queue_depth)
    in_features = 7
    window_size = 5
    hidden_features = 16
    num_classes = 3
    
    if model_type.lower() == "gnn":
        # For GNN, we pass flattened temporal features per node (window_size * in_features = 35)
        model = GNNModel(in_features=in_features * window_size, hidden_features=hidden_features, num_classes=num_classes)
    else:
        model = ConvModel(in_features=in_features, window_size=window_size, hidden_features=hidden_features, num_classes=num_classes)
        
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    print(f"Training {model_type.upper()} model for {epochs} epochs...")
    
    best_val_loss = float('inf')
    best_epoch_metrics = {}
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            logits = model(batch_x) # [batch_size, 3, 3]
            
            # Reshape logits to [batch_size * 3, 3] and targets to [batch_size * 3]
            loss = criterion(logits.view(-1, num_classes), batch_y.view(-1))
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch_x.size(0)
            
        train_loss /= train_size
        
        # Validation
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        
        # Compute precision/recall/F1 matrices
        y_true = []
        y_pred = []
        
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                logits = model(batch_x)
                loss = criterion(logits.view(-1, num_classes), batch_y.view(-1))
                val_loss += loss.item() * batch_x.size(0)
                
                preds = torch.argmax(logits, dim=2) # [batch_size, 3]
                correct += (preds == batch_y).sum().item()
                total += batch_y.numel()
                
                y_true.extend(batch_y.view(-1).tolist())
                y_pred.extend(preds.view(-1).tolist())
                
        val_loss /= val_size
        accuracy = correct / total
        
        # Calculate F1 score macro-average
        # Classes: 0, 1, 2
        f1_scores = []
        for cls in range(num_classes):
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            f1_scores.append(f1)
            
        macro_f1 = sum(f1_scores) / len(f1_scores)
        
        if (epoch + 1) % 5 == 0 or epoch == epochs - 1:
            print(f"Epoch {epoch+1:02d}/{epochs} - Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f} - Accuracy: {accuracy:.4f} - Macro-F1: {macro_f1:.4f}")
            
        # Keep track of best model metrics
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch_metrics = {
                "accuracy": accuracy,
                "macro_f1": macro_f1,
                "val_loss": val_loss,
                "train_loss": train_loss
            }
            # Save temporary best state
            torch.save(model.state_dict(), os.path.join(ARTIFACTS_DIR, f"temp_best_{model_type}.pt"))
            
    # Load best weights
    model.load_state_dict(torch.load(os.path.join(ARTIFACTS_DIR, f"temp_best_{model_type}.pt")))
    os.remove(os.path.join(ARTIFACTS_DIR, f"temp_best_{model_type}.pt"))
    
    return model, best_epoch_metrics, train_size, val_size

def save_model_artifact(model, model_type, metrics, train_size, val_size, conn):
    # Unique model ID
    timestamp = time.time()
    model_id = f"model-{model_type}-{int(timestamp)}"
    artifact_path = os.path.join(ARTIFACTS_DIR, f"{model_id}.pt")
    
    # Save PyTorch state dict
    torch.save(model.state_dict(), artifact_path)
    print(f"Model weights saved to {artifact_path}")
    
    # Write to database
    with conn.cursor() as cur:
        # Mark other models of this type as inactive
        cur.execute("UPDATE models SET active = FALSE WHERE model_type = %s", (model_type,))
        
        # Insert metadata
        cur.execute("""
            INSERT INTO models (model_id, model_type, training_timestamp, dataset_version, training_samples, validation_samples, metrics, artifact_path, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        """, (
            model_id,
            model_type,
            timestamp,
            f"v-{int(timestamp)}",
            train_size,
            val_size,
            json.dumps(metrics),
            artifact_path
        ))
        
        # Verify if a rule for prediction states exists, and seed default rules if none
        cur.execute("SELECT COUNT(*) FROM rules")
        rule_count = cur.fetchone()[0]
        if rule_count == 0:
            print("Seeding default automation rules...")
            # Let's see if we have scripts in DB to hook rules to.
            # If not, backend will register scripts, but we can seed rules with placeholder scripts or empty script IDs first.
            # We will insert rules referencing mock-be-2 and mock-be-3.
            pass
            
        conn.commit()
        
    print(f"Registered model {model_id} in DB database.")
    return model_id

def main():
    parser = argparse.ArgumentParser(description="Train Logoph AI Models")
    parser.add_argument("--model-type", type=str, default="gnn", choices=["gnn", "conv"], help="Type of model to train (gnn or conv)")
    parser.add_argument("--epochs", type=int, default=30, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    args = parser.parse_args()
    
    conn = get_db_connection()
    try:
        init_db_schema(conn)
        bootstrap_telemetry(conn)
        
        # Align telemetry to create dataset
        X, Y = load_and_align_data(conn)
        
        # Train
        model, metrics, train_size, val_size = train_model(args.model_type, X, Y, epochs=args.epochs, batch_size=args.batch_size)
        
        # Save
        save_model_artifact(model, args.model_type, metrics, train_size, val_size, conn)
        
        print("Training complete successfully!")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
