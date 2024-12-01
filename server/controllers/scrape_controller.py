
from flask import Blueprint, request, jsonify
from services.scraper_service import scrape_elements

scrape_bp = Blueprint('scrape', __name__)

@scrape_bp.route('/scrape', methods=['GET'])
def scrape():
    url = request.args.get('url') 
    options = request.args.get('options') 
    options_list = options.split(',') if options else []
    
    data = scrape_elements(url, options_list)
    return jsonify(data)  # Devolver datos en JSON
