import json
from flask import Blueprint, jsonify
from api_gateway.services.graph_service import GraphService
from datetime import datetime

graph_bp = Blueprint('graph_bp', __name__)

GNN_LOG_FILE = "/app/data/otel_logs.jsonl"
def log_to_gnn(source, target):
    gnn_entry = {"timestamp": int(datetime.utcnow().timestamp()), "source": source, "target": target}
    try:
        with open(GNN_LOG_FILE, "a") as f:
            f.write(json.dumps(gnn_entry) + "\n")
    except: pass

@graph_bp.route('/graph', methods=['GET'])
def get_graph():
    log_to_gnn("gateway", "graph-service")
    try:
        graph_data = GraphService.get_service_graph()
        return jsonify(graph_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
