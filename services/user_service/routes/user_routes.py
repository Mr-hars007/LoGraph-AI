from flask import Blueprint, request, jsonify
from services.user_service.services.user_service import UserService

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users', methods=['POST'])
def register():
    data = request.get_json()
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
    user = UserService.get_user_by_id(uid)
    return jsonify(user) if user else (jsonify({"error": "Not found"}), 404)
