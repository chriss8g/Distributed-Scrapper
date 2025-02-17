from flask import Flask, send_from_directory
import socket

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == "__main__":
    try:
        app.run(debug=True, host='0.0.0.0', port=3000)
    except RuntimeError as e:
        print(f"Error: {e}")
