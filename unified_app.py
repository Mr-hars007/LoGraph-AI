import os
import sys
import json
import logging
from flask import Flask, Blueprint, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd
import networkx as nx
import random
import time
from datetime import datetime
from otel_setup import setup_otel, instrument_app
from data_utils import get_db

load_dotenv()

# --- Logging Configuration ---
LOG_FILE = os.path.join("data", "system_logs", "system_activity.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | [%(name)s] | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SystemFlow")

# OpenTelemetry Setup
setup_otel("unified-app")

app = Flask(__name__)
CORS(app)

# Instrument App
instrument_app(app)

# --- Request Middleware for Logging ---
@app.before_request
def start_timer():
    g.start = time.time()
    logger.info(f"REQUEST START: {request.method} {request.path} | Remote: {request.remote_addr}")

@app.after_request
def log_request(response):
    if hasattr(g, 'start'):
        latency = round(time.time() - g.start, 4)
        status = response.status_code
        logger.info(f"REQUEST END:   {request.method} {request.path} | Status: {status} | Latency: {latency}s")
    return response

# --- Database Config (MOCKED via files) ---
db = get_db()

# --- Models & Helpers ---
def log_interaction(source, target, status="success", latency=0.0, msg=""):
    """Logs internal interactions for graph visualization and file logging."""
    latency = round(latency, 4)
    now = datetime.utcnow()
    
    log_entry = {
        "source": source,
        "target": target,
        "timestamp": now.isoformat(),
        "status": status,
        "latency": latency,
        "message": msg
    }
    
    # 1. Standard System Log
    flow_msg = f"FLOW: {source} -> {target} | Status: {status} | Latency: {latency}s"
    if msg: flow_msg += f" | Info: {msg}"
    if status == "success":
        logger.info(flow_msg)
    else:
        logger.warning(flow_msg)

    # 2. Database Log (MOCKED file)
    try:
        db.logs.insert_one(log_entry)
    except Exception as e:
        app.logger.error(f"Failed to log interaction to local file: {e}")

# --- Services ---
class UserService:
    @staticmethod
    def create_user(data):
        start = time.time()
        user = {
            "name": data.get('name'),
            "email": data.get('email'),
            "password": data.get('password'),
            "created_at": datetime.now()
        }
        result = db.users.insert_one(user)
        log_interaction("gateway", "user-service", "success", time.time() - start, f"Created user {data.get('email')}")
        return result.get('id')

    @staticmethod
    def login(email, password):
        start = time.time()
        user = db.users.find_one({"email": email, "password": password})
        status = "success" if user else "failure"
        log_interaction("gateway", "user-service", status, time.time() - start, f"Login attempt for {email}")
        return user

    @staticmethod
    def get_user_by_id(user_id):
        start = time.time()
        try:
            user = db.users.find_one({"id": user_id})
            status = "success" if user else "failure"
            log_interaction("gateway", "user-service", status, time.time() - start, f"Fetch user {user_id}")
            return user
        except Exception as e:
            log_interaction("gateway", "user-service", "error", time.time() - start, str(e))
            return None

class PaymentService:
    @staticmethod
    def process_payment(data):
        start = time.time()
        time.sleep(random.uniform(0.1, 0.2)) # Simulation
        is_success = random.random() < 0.95
        
        payment_doc = {
            "orderId": data.get("orderId"),
            "userId": data.get("userId"),
            "amount": data.get("amount"),
            "method": data.get("method"),
            "status": "success" if is_success else "failed",
            "created_at": datetime.now()
        }
        result = db.payments.insert_one(payment_doc)
        txn_id = result.get('txnId')
        log_interaction("order-service", "payment-service", "success" if is_success else "failure", time.time() - start, f"TXN: {txn_id}")
        
        return {"status": "success", "txnId": txn_id} if is_success else {"status": "failed", "error": "Declined"}

class OrderService:
    @staticmethod
    def create_order(data):
        start = time.time()
        order_doc = {
            "userId": data.get("userId"),
            "items": data.get("items", []),
            "total": data.get("total"),
            "address": data.get("address"),
            "status": "pending",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now()
        }
        result = db.orders.insert_one(order_doc)
        order_id = result.get('orderId')
        log_interaction("gateway", "order-service", "success", time.time() - start, f"Order {order_id} created")
        return order_id

    @staticmethod
    def get_orders(user_id=None):
        start = time.time()
        query = {"userId": user_id} if user_id else {}
        orders = list(db.orders.find(query))
        orders.sort(key=lambda x: str(x.get('created_at')), reverse=True)
        log_interaction("gateway", "order-service", "success", time.time() - start, f"Fetched {len(orders)} orders for user {user_id}")
        return orders

# --- Routes ---
user_bp = Blueprint('user_bp', __name__)
@user_bp.route('/users', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('email'): return jsonify({"error": "Missing email"}), 400
    uid = UserService.create_user(data)
    return jsonify({"id": uid, "token": f"mock-jwt-{uid}", "name": data.get('name')}), 201

@user_bp.route('/users/login', methods=['POST'])
def login():
    data = request.get_json()
    user = UserService.login(data.get('email'), data.get('password'))
    if user:
        return jsonify({"userId": user['id'], "name": user['name'], "token": f"mock-jwt-{user['id']}"}), 200
    return jsonify({"error": "Invalid email or password"}), 401

@user_bp.route('/users/<uid>', methods=['GET', 'PUT', 'DELETE'])
def user_detail(uid):
    if request.method == 'DELETE':
        db.users.delete_one({"id": uid})
        return jsonify({"message": "Deleted"}), 200
    if request.method == 'PUT':
        db.users.update_one({"id": uid}, {"$set": request.get_json()})
        return jsonify({"message": "Updated"}), 200
    user = UserService.get_user_by_id(uid)
    return jsonify(user) if user else (jsonify({"error": "Not found"}), 404)

order_bp = Blueprint('order_bp', __name__)
@order_bp.route('/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'POST':
        data = request.get_json()
        oid = OrderService.create_order(data)
        return jsonify({"id": oid, "orderId": oid}), 201
    uid = request.args.get('userId')
    return jsonify(OrderService.get_orders(uid)), 200

payment_bp = Blueprint('payment_bp', __name__)
@payment_bp.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    result = PaymentService.process_payment(data)
    if result["status"] == "success":
        db.orders.update_one({"orderId": data.get("orderId")}, {"$set": {"status": "processing"}})
        return jsonify(result), 200
    return jsonify(result), 402

graph_bp = Blueprint('graph_bp', __name__)
@graph_bp.route('/graph', methods=['GET'])
def get_graph():
    pipeline = [{"$group": {"_id": {"from": "$source", "to": "$target"}}}]
    interactions = list(db.logs.aggregate(pipeline))
    nodes = set(); edges = []
    for interaction in interactions:
        source, target = interaction['_id']['from'], interaction['_id']['to']
        nodes.add(source); nodes.add(target)
        edges.append({"from": source, "to": target})
    return jsonify({"nodes": list(nodes), "edges": edges}), 200

upload_bp = Blueprint('upload_bp', __name__)
@upload_bp.route('/upload-data', methods=['POST'])
def upload_data():
    if 'file' not in request.files: return jsonify({"error": "No file"}), 400
    df = pd.read_csv(request.files['file'])
    G = nx.from_pandas_edgelist(df, source="source", target="target")
    log_interaction("gateway", "backend-service", "success")
    return jsonify({"nodes": G.number_of_nodes(), "edges": G.number_of_edges()}), 200

prediction_bp = Blueprint('prediction_bp', __name__)
@prediction_bp.route('/predictions', methods=['GET'])
def get_predictions():
    log_interaction("gateway", "prediction-service", "success")
    return jsonify({"risk": "low", "service": "unified", "reason": "Stable patterns"}), 200

from flask import Flask, Blueprint, request, jsonify, g, render_template_string
...
@app.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>LoGraph-AI Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <style>
        body { font-family: sans-serif; margin: 20px; background: #f0f2f5; }
        .container { display: flex; gap: 20px; height: 85vh; }
        .panel { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        #graph { flex: 2; }
        #logs { flex: 1; overflow-y: auto; font-family: monospace; font-size: 12px; background: #1c1c1c; color: #00ff00; }
        h2 { margin-top: 0; color: #333; }
        .log-entry { border-bottom: 1px solid #333; padding: 4px 0; }
    </style>
</head>
<body>
    <h1>📊 LoGraph-AI System Dashboard</h1>
    <div class="container">
        <div id="graph" class="panel">
            <h2>Service Interaction Graph</h2>
            <div id="cy" style="width: 100%; height: 90%;"></div>
        </div>
        <div id="logs" class="panel">
            <h2>Live System Logs</h2>
            <div id="log-container">Loading logs...</div>
        </div>
    </div>

    <script>
        async function updateGraph() {
            const res = await fetch('/graph');
            const data = await res.json();
            const elements = [];
            data.nodes.forEach(n => elements.push({ data: { id: n, label: n } }));
            data.edges.forEach(e => elements.push({ data: { source: e.from, target: e.to } }));
            
            cytoscape({
                container: document.getElementById('cy'),
                elements: elements,
                style: [
                    { selector: 'node', style: { 'background-color': '#007bff', 'label': 'data(label)', 'color': '#333', 'text-valign': 'center' } },
                    { selector: 'edge', style: { 'width': 3, 'line-color': '#ccc', 'target-arrow-color': '#ccc', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier' } }
                ],
                layout: { name: 'cose' }
            });
        }

        async function updateLogs() {
            try {
                const res = await fetch('/dashboard/raw-logs');
                const text = await res.text();
                const container = document.getElementById('log-container');
                container.innerHTML = text.split('\\n').reverse().map(line => `<div class="log-entry">${line}</div>`).join('');
            } catch(e) {}
        }

        setInterval(updateGraph, 5000);
        setInterval(updateLogs, 2000);
        updateGraph();
        updateLogs();
    </script>
</body>
</html>
""")

@app.route('/dashboard/raw-logs', methods=['GET'])
def raw_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            return f.read()
    return "No logs yet"

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "LoGraph-AI Unified API is running",
        "endpoints": {
            "health": "/health",
            "users": "/users",
            "orders": "/orders",
            "payment": "/pay",
            "graph": "/graph",
            "predictions": "/predictions"
        }
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return {"status": "Integrated Unified System is running"}, 200

app.register_blueprint(user_bp)
app.register_blueprint(order_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(graph_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(prediction_bp)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5005))
    app.run(debug=True, port=port, host='0.0.0.0')
