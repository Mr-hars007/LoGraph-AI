import os
import json
import uuid
from datetime import datetime

# Centralized data paths
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
LOGS_DIR = os.path.join(DATA_DIR, "system_logs")
USERS_FILE = os.path.join(DATA_DIR, "user_details.json")
ORDERS_FILE = os.path.join(LOGS_DIR, "orders.json")
PAYMENTS_FILE = os.path.join(LOGS_DIR, "payments.json")
DB_LOGS_FILE = os.path.join(LOGS_DIR, "db_logs.json")

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)

def _read_json(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return []

def _write_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4, default=str)

class FileCollection:
    def __init__(self, file_path, id_field="id"):
        self.file_path = file_path
        self.id_field = id_field

    def find(self, query=None):
        data = _read_json(self.file_path)
        if not query:
            return data
        return [item for item in data if all(item.get(k) == v for k, v in query.items())]

    def find_one(self, query):
        results = self.find(query)
        return results[0] if results else None

    def insert_one(self, document):
        data = _read_json(self.file_path)
        if self.id_field not in document:
            document[self.id_field] = str(uuid.uuid4())
        data.append(document)
        _write_json(self.file_path, data)
        return document

    def update_one(self, query, update):
        data = _read_json(self.file_path)
        updated = False
        for item in data:
            if all(item.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    item.update(update["$set"])
                else:
                    item.update(update)
                updated = True
                break
        if updated:
            _write_json(self.file_path, data)
        return updated

    def delete_one(self, query):
        data = _read_json(self.file_path)
        new_data = [item for item in data if not all(item.get(k) == v for k, v in query.items())]
        if len(new_data) < len(data):
            _write_json(self.file_path, new_data)
            return True
        return False

    def aggregate(self, pipeline):
        # Very limited support for the group pipeline used in unified_app.py
        data = _read_json(self.file_path)
        if pipeline and "$group" in pipeline[0]:
            group_cfg = pipeline[0]["$group"]
            id_cfg = group_cfg.get("_id", {})
            results = {}
            for item in data:
                key_parts = []
                for k, v in id_cfg.items():
                    # Simplified: assume v is "$field"
                    field_name = v.replace("$", "")
                    key_parts.append((k, item.get(field_name)))
                key = tuple(key_parts)
                if key not in results:
                    results[key] = {"_id": dict(key_parts)}
            return list(results.values())
        return data

class MockDB:
    def __init__(self):
        self.users = FileCollection(USERS_FILE)
        self.orders = FileCollection(ORDERS_FILE, id_field="orderId")
        self.payments = FileCollection(PAYMENTS_FILE, id_field="txnId")
        self.logs = FileCollection(DB_LOGS_FILE)

db = MockDB()

def get_db():
    return db
