import random
import json
from services.order_service.config.db import get_db
from datetime import datetime

db = get_db()
GNN_LOG_FILE = "/app/data/otel_logs.jsonl"

def log_to_gnn(source, target, status="success"):
    now = datetime.utcnow()
    try:
        db.logs.insert_one({
            "source": source,
            "target": target,
            "timestamp": now.isoformat(),
            "status": status
        })
    except: pass

class OrderService:
    @staticmethod
    def create_order(data):
        log_to_gnn("order-service", "order-mongodb")
        order_id = f"ORD-{random.randint(1000, 9999)}"
        order = {"orderId": order_id, "userId": data.get("userId"), "items": data.get("items", []), "total": data.get("total"), "status": "pending", "created_at": datetime.now()}
        db.orders.insert_one(order)
        return order_id

    @staticmethod
    def get_orders(user_id=None):
        log_to_gnn("order-service", "order-mongodb")
        query = {"userId": user_id} if user_id else {}
        orders = list(db.orders.find(query))
        return orders

    @staticmethod
    def get_order(order_id):
        log_to_gnn("order-service", "order-mongodb")
        order = db.orders.find_one({"orderId": order_id})
        return order

    @staticmethod
    def update_order_status(order_id, status):
        log_to_gnn("order-service", "order-mongodb")
        db.orders.update_one({"orderId": order_id}, {"$set": {"status": status}})
        return True

    @staticmethod
    def cancel_order(order_id):
        log_to_gnn("order-service", "order-mongodb")
        db.orders.update_one({"orderId": order_id}, {"$set": {"status": "cancelled"}})
        return True
