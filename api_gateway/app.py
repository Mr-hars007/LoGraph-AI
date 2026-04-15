import os
import sys
import logging
import json
import time
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from api_gateway.routes.gateway_routes import gateway_bp
from api_gateway.routes.graph_routes import graph_bp
from api_gateway.routes.prediction_routes import prediction_bp
from dotenv import load_dotenv
from datetime import datetime
from otel_setup import setup_otel, instrument_app

load_dotenv()

# --- Logging Configuration ---
LOG_FILE = "/app/data/system_logs/system_activity.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | [GATEWAY] | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Gateway")

# --- OTel Setup ---
setup_otel("api-gateway")

app = Flask(__name__)
CORS(app)

# Instrument the app
instrument_app(app)

# --- Request Middleware for Logging ---
@app.before_request
def start_timer():
    g.start = time.time()
    logger.info(f"REQ START: {request.method} {request.path}")

@app.after_request
def log_request(response):
    if hasattr(g, 'start'):
        latency = round(time.time() - g.start, 4)
        logger.info(f"REQ END:   {request.method} {request.path} | Status: {response.status_code} | Latency: {latency}s")
    return response

# Add the /app directory to sys.path to allow absolute imports from root
if "/app" not in sys.path:
    sys.path.append("/app")

app.register_blueprint(gateway_bp)
app.register_blueprint(graph_bp)
app.register_blueprint(prediction_bp)

@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "API Gateway is running"}, 200

if __name__ == "__main__":
    port = int(os.getenv("GATEWAY_PORT", 5005))
    app.run(debug=True, port=port, host='0.0.0.0')
