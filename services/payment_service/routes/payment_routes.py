from flask import Blueprint, request, jsonify
from services.payment_service.services.payment_service import PaymentService

payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    result = PaymentService.process_payment(data)
    if result["status"] == "success":
        return jsonify(result), 200
    return jsonify(result), 402

@payment_bp.route('/payments/<txn_id>', methods=['GET'])
def get_payment(txn_id):
    payment = PaymentService.get_payment(txn_id)
    return jsonify(payment) if payment else (jsonify({"error": "Not found"}), 404)

@payment_bp.route('/payments/<txn_id>/refund', methods=['POST'])
def refund(txn_id):
    PaymentService.refund(txn_id)
    return jsonify({"message": f"Refunded txn {txn_id}"}), 200
