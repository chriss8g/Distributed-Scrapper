from flask import Blueprint, request, jsonify
from services.scraper_service import scrape_html, scrape_links, scrape_files

scrape_bp = Blueprint('scrape', __name__)

@scrape_bp.route('/scrape', methods=['GET'])
def scrape():
    url = request.args.get('url')
    scrape_type = request.args.get('type')  # Puede ser 'html', 'links' o 'files'

    if not url:
        return jsonify({"error": "URL is required"}), 400

    if scrape_type not in ['html', 'links', 'files']:
        return jsonify({"error": "Invalid scrape type"}), 400

    try:
        if scrape_type == 'html':
            result = scrape_html(url)
        elif scrape_type == 'links':
            result = scrape_links(url)
        elif scrape_type == 'files':
            result = scrape_files(url)
        else:
            return jsonify({"error": "Invalid scrape type"}), 400

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Scraping failed: {str(e)}"}), 500
