from flask import Blueprint, request, jsonify
from services.db_service import save_to_db

db_bp = Blueprint('db', __name__)

@db_bp.route('/save', methods=['POST'])
def save():
    news_data = request.json  # Datos en formato JSON
    result = save_to_db(news_data)
    return jsonify({"status": result})