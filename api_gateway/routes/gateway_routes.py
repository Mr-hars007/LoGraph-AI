import os
import requests
import json
import pandas as pd
import networkx as nx
from flask import Blueprint, request, jsonify
from datetime import datetime
from api_gateway.config.db import get_db

gateway_bp = Blueprint('gateway_bp', __name__)
@gateway_bp.route('/upload-data', methods=['POST'])
def upload_data():
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    try:
        df = pd.read_csv(request.files['file'])
        G = nx.from_pandas_edgelist(df, source="source", target="target")
        log_to_gnn("gateway", "backend-service")
        return jsonify({"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to process CSV: {str(e)}"}), 500
db = get_db()

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:5001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order_service:5002")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment_service:5003")

GNN_LOG_FILE = "/app/data/otel_logs.jsonl"
def log_to_gnn(source, target, status="success"):
    now = datetime.utcnow()
    # 1. Database Log for Graph Visualization (UI)
    try:
        db.logs.insert_one({
            "source": source,
            "target": target,
            "timestamp": now.isoformat(),
            "status": status
        })
    except: pass

@gateway_bp.route('/users', methods=['POST'])
@gateway_bp.route('/users/login', methods=['POST'])
@gateway_bp.route('/users/<path:path>', methods=['GET', 'PUT', 'DELETE'])
def user_proxy(path=""):
    log_to_gnn("api-gateway", "user-service")
    url = f"{USER_SERVICE_URL}/users" if not path else f"{USER_SERVICE_URL}/users/{path}"
    if request.path.endswith('/login'): url = f"{USER_SERVICE_URL}/users/login"
    return forward_request(url, request.method, request.get_json(), request.headers)

@gateway_bp.route('/orders', methods=['GET', 'POST'])
@gateway_bp.route('/orders/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def order_proxy(path=""):
    log_to_gnn("api-gateway", "order-service")
    url = f"{ORDER_SERVICE_URL}/orders" if not path else f"{ORDER_SERVICE_URL}/orders/{path}"
    return forward_request(url, request.method, request.get_json(), request.headers)

@gateway_bp.route('/pay', methods=['POST'])
def payment_proxy_pay():
    log_to_gnn("api-gateway", "payment-service")
    data = request.get_json()
    resp_text, status_code, resp_headers = forward_request(f"{PAYMENT_SERVICE_URL}/pay", request.method, data, request.headers)
    
    if status_code == 200:
        # Success, update order status
        order_id = data.get("orderId")
        if order_id:
            try:
                requests.put(f"{ORDER_SERVICE_URL}/orders/{order_id}/status", json={"status": "processing"})
            except Exception as e:
                print(f"Failed to update order status: {e}")
                
    return (resp_text, status_code, resp_headers)

@gateway_bp.route('/payments', methods=['GET', 'POST'])
@gateway_bp.route('/payments/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def payment_proxy_rest(path=""):
    log_to_gnn("api-gateway", "payment-service")
    url = f"{PAYMENT_SERVICE_URL}/payments" if not path else f"{PAYMENT_SERVICE_URL}/payments/{path}"
    return forward_request(url, request.method, request.get_json(), request.headers)

def forward_request(url, method, data, headers):
    """Utility to forward requests to target microservices."""
    try:
        resp = requests.request(
            method=method,
            url=url,
            json=data,
            headers={k: v for k, v in headers if k.lower() != 'host'}
        )
        return (resp.text, resp.status_code, resp.headers.items())
    except Exception as e:
        return jsonify({"error": f"Gateway failed to connect: {str(e)}"}), 502
