import json
from flask import Blueprint, jsonify
from api_gateway.config.db import get_db
from datetime import datetime

prediction_bp = Blueprint('prediction_bp', __name__)

GNN_LOG_FILE = "/app/data/otel_logs.jsonl"
def log_to_gnn(source, target):
    gnn_entry = {"timestamp": int(datetime.utcnow().timestamp()), "source": source, "target": target}
    try:
        with open(GNN_LOG_FILE, "a") as f:
            f.write(json.dumps(gnn_entry) + "\n")
    except: pass

@prediction_bp.route('/predictions', methods=['GET'])
def get_predictions():
    log_to_gnn("gateway", "prediction-service")
    return jsonify({"risk": "low", "service": "unified", "reason": "Stable patterns"}), 200
