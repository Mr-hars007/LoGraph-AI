import time
import sys
import requests

BACKEND_URL = "http://localhost:8000"
AI_URL = "http://localhost:8004"
MOCK_BE_URLS = {
    "mock-be-1": "http://localhost:8001",
    "mock-be-2": "http://localhost:8002",
    "mock-be-3": "http://localhost:8003"
}

def log(msg):
    print(f"[*] {msg}", flush=True)

def error(msg):
    print(f"[ERROR] {msg}", file=sys.stderr, flush=True)

def verify_health():
    log("Verifying service health status...")
    
    # Check Central Backend
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if r.status_code == 200:
            log("Central Backend: HEALTHY")
        else:
            raise Exception(f"status code {r.status_code}")
    except Exception as e:
        error(f"Central Backend: UNHEALTHY ({e})")
        return False

    # Check AI Service
    try:
        r = requests.get(f"{AI_URL}/health", timeout=2)
        if r.status_code == 200:
            log("AI Service: HEALTHY")
        else:
            raise Exception(f"status code {r.status_code}")
    except Exception as e:
        error(f"AI Service: UNHEALTHY ({e})")
        return False

    # Check Mock Backends
    for be_id, url in MOCK_BE_URLS.items():
        try:
            r = requests.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                log(f"Mock Backend {be_id}: HEALTHY")
            else:
                raise Exception(f"status code {r.status_code}")
        except Exception as e:
            error(f"Mock Backend {be_id}: UNHEALTHY ({e})")
            return False

    log("All services are healthy.")
    return True

def trigger_and_wait_training():
    log("Triggering GNN model training pipeline...")
    try:
        r = requests.post(f"{BACKEND_URL}/api/train", json={"model_type": "gnn", "epochs": 20}, timeout=5)
        if r.status_code != 200:
            error(f"Failed to trigger training: {r.text}")
            return False
        log("Training triggered. Bootstrapping synthetic dataset & training GNN model...")
    except Exception as e:
        error(f"Failed to connect to training API: {e}")
        return False

    # Poll models API until GNN model is active
    for attempt in range(30):
        try:
            r = requests.get(f"{BACKEND_URL}/api/models", timeout=2)
            if r.status_code == 200:
                models = r.json()
                active_gnn = next((m for m in models if m["model_type"] == "gnn" and m["active"]), None)
                if active_gnn:
                    log(f"GNN model is trained and ACTIVE: {active_gnn['model_id']}")
                    log(f"Metrics: {active_gnn['metrics']}")
                    return True
        except Exception as e:
            log(f"Polling models error: {e}")
        
        log(f"Waiting for model training to complete (attempt {attempt+1}/30)...")
        time.sleep(3)
        
    error("Model training timed out.")
    return False

def verify_rules():
    log("Verifying that default remediation script and rules are active...")
    try:
        r = requests.get(f"{BACKEND_URL}/api/rules", timeout=2)
        if r.status_code == 200:
            rules = r.json()
            active_rules = [r for r in rules if r["enabled"]]
            log(f"Found {len(active_rules)} enabled automation rules.")
            for r in active_rules:
                log(f"Rule: IF {r['prediction']} (score >= {r['minimum_score']}) ON {r['target_backend']} -> Trigger {r['script_name']}")
            return len(active_rules) > 0
    except Exception as e:
        error(f"Failed to check rules: {e}")
    return False

def run_incident_loop():
    target_backend = "mock-be-2"
    log(f"Step 1: Straining backend {target_backend} to trigger incident...")
    
    try:
        r = requests.post(f"{BACKEND_URL}/api/demo/stress", json={
            "backend_id": target_backend,
            "duration": 30,
            "intensity": "high"
        }, timeout=2)
        if r.status_code != 200:
            error(f"Failed to trigger stress: {r.text}")
            return False
        log(f"Stress request accepted for {target_backend}.")
    except Exception as e:
        error(f"Failed to request stress: {e}")
        return False

    log("Step 2: Monitoring metrics degradation and waiting for GNN prediction + action trigger...")
    
    action_triggered = None
    
    # We poll for the next 20 seconds
    for sec in range(25):
        time.sleep(1)
        # Check telemetry
        try:
            t_res = requests.get(f"{BACKEND_URL}/api/telemetry/latest", timeout=2)
            if t_res.status_code == 200:
                tel = t_res.json()
                be_tel = next((item for item in tel if item["backend_id"] == target_backend), None)
                if be_tel:
                    log(f"[Telemetry] {target_backend} CPU: {be_tel['cpu']}% | Latency: {be_tel['latency']}ms | Health: {be_tel['health_status']}")
        except Exception:
            pass
            
        # Check if action got queued
        try:
            a_res = requests.get(f"{BACKEND_URL}/api/actions", timeout=2)
            if a_res.status_code == 200:
                actions = a_res.json()
                recent_action = next((a for a in actions if a["backend_id"] == target_backend), None)
                if recent_action:
                    log(f"[Action Detected] Action ID: {recent_action['id']} | Script: {recent_action['script_name']} | Status: {recent_action['status']}")
                    if recent_action["status"] in ["QUEUED", "EXECUTING", "SUCCESS"]:
                        action_triggered = recent_action
                        break
        except Exception as e:
            log(f"Error checking actions: {e}")
            
    if not action_triggered:
        error("Self-healing action was not triggered within time limit.")
        return False
        
    log("Step 3: Action triggered. Monitoring sandboxed script execution...")
    
    action_completed = False
    for attempt in range(15):
        try:
            a_res = requests.get(f"{BACKEND_URL}/api/actions", timeout=2)
            if a_res.status_code == 200:
                actions = a_res.json()
                target_act = next((a for a in actions if a["id"] == action_triggered["id"]), None)
                if target_act:
                    log(f"[Action Status Update] Status: {target_act['status']}")
                    if target_act["status"] == "SUCCESS":
                        log(f"[Sandbox Output]: {target_act['output']}")
                        action_completed = True
                        break
                    elif target_act["status"] == "FAILED":
                        error(f"[Sandbox Execution Failed]: {target_act['error']}")
                        return False
        except Exception as e:
            log(f"Error checking action state: {e}")
        time.sleep(1)

    if not action_completed:
        error("Action execution timed out.")
        return False

    log("Step 4: Remediated. Waiting 3 seconds for recovery telemetry propagation...")
    time.sleep(3)

    try:
        t_res = requests.get(f"{BACKEND_URL}/api/telemetry/latest", timeout=2)
        if t_res.status_code == 200:
            tel = t_res.json()
            be_tel = next((item for item in tel if item["backend_id"] == target_backend), None)
            if be_tel and be_tel["health_status"] == "NORMAL" and be_tel["cpu"] < 50.0:
                log(f"SUCCESS: Backend {target_backend} successfully recovered back to normal state! CPU is {be_tel['cpu']}%")
                return True
            else:
                error(f"Recovery failed. Telemetry state: {be_tel}")
    except Exception as e:
        error(f"Failed to check recovery telemetry: {e}")

    return False

def main():
    log("=== Logoph AI End-to-End Self-Healing Integration Test ===")
    
    if not verify_health():
        log("E2E Test FAILED: Stack is unhealthy or offline.")
        sys.exit(1)
        
    if not trigger_and_wait_training():
        log("E2E Test FAILED: Model training failed.")
        sys.exit(1)
        
    if not verify_rules():
        log("E2E Test FAILED: Remediation rules missing.")
        sys.exit(1)
        
    if not run_incident_loop():
        log("E2E Test FAILED: Incident self-healing loop failed.")
        sys.exit(1)
        
    log("=== E2E Test COMPLETED SUCCESSFUL ===")
    log("All components (Telemetry, GNN model inference, Action rules, Sandbox execution, LGCA and Recovery) verified.")
    sys.exit(0)

if __name__ == "__main__":
    main()
