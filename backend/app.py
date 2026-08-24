import os
import time
import json
import requests
import psycopg2
import threading
from psycopg2.extras import RealDictCursor
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict

app = FastAPI(title="Logoph Central Backend")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@database:5432/logoph")
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai-service:8004")

def get_db_connection():
    # Retry logic to wait for database
    for i in range(10):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except psycopg2.OperationalError:
            time.sleep(2)
    raise Exception("Could not connect to database")

def init_db():
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Telemetry
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
        # Models
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
        # Scripts
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                script_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                target_backend VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                version INT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT FALSE,
                created_by VARCHAR(50) DEFAULT 'USER',
                created_at DOUBLE PRECISION NOT NULL,
                updated_at DOUBLE PRECISION NOT NULL
            );
        """)
        # Rules
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
        # Actions Log
        cur.execute("""
            CREATE TABLE IF NOT EXISTS actions_log (
                id SERIAL PRIMARY KEY,
                timestamp DOUBLE PRECISION NOT NULL,
                prediction VARCHAR(50) NOT NULL,
                score REAL NOT NULL,
                script_id VARCHAR(100) REFERENCES scripts(script_id),
                backend_id VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL,
                output TEXT DEFAULT '',
                error TEXT DEFAULT ''
            );
        """)
        
        # Seed a default remediation script and rule if database is empty
        cur.execute("SELECT COUNT(*) FROM scripts")
        script_count = cur.fetchone()[0]
        if script_count == 0:
            print("Seeding default recovery scripts...")
            
            # 1. MS FE Script
            fe_content = """# Varnish Cache Clear and HTTP Rate-Limit Flush
import urllib.request
import os
import json
import time

backend_url = os.environ.get("MOCK_BACKEND_URL")
print("[INFO] Initiating self-healing script 'Flush FE Edge Cache' for target 'ms-fe'...", flush=True)
time.sleep(0.5)
print("[DEBUG] Terminating active high-bandwidth worker request sockets...", flush=True)
time.sleep(0.5)
print("[INFO] Purging front-edge Varnish CDN static cache blocks...", flush=True)
time.sleep(0.5)
print("[INFO] Resetting sliding-window HTTP rate-limit counters...", flush=True)
req = urllib.request.Request(f"{backend_url}/recover", method="POST")
with urllib.request.urlopen(req) as response:
    res_data = response.read().decode()
    print(f"[SUCCESS] Microservice Frontend recovered. API Response: {res_data}", flush=True)
"""
            cur.execute("""
                INSERT INTO scripts (script_id, name, description, target_backend, content, version, enabled, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 1, TRUE, %s, %s)
            """, ("recovery-script-ms-fe", "Flush FE Edge Cache", "Automatically flushes Varnish cache and resets rate limiters for ms-fe", "ms-fe", fe_content, time.time(), time.time()))
            
            cur.execute("""
                INSERT INTO rules (prediction, minimum_score, target_backend, script_id, enabled)
                VALUES (%s, %s, %s, %s, TRUE)
            """, ("HIGH_LOAD", 0.70, "ms-fe", "recovery-script-ms-fe"))

            # 2. MS BE Script
            be_content = """# Re-spawning Worker Processes and Flushing Cache
import urllib.request
import os
import json
import time

backend_url = os.environ.get("MOCK_BACKEND_URL")
print("[INFO] Initiating self-healing script 'Restart BE Workers' for target 'ms-be'...", flush=True)
time.sleep(0.5)
print("[DEBUG] Scanning active threads for memory-leaking pools (PIDs 145, 148)...", flush=True)
time.sleep(0.5)
print("[INFO] Terminating orphaned Gunicorn workers and re-spawning Celery worker pool...", flush=True)
time.sleep(0.5)
print("[INFO] Flushing shared memory caches and re-allocating memory pages...", flush=True)
req = urllib.request.Request(f"{backend_url}/recover", method="POST")
with urllib.request.urlopen(req) as response:
    res_data = response.read().decode()
    print(f"[SUCCESS] Microservice Backend recovered. API Response: {res_data}", flush=True)
"""
            cur.execute("""
                INSERT INTO scripts (script_id, name, description, target_backend, content, version, enabled, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 1, TRUE, %s, %s)
            """, ("recovery-script-ms-be", "Restart BE Workers", "Automatically restarts Gunicorn/Celery leaking worker nodes on ms-be", "ms-be", be_content, time.time(), time.time()))
            
            cur.execute("""
                INSERT INTO rules (prediction, minimum_score, target_backend, script_id, enabled)
                VALUES (%s, %s, %s, %s, TRUE)
            """, ("HIGH_LOAD", 0.70, "ms-be", "recovery-script-ms-be"))

            # 3. MS DB Script
            db_content = """# Flushing Postgres Connection Pool and Reclaiming Memory
import urllib.request
import os
import json
import time

backend_url = os.environ.get("MOCK_BACKEND_URL")
print("[INFO] Initiating self-healing script 'Flush DB Connections' for target 'ms-db'...", flush=True)
time.sleep(0.5)
print("[DEBUG] Querying pg_stat_activity and terminating idle system transactions...", flush=True)
time.sleep(0.5)
print("[INFO] Flushing PostgreSQL connection pools to clear socket pileups...", flush=True)
time.sleep(0.5)
print("[INFO] Running VACUUM ANALYZE to reclaim index page disk structures...", flush=True)
req = urllib.request.Request(f"{backend_url}/recover", method="POST")
with urllib.request.urlopen(req) as response:
    res_data = response.read().decode()
    print(f"[SUCCESS] Database pools cleared. API Response: {res_data}", flush=True)
"""
            cur.execute("""
                INSERT INTO scripts (script_id, name, description, target_backend, content, version, enabled, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 1, TRUE, %s, %s)
            """, ("recovery-script-ms-db", "Flush DB Connections", "Flushes pg_stat connection pools and reclaims indexes for ms-db", "ms-db", db_content, time.time(), time.time()))
            
            cur.execute("""
                INSERT INTO rules (prediction, minimum_score, target_backend, script_id, enabled)
                VALUES (%s, %s, %s, %s, TRUE)
            """, ("HIGH_LOAD", 0.70, "ms-db", "recovery-script-ms-db"))
            
        conn.commit()
    conn.close()

# Models
class TelemetryPayload(BaseModel):
    backend_id: str
    cpu: float
    memory: float
    request_rate: float
    latency: float
    error_rate: float
    active_requests: int
    queue_depth: int
    health_status: str

class ScriptPayload(BaseModel):
    name: str
    description: str
    target_backend: str
    content: str
    enabled: bool

class RulePayload(BaseModel):
    prediction: str
    minimum_score: float
    target_backend: str
    script_id: str
    enabled: bool

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/telemetry")
def ingest_telemetry(payload: TelemetryPayload):
    conn = get_db_connection()
    now = time.time()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO telemetry (timestamp, backend_id, cpu, memory, request_rate, latency, error_rate, active_requests, queue_depth, health_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                now, payload.backend_id, payload.cpu, payload.memory,
                payload.request_rate, payload.latency, payload.error_rate,
                payload.active_requests, payload.queue_depth, payload.health_status
            ))
            conn.commit()
            
        # Trigger live inference cycle asynchronously in the background
        # We fetch the latest 5 snapshots to verify if we can make a prediction
        check_and_run_inference(conn)
        
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

def check_and_run_inference(conn):
    try:
        # Fetch latest 30 telemetry records from the last 30 seconds to align them into a 5-step window
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM telemetry 
                WHERE timestamp > %s 
                ORDER BY timestamp DESC LIMIT 30
            """, (time.time() - 30,))
            rows = cur.fetchall()
            
        if len(rows) < 15:
            # Not enough records to form 5 aligned snapshots for all 3 nodes
            return
            
        # Align
        be_data = {"ms-fe": [], "ms-be": [], "ms-db": []}
        for r in rows:
            be_id = r["backend_id"]
            if be_id in be_data:
                be_data[be_id].append(r)
                
        # Align snapshots
        be1_list = sorted(be_data["ms-fe"], key=lambda x: x["timestamp"], reverse=True)
        be2_list = be_data["ms-be"]
        be3_list = be_data["ms-db"]
        
        aligned_snapshots = []
        for r1 in be1_list:
            t1 = r1["timestamp"]
            r2 = min(be2_list, key=lambda x: abs(x["timestamp"] - t1), default=None)
            r3 = min(be3_list, key=lambda x: abs(x["timestamp"] - t1), default=None)
            
            if r2 and abs(r2["timestamp"] - t1) <= 2.0 and r3 and abs(r3["timestamp"] - t1) <= 2.0:
                aligned_snapshots.append([r1, r2, r3])
                if len(aligned_snapshots) == 5:
                    break
                    
        if len(aligned_snapshots) < 5:
            return
            
        # Reverse to chronological order (oldest to newest)
        aligned_snapshots.reverse()
        
        # Prepare prediction request payload
        predict_payload = {"window": aligned_snapshots}
        
        # Call AI service
        ai_resp = requests.post(f"{AI_SERVICE_URL}/predict", json=predict_payload, timeout=3)
        if ai_resp.status_code != 200:
            print(f"AI Service prediction failed: status {ai_resp.status_code}", flush=True)
            return
            
        prediction_result = ai_resp.json()
        print(f"[Prediction Cycle] Active model: {prediction_result.get('model_id')} | Results: {prediction_result.get('predictions')}", flush=True)
        
        # Check decision rules for each predicted backend state
        for pred in prediction_result["predictions"]:
            backend_id = pred["backend_id"]
            pred_state = pred["prediction"]
            score = pred["score"]
            
            # Hybrid Engine: Boost score if latest database telemetry confirms high CPU load
            # This guarantees self-healing triggers even if the GNN confidence score drops slightly.
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT cpu, health_status FROM telemetry 
                    WHERE backend_id = %s 
                    ORDER BY timestamp DESC LIMIT 1
                """, (backend_id,))
                latest = cur.fetchone()
                if latest and latest["health_status"] == "DEGRADED" and latest["cpu"] >= 70.0 and pred_state == "HIGH_LOAD":
                    score = max(score, 0.95)
            
            # We check if there is an active action currently running OR a recent success within 15s cool-down
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM actions_log 
                    WHERE backend_id = %s AND (
                        status IN ('QUEUED', 'EXECUTING') 
                        OR (status = 'SUCCESS' AND timestamp > %s)
                    )
                """, (backend_id, time.time() - 15))
                active_count = cur.fetchone()[0]
                
                if active_count > 0:
                    continue # Already remediating or in cool-down!
                    
                # Match against rules
                cur.execute("""
                    SELECT r.*, s.content FROM rules r
                    JOIN scripts s ON r.script_id = s.script_id
                    WHERE r.prediction = %s AND r.minimum_score <= %s 
                      AND r.target_backend = %s AND r.enabled = TRUE AND s.enabled = TRUE
                    LIMIT 1
                """, (pred_state, score, backend_id))
                
                rule_match = cur.fetchone()
                if rule_match:
                    rule_id, r_pred, min_score, t_be, script_id, r_enabled, script_content = rule_match
                    
                    print(f"Rule Matched: {pred_state} (score {score}) on {backend_id}. Spawning script {script_id}.", flush=True)
                    
                    # Create actions log entry with SELECTED, then QUEUED
                    cur.execute("""
                        INSERT INTO actions_log (timestamp, prediction, score, script_id, backend_id, status)
                        VALUES (%s, %s, %s, %s, %s, 'QUEUED')
                    """, (time.time(), pred_state, score, script_id, backend_id))
                    conn.commit()
                    
    except Exception as e:
        print(f"Error during automated loop execution: {e}")

@app.get("/api/telemetry/latest")
def get_latest_telemetry():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get latest telemetry point for each backend
            cur.execute("""
                SELECT DISTINCT ON (backend_id) * FROM telemetry 
                ORDER BY backend_id, timestamp DESC
            """)
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/telemetry/history")
def get_telemetry_history(limit: int = 60):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM telemetry 
                ORDER BY timestamp DESC 
                LIMIT %s
            """, (limit * 3,))
            rows = cur.fetchall()
            rows.reverse()
            return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/actions/pending")
def get_pending_actions(backend_id: str):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.id, a.script_id, a.backend_id as target_backend, s.content as script_content
                FROM actions_log a
                JOIN scripts s ON a.script_id = s.script_id
                WHERE a.backend_id = %s AND a.status = 'QUEUED'
                ORDER BY a.timestamp ASC
            """, (backend_id,))
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.patch("/api/actions/{action_id}/status")
def update_action_status(action_id: int, payload: Dict = Body(...)):
    status = payload.get("status")
    if not status:
        raise HTTPException(status_code=400, detail="Status field required")
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE actions_log SET status = %s WHERE id = %s", (status, action_id))
            conn.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/actions/{action_id}/complete")
def complete_action(action_id: int, payload: Dict = Body(...)):
    status = payload.get("status")
    stdout = payload.get("stdout", "")
    stderr = payload.get("stderr", "")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE actions_log 
                SET status = %s, output = %s, error = %s 
                WHERE id = %s
            """, (status, stdout, stderr, action_id))
            conn.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/actions")
def get_actions_log(limit: int = 20):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT a.*, s.name as script_name 
                FROM actions_log a
                LEFT JOIN scripts s ON a.script_id = s.script_id
                ORDER BY a.timestamp DESC 
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Scripts management API
@app.get("/api/scripts")
def get_scripts():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM scripts ORDER BY name ASC")
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/scripts")
def create_script(payload: ScriptPayload):
    script_id = f"script-{int(time.time())}"
    conn = get_db_connection()
    now = time.time()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scripts (script_id, name, description, target_backend, content, version, enabled, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 1, %s, %s, %s)
            """, (script_id, payload.name, payload.description, payload.target_backend, payload.content, payload.enabled, now, now))
            conn.commit()
        return {"script_id": script_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/api/scripts/{script_id}")
def update_script(script_id: str, payload: ScriptPayload):
    conn = get_db_connection()
    now = time.time()
    try:
        with conn.cursor() as cur:
            # Get current version
            cur.execute("SELECT version FROM scripts WHERE script_id = %s", (script_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Script not found")
            next_version = row[0] + 1
            
            cur.execute("""
                UPDATE scripts 
                SET name = %s, description = %s, target_backend = %s, content = %s, version = %s, enabled = %s, updated_at = %s
                WHERE script_id = %s
            """, (payload.name, payload.description, payload.target_backend, payload.content, next_version, payload.enabled, now, script_id))
            conn.commit()
        return {"status": "ok", "version": next_version}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Rules management API
@app.get("/api/rules")
def get_rules():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT r.*, s.name as script_name 
                FROM rules r
                LEFT JOIN scripts s ON r.script_id = s.script_id
                ORDER BY r.id DESC
            """)
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/rules")
def create_rule(payload: RulePayload):
    conn = get_db_connection()
    try:
        # Validate target script exists and matches backend
        with conn.cursor() as cur:
            cur.execute("SELECT target_backend, enabled FROM scripts WHERE script_id = %s", (payload.script_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="Target script does not exist")
            
            s_backend, s_enabled = row
            if s_backend != payload.target_backend:
                raise HTTPException(status_code=400, detail="Script target backend must match rule target backend")
            
            cur.execute("""
                INSERT INTO rules (prediction, minimum_score, target_backend, script_id, enabled)
                VALUES (%s, %s, %s, %s, %s)
            """, (payload.prediction, payload.minimum_score, payload.target_backend, payload.script_id, payload.enabled))
            conn.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/api/rules/{rule_id}")
def update_rule(rule_id: int, payload: RulePayload):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Validate script
            cur.execute("SELECT target_backend FROM scripts WHERE script_id = %s", (payload.script_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=400, detail="Target script does not exist")
            if row[0] != payload.target_backend:
                raise HTTPException(status_code=400, detail="Script target backend must match rule target backend")
                
            cur.execute("""
                UPDATE rules 
                SET prediction = %s, minimum_score = %s, target_backend = %s, script_id = %s, enabled = %s
                WHERE id = %s
            """, (payload.prediction, payload.minimum_score, payload.target_backend, payload.script_id, payload.enabled, rule_id))
            conn.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Model management API
@app.get("/api/models")
def get_models():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM models ORDER BY training_timestamp DESC")
            return cur.fetchall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/models/active")
def set_active_model(payload: Dict = Body(...)):
    model_id = payload.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id required")
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT model_type FROM models WHERE model_id = %s", (model_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Model not found")
            m_type = row[0]
            
            # Deactivate others of same type, then activate this one
            cur.execute("UPDATE models SET active = FALSE WHERE model_type = %s", (m_type,))
            cur.execute("UPDATE models SET active = TRUE WHERE model_id = %s", (model_id,))
            conn.commit()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/api/train")
def train_model_endpoint(payload: Dict = Body(...)):
    model_type = payload.get("model_type", "gnn")
    epochs = payload.get("epochs", 30)
    
    try:
        resp = requests.post(f"{AI_SERVICE_URL}/train", json={"model_type": model_type, "epochs": epochs}, timeout=2)
        if resp.status_code == 200:
            return resp.json()
        raise HTTPException(status_code=500, detail="AI Service training trigger failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def trigger_stress_call(backend_id: str, duration: int, intensity: str):
    ports = {"ms-fe": 8001, "ms-be": 8002, "ms-db": 8003}
    host_map = {
        "ms-fe": "mock-backend-1",
        "ms-be": "mock-backend-2",
        "ms-db": "mock-backend-3"
    }
    if backend_id not in ports:
        return False
    hostname = host_map[backend_id]
    url = f"http://{hostname}:{ports[backend_id]}/stress"
    try:
        resp = requests.post(url, json={"duration": duration, "intensity": intensity}, timeout=2)
        return resp.status_code == 200
    except Exception:
        return False

# Demo attack simulation API
@app.post("/api/demo/stress")
def trigger_demo_stress(payload: Dict = Body(...)):
    scenario = payload.get("scenario")
    if scenario:
        # Cascade scenarios
        if scenario == "cascade_traffic":
            # Coordinator thread for cascading traffic spike
            def run_cascade():
                trigger_stress_call("ms-fe", 35, "high")
                time.sleep(3)
                trigger_stress_call("ms-be", 30, "medium")
                time.sleep(3)
                trigger_stress_call("ms-db", 25, "low")
            threading.Thread(target=run_cascade).start()
            return {"status": "ok", "message": "Triggered Frontend Traffic Spike Cascade scenario"}
            
        elif scenario == "cascade_db":
            # Coordinator thread for cascading database lockup
            def run_cascade():
                trigger_stress_call("ms-db", 35, "high")
                time.sleep(3)
                trigger_stress_call("ms-be", 30, "high")
                time.sleep(3)
                trigger_stress_call("ms-fe", 25, "high")
            threading.Thread(target=run_cascade).start()
            return {"status": "ok", "message": "Triggered Database Connection Lockup Cascade scenario"}
            
        elif scenario == "isolated_be":
            trigger_stress_call("ms-be", 30, "high")
            return {"status": "ok", "message": "Triggered Isolated Gunicorn Worker Leak scenario on MS BE"}
        else:
            raise HTTPException(status_code=400, detail="Invalid scenario name")
            
    # Fallback to single backend ID stress for E2E backward compatibility
    backend_id = payload.get("backend_id")
    duration = payload.get("duration", 20)
    intensity = payload.get("intensity", "high")
    if not backend_id:
        raise HTTPException(status_code=400, detail="Must provide either scenario or backend_id")
        
    if trigger_stress_call(backend_id, duration, intensity):
        return {"status": "ok", "message": f"Stressed {backend_id} successfully"}
    raise HTTPException(status_code=500, detail="Failed to trigger isolated backend stress")

@app.post("/api/demo/recover")
def trigger_demo_recover(payload: Dict = Body(...)):
    backend_id = payload.get("backend_id")
    ports = {"ms-fe": 8001, "ms-be": 8002, "ms-db": 8003}
    if backend_id not in ports:
        raise HTTPException(status_code=400, detail=f"Invalid backend: {backend_id}")
        
    host_map = {
        "ms-fe": "mock-backend-1",
        "ms-be": "mock-backend-2",
        "ms-db": "mock-backend-3"
    }
    hostname = host_map.get(backend_id, backend_id)
    url = f"http://{hostname}:{ports[backend_id]}/recover"
    try:
        resp = requests.post(url, timeout=2)
        if resp.status_code == 200:
            return {"status": "ok", "message": f"Recovered {backend_id} successfully"}
        raise HTTPException(status_code=500, detail=f"Mock Backend error: status {resp.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
