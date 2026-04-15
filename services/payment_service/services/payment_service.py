import random
import json
from services.payment_service.config.db import get_db
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

class PaymentService:
    @staticmethod
    def process_payment(data):
        log_to_gnn("payment-service", "payment-mongodb")
        is_success = random.random() < 0.95
        txn_id = f"TXN-{random.randint(100000, 999999)}"
        payment = {"txnId": txn_id, "orderId": data.get("orderId"), "userId": data.get("userId"), "status": "success" if is_success else "failed", "created_at": datetime.now()}
        db.payments.insert_one(payment)
        return {"status": "success", "txnId": txn_id} if is_success else {"status": "failed", "error": "Declined"}

    @staticmethod
    def get_payment(txn_id):
        log_to_gnn("payment-service", "payment-mongodb")
        payment = db.payments.find_one({"txnId": txn_id})
        return payment

    @staticmethod
    def refund(txn_id):
        log_to_gnn("payment-service", "payment-mongodb")
        db.payments.update_one({"txnId": txn_id}, {"$set": {"status": "refunded"}})
        return True
