from flask import Blueprint, request, jsonify
from services.db_service import save_to_db

db_bp = Blueprint('db', __name__)

@db_bp.route('/url', methods=['POST'])
def create_url():
    url_data = request.json
    result = save_url_to_db(url_data)
    return jsonify({"status": result})

@db_bp.route('/url/<int:url_id>', methods=['GET'])
def get_url(url_id):
    url = get_url_from_db(url_id)
    return jsonify(url)

@db_bp.route('/url/<int:url_id>', methods=['PUT'])
def update_url(url_id):
    url_data = request.json
    result = update_url_in_db(url_id, url_data)
    return jsonify({"status": result})

@db_bp.route('/url/<int:url_id>', methods=['DELETE'])
def delete_url(url_id):
    result = delete_url_from_db(url_id)
    return jsonify({"status": result})

@db_bp.route('/links', methods=['POST'])
def create_link():
    link_data = request.json
    result = save_link_to_db(link_data)
    return jsonify({"status": result})

@db_bp.route('/links/<int:link_id>', methods=['GET'])
def get_link(link_id):
    link = get_link_from_db(link_id)
    return jsonify(link)

@db_bp.route('/links/<int:link_id>', methods=['PUT'])
def update_link(link_id):
    link_data = request.json
    result = update_link_in_db(link_id, link_data)
    return jsonify({"status": result})

@db_bp.route('/links/<int:link_id>', methods=['DELETE'])
def delete_link(link_id):
    result = delete_link_from_db(link_id)
    return jsonify({"status": result})

@db_bp.route('/files', methods=['POST'])
def create_file():
    file_data = request.json
    result = save_file_to_db(file_data)
    return jsonify({"status": result})

@db_bp.route('/files/<int:file_id>', methods=['GET'])
def get_file(file_id):
    file = get_file_from_db(file_id)
    return jsonify(file)

@db_bp.route('/files/<int:file_id>', methods=['PUT'])
def update_file(file_id):
    file_data = request.json
    result = update_file_in_db(file_id, file_data)
    return jsonify({"status": result})

@db_bp.route('/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    result = delete_file_from_db(file_id)
    return jsonify({"status": result})

@db_bp.route('/save', methods=['POST'])
def save():
    scraped_data = request.json  # Datos en formato JSON
    result = save_scraped_data(scraped_data)
    return jsonify({"status": result})
