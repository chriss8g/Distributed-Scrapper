from flask import Flask, send_from_directory
from flask_cors import CORS
import socket

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

def find_free_port(start_port=3000, max_attempts=10):
    """
    Encuentra un puerto libre comenzando desde start_port.
    Intenta hasta max_attempts veces.
    """
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("0.0.0.0", port)) != 0:
                return port
    raise RuntimeError("No se encontró ningún puerto libre en el rango especificado.")

if __name__ == "__main__":
    try:
        port = find_free_port(start_port=3000)
        app.run(debug=True, host="0.0.0.0", port=port)
    except RuntimeError as e:
        print(f"Error: {e}")
