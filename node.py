from flask import Flask, request, jsonify
import requests
from utils import hash_key

app = Flask(__name__)

# Nodo actual
current_node = None
# Cantidad de bits en el anillo
bits = 12

class Node:
    def __init__(self, ip):
        self.ip = ip
        self.id = hash_key(ip, bits)
        self.data = {}  # Almacena las URLs
        self.successor = None  # Sucesor en el anillo

    def __repr__(self):
        return f"Node(IP={self.ip}, ID={self.id})"

@app.route('/data', methods=['GET'])
def data():
    """Muestra la data almacenada"""
    global current_node
    return jsonify({"message": ', '.join(i for i in current_node.data.keys())}), 200


@app.route('/join', methods=['POST'])
def join():
    """Un nuevo nodo se une al anillo."""
    global current_node
    data = request.json
    new_node_ip = data['ip']
    new_node_id = hash_key(new_node_ip, bits)

    if not current_node.successor:
        requests.post(f"http://{new_node_ip}/set_successor", json={'ip': current_node.ip})
        current_node.successor = Node(new_node_ip)
        return jsonify({"message": "Nodo unido al anillo"}), 200

    successor_ip = current_node.successor.ip
    
    # Actualizar el sucesor del nuevo nodo
    if is_responsible(new_node_id, current_node):
        requests.post(f"http://{new_node_ip}/set_successor", json={'ip': successor_ip})
        current_node.successor = Node(new_node_ip)
        return jsonify({"message": "Nodo unido al anillo"}), 200
    else:
        response = requests.post(f"http://{successor_ip}/join", json={'ip': new_node_ip})
        return response.json(), 200

@app.route('/set_successor', methods=['POST'])
def set_successor():
    """Establece el sucesor del nodo."""
    global current_node
    data = request.json
    successor_ip = data['ip']
    current_node.successor = Node(successor_ip)
    return jsonify({"message": "Sucesor actualizado"}), 200

@app.route('/store', methods=['POST'])
def store():
    """Almacena una URL en el nodo responsable."""
    global current_node
    data = request.json
    url = data['url']
    url_id = hash_key(url, bits)

    if is_responsible(url_id, current_node):
        current_node.data[url] = url_id
        return jsonify({"message": f"URL '{url}' almacenada en {current_node.ip}"}), 200
    else:
        # Reenviar la solicitud al sucesor
        response = requests.post(f"http://{current_node.successor.ip}/store", json={'url': url})
        return response.json(), 200

@app.route('/get', methods=['GET'])
def get():
    """Recupera una URL desde el nodo responsable."""
    global current_node
    url = request.args.get('url')
    url_id = hash_key(url, bits)

    if is_responsible(url_id, current_node):
        if url in current_node.data:
            return jsonify({"message": f"URL '{url}' encontrada en {current_node.ip}"}), 200
        else:
            return jsonify({"message": f"La URL '{url}' no ha sido almacenada"}), 404
    else:
        # Reenviar la solicitud al sucesor
        response = requests.get(f"http://{current_node.successor.ip}/get", params={'url': url})
        return response.json(), 200

def is_responsible(key_id, node):
    """Verifica si el nodo es responsable de un identificador."""
    if node.id < node.successor.id:
        return node.id < key_id < node.successor.id
    else:
        return (node.id < key_id < 2**bits) or (0 < key_id < node.successor.id)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Uso: python node.py <ip>")
        sys.exit(1)

    ip = sys.argv[1]
    current_node = Node(ip)
    app.run(host=ip.split(':')[0], port=int(ip.split(':')[1]))