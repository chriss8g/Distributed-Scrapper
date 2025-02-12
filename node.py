from flask import Flask, request, jsonify
import requests
from utils import hash_key, Node, is_responsible, load_data, save_data

app = Flask(__name__)

# Nodo actual
current_node = None

@app.route('/data', methods=['GET'])
def data():
    """Muestra la data almacenada"""
    global current_node
    data = load_data()
    return jsonify({"message": ', '.join(data.keys())}), 200

@app.route('/join', methods=['POST'])
def join():
    """Un nuevo nodo se une al anillo."""
    global current_node
    data = request.json
    new_node_ip = data['ip']
    new_node_id = hash_key(new_node_ip)
    new_node = Node(new_node_ip)

    if not current_node.successor:
        requests.post(f"http://{new_node_ip}/set_successor", json={'ip': current_node.ip})
        new_node.successor = current_node
        current_node.successor = new_node
        # Transferir las claves que ahora le corresponden al nuevo nodo
        transfer_keys(new_node)
        return jsonify({"message": "Nodo unido al anillo"}), 200

    successor_ip = current_node.successor.ip
    
    # Actualizar el sucesor del nuevo nodo
    if is_responsible(new_node_id, current_node):
        requests.post(f"http://{new_node_ip}/set_successor", json={'ip': successor_ip})
        new_node.successor = current_node.successor
        current_node.successor = new_node
        # Transferir las claves que ahora le corresponden al nuevo nodo
        transfer_keys(new_node)
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
    url_id = hash_key(url)

    if is_responsible(url_id, current_node):
        data = load_data()
        data[url] = url_id
        save_data(data)
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
    url_id = hash_key(url)

    if is_responsible(url_id, current_node):
        data = load_data()
        if url in data:
            return jsonify({"message": f"URL '{url}' encontrada en {current_node.ip}"}), 200
        else:
            return jsonify({"message": f"La URL '{url}' no ha sido almacenada"}), 404
    else:
        # Reenviar la solicitud al sucesor
        response = requests.get(f"http://{current_node.successor.ip}/get", params={'url': url})
        return response.json(), 200

@app.route('/receive_keys', methods=['POST'])
def receive_keys():
    """Recibe las claves transferidas desde otro nodo."""
    global current_node
    data = request.json
    current_data = load_data()
    current_data.update(data)
    save_data(current_data)
    return jsonify({"message": "Claves recibidas correctamente"}), 200

def transfer_keys(new_node):
    """Transfiere las claves que ahora corresponden al nuevo nodo."""
    global current_node
    current_data = load_data()
    keys_to_transfer = {}
    for url, url_id in list(current_data.items()):
        if is_responsible(url_id, new_node):
            keys_to_transfer[url] = url_id
            del current_data[url]
    if keys_to_transfer:
        requests.post(f"http://{new_node.ip}/receive_keys", json=keys_to_transfer)
        save_data(current_data)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Uso: python node.py <ip>")
        sys.exit(1)

    ip = sys.argv[1]
    current_node = Node(ip)
    app.run(host=ip.split(':')[0], port=int(ip.split(':')[1]))