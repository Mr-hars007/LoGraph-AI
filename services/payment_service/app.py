import os
import sys
import logging
import json
import time
from flask import Flask, request, jsonify, g
from services.payment_service.routes.payment_routes import payment_bp
from dotenv import load_dotenv
from datetime import datetime
from otel_setup import setup_otel, instrument_app

load_dotenv()

# --- Logging Configuration ---
LOG_FILE = "/app/data/system_logs/system_activity.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | [PAY-SVC] | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PaymentService")

# --- OTel Setup ---
setup_otel("payment-service")

app = Flask(__name__)
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

if "/app" not in sys.path:
    sys.path.append("/app")

app.register_blueprint(payment_bp)

@app.route('/health', methods=['GET'])
def health_check():
    return {"status": "Payment Service is running"}, 200

if __name__ == "__main__":
    port = int(os.getenv("PAYMENT_SERVICE_PORT", 5003))
    app.run(debug=True, port=port, host='0.0.0.0')
