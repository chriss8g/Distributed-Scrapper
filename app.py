from flask import Flask
from controllers.scrape_controller import scrape_bp
from controllers.db_controller import db_bp

app = Flask(__name__)

app.register_blueprint(scrape_bp)
app.register_blueprint(db_bp)

if __name__ == "__main__":
    app.run(debug=True)