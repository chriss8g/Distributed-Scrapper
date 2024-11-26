from flask import Flask, send_from_directory
from controllers.scrape_controller import scrape_bp
from controllers.db_controller import db_bp
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.register_blueprint(scrape_bp)
app.register_blueprint(db_bp)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == "__main__":
    app.run(debug=True)