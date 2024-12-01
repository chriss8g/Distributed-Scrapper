from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)