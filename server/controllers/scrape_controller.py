
from flask import Blueprint, request, jsonify
from services.scraper_service import scrape_news

scrape_bp = Blueprint('scrape', __name__)

@scrape_bp.route('/scrape', methods=['GET'])
def scrape():
    keyword = request.args.get('keyword')  # Recibir la palabra clave
    if not keyword:
        return jsonify({"error": "Falta la palabra clave"}), 400
    
    data = scrape_news(keyword)
    return jsonify(data)  # Devolver datos en JSON
