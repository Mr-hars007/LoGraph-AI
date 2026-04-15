from api_gateway.config.db import get_db

db = get_db()

class GraphService:
    @staticmethod
    def get_service_graph():
        interactions = list(db.logs.find())
        nodes = set(); edges = []
        for interaction in interactions:
            source, target = interaction['source'], interaction['target']
            nodes.add(source); nodes.add(target)
            edges.append({"from": source, "to": target})
        return {"nodes": list(nodes), "edges": edges}
