import json
from datetime import datetime
from services.user_service.config.db import get_db

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

class UserService:
    @staticmethod
    def create_user(data):
        log_to_gnn("user-service", "user-mongodb")
        user = {"name": data.get('name'), "email": data.get('email'), "password": data.get('password'), "created_at": datetime.now()}
        result = db.users.insert_one(user)
        return result.get('id')

    @staticmethod
    def login(email, password):
        log_to_gnn("user-service", "user-mongodb")
        user = db.users.find_one({"email": email, "password": password})
        return user

    @staticmethod
    def get_user_by_id(user_id):
        log_to_gnn("user-service", "user-mongodb")
        user = db.users.find_one({"id": user_id})
        return user
