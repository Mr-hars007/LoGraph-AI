import os
import time
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("LGCA")

# Configuration
BACKEND_ID = os.environ.get("BACKEND_ID", "mock-be-1")
MOCK_BACKEND_URL = os.environ.get("MOCK_BACKEND_URL", "http://mock-backend-1:8001")
CENTRAL_BACKEND_URL = os.environ.get("CENTRAL_BACKEND_URL", "http://backend:8000")
SANDBOX_URL = os.environ.get("SANDBOX_URL", "http://script-sandbox:8005")
POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "1.0"))

def collect_and_send_telemetry():
    try:
        # 1. Fetch metrics from the Mock Backend
        metrics_resp = requests.get(f"{MOCK_BACKEND_URL}/metrics", timeout=2)
        if metrics_resp.status_code != 200:
            logger.error(f"Failed to fetch metrics from backend {BACKEND_ID}: status {metrics_resp.status_code}")
            return
        
        telemetry = metrics_resp.json()
        
        # 2. Transmit to Logoph AI Backend
        payload = {
            "backend_id": BACKEND_ID,
            "cpu": telemetry["cpu"],
            "memory": telemetry["memory"],
            "request_rate": telemetry["request_rate"],
            "latency": telemetry["latency"],
            "error_rate": telemetry["error_rate"],
            "active_requests": telemetry["active_requests"],
            "queue_depth": telemetry["queue_depth"],
            "health_status": telemetry["health_status"]
        }
        
        backend_resp = requests.post(f"{CENTRAL_BACKEND_URL}/api/telemetry", json=payload, timeout=2)
        if backend_resp.status_code not in [200, 201]:
            logger.error(f"Failed to transmit telemetry to central backend: status {backend_resp.status_code}")
            
    except Exception as e:
        logger.error(f"Error during telemetry collection/transmission: {e}")

def process_pending_actions():
    try:
        # Get pending actions for this backend
        resp = requests.get(f"{CENTRAL_BACKEND_URL}/api/actions/pending?backend_id={BACKEND_ID}", timeout=2)
        if resp.status_code != 200:
            return
            
        actions = resp.json()
        if not actions:
            return
            
        for action in actions:
            action_id = action["id"]
            script_content = action["script_content"]
            
            logger.info(f"Processing action {action_id} for backend {BACKEND_ID}")
            
            # Action validation
            if not script_content or len(script_content.strip()) == 0:
                report_result(action_id, "FAILED", "", "Action validation error: Empty script content.")
                continue
                
            if action["target_backend"] != BACKEND_ID:
                report_result(action_id, "FAILED", "", f"Action validation error: Target backend mismatch. Expected {BACKEND_ID}, got {action['target_backend']}")
                continue
            
            # Mark action as executing
            update_status(action_id, "EXECUTING")
            
            # Delegate to sandbox
            sandbox_payload = {
                "script_content": script_content,
                "target_backend_url": MOCK_BACKEND_URL,
                "timeout": 5
            }
            
            try:
                sandbox_resp = requests.post(f"{SANDBOX_URL}/execute", json=sandbox_payload, timeout=12)
                if sandbox_resp.status_code == 200:
                    result = sandbox_resp.json()
                    report_result(action_id, result["status"], result.get("stdout", ""), result.get("stderr", ""))
                else:
                    report_result(action_id, "FAILED", "", f"Sandbox HTTP error: status {sandbox_resp.status_code}")
            except Exception as e:
                report_result(action_id, "FAILED", "", f"Failed to execute script in sandbox: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error processing pending actions: {e}")

def update_status(action_id, status):
    try:
        requests.patch(f"{CENTRAL_BACKEND_URL}/api/actions/{action_id}/status", json={"status": status}, timeout=2)
    except Exception as e:
        logger.error(f"Failed to update action {action_id} status: {e}")

def report_result(action_id, status, stdout, stderr):
    try:
        payload = {
            "status": status,
            "stdout": stdout,
            "stderr": stderr
        }
        requests.post(f"{CENTRAL_BACKEND_URL}/api/actions/{action_id}/complete", json=payload, timeout=2)
        logger.info(f"Completed action {action_id} with status {status}")
    except Exception as e:
        logger.error(f"Failed to report result for action {action_id}: {e}")

def main():
    logger.info(f"LGCA started for {BACKEND_ID}")
    
    # Wait for backend to be ready
    while True:
        try:
            resp = requests.get(f"{CENTRAL_BACKEND_URL}/health", timeout=2)
            if resp.status_code == 200:
                logger.info("Central backend is ready!")
                break
        except Exception:
            pass
        logger.info("Waiting for central backend to become ready...")
        time.sleep(2)

    while True:
        collect_and_send_telemetry()
        process_pending_actions()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
