import time
import random
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock Backend 3")

# Backend state
backend_id = "mock-be-3"
port = 8003

# Telemetry state
state = {
    "stress_until": 0,
    "stress_intensity": "low",  # low, medium, high
    "cpu": 25.0,
    "memory": 35.0,
    "request_rate": 20.0,
    "latency": 40.0,
    "error_rate": 0.5,
    "active_requests": 5.0,
    "queue_depth": 0.0,
    "health_status": "NORMAL"
}

class StressRequest(BaseModel):
    duration: int
    intensity: str

@app.get("/health")
def health():
    return {"status": "ok", "backend_id": backend_id}

@app.get("/metrics")
def get_metrics():
    now = time.time()
    is_stressed = now < state["stress_until"]
    
    # Calculate telemetry dynamically with realistic noise
    if is_stressed:
        intensity = state["stress_intensity"]
        if intensity == "high":
            cpu_target = random.uniform(80.0, 95.0)
            mem_target = random.uniform(75.0, 90.0)
            latency_target = random.uniform(250.0, 500.0)
            error_target = random.uniform(10.0, 20.0)
            req_target = random.uniform(100.0, 150.0)
            active_target = random.uniform(25.0, 40.0)
            queue_target = random.uniform(10.0, 20.0)
            health = "DEGRADED"
        elif intensity == "medium":
            cpu_target = random.uniform(60.0, 80.0)
            mem_target = random.uniform(60.0, 75.0)
            latency_target = random.uniform(120.0, 250.0)
            error_target = random.uniform(3.0, 10.0)
            req_target = random.uniform(60.0, 100.0)
            active_target = random.uniform(15.0, 25.0)
            queue_target = random.uniform(3.0, 10.0)
            health = "DEGRADED"
        else: # low stress
            cpu_target = random.uniform(45.0, 60.0)
            mem_target = random.uniform(50.0, 60.0)
            latency_target = random.uniform(80.0, 120.0)
            error_target = random.uniform(1.0, 3.0)
            req_target = random.uniform(35.0, 60.0)
            active_target = random.uniform(8.0, 15.0)
            queue_target = random.uniform(1.0, 3.0)
            health = "NORMAL"
    else:
        # Normal workload oscillations
        cpu_target = random.uniform(20.0, 40.0)
        mem_target = random.uniform(30.0, 50.0)
        latency_target = random.uniform(20.0, 80.0)
        error_target = random.uniform(0.1, 0.9)
        req_target = random.uniform(10.0, 30.0)
        active_target = random.uniform(2.0, 8.0)
        queue_target = 0.0
        health = "NORMAL"
        
    state["cpu"] = round(cpu_target, 2)
    state["memory"] = round(mem_target, 2)
    state["request_rate"] = round(req_target, 2)
    state["latency"] = round(latency_target, 2)
    state["error_rate"] = round(error_target, 2)
    state["active_requests"] = int(active_target)
    state["queue_depth"] = int(queue_target)
    state["health_status"] = health

    return {
        "backend_id": backend_id,
        "timestamp": now,
        "cpu": state["cpu"],
        "memory": state["memory"],
        "request_rate": state["request_rate"],
        "latency": state["latency"],
        "error_rate": state["error_rate"],
        "active_requests": state["active_requests"],
        "queue_depth": state["queue_depth"],
        "health_status": state["health_status"]
    }

@app.post("/stress")
def trigger_stress(req: StressRequest):
    duration = min(req.duration, 60)
    intensity = req.intensity.lower()
    if intensity not in ["low", "medium", "high"]:
        raise HTTPException(status_code=400, detail="Invalid intensity. Must be low, medium, or high")
        
    state["stress_until"] = time.time() + duration
    state["stress_intensity"] = intensity
    return {"status": f"Stressed {backend_id} at {intensity} intensity for {duration}s"}

@app.post("/recover")
def trigger_recovery():
    state["stress_until"] = 0
    state["stress_intensity"] = "low"
    return {"status": f"Recovered {backend_id} to normal state"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=port)
