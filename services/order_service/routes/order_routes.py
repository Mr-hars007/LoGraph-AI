from flask import Blueprint, request, jsonify
from services.order_service.services.order_service import OrderService

order_bp = Blueprint('order_bp', __name__)

@order_bp.route('/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'POST':
        data = request.get_json()
        oid = OrderService.create_order(data)
        return jsonify({"id": oid, "orderId": oid}), 201
    uid = request.args.get('userId')
    return jsonify(OrderService.get_orders(uid)), 200

@order_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    order = OrderService.get_order(order_id)
    return jsonify(order) if order else (jsonify({"error": "Not found"}), 404)

@order_bp.route('/orders/<order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    OrderService.cancel_order(order_id)
    return jsonify({"message": f"Order {order_id} cancelled"}), 200

@order_bp.route('/orders/<order_id>/status', methods=['PUT'])
def update_status(order_id):
    data = request.get_json()
    status = data.get('status')
    if not status: return jsonify({"error": "Missing status"}), 400
    OrderService.update_order_status(order_id, status)
    return jsonify({"message": f"Order {order_id} status updated to {status}"}), 200
