from flask import Flask, send_from_directory
from flask_cors import CORS
import socket

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == "__main__":
    try:
        app.run(debug=True, port=3000)
    except RuntimeError as e:
        print(f"Error: {e}")
