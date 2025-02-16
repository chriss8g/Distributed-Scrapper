from flask import Flask, request, jsonify
import time
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
from node import ChordNode

# Inicialización del servidor Flask
app = Flask(__name__)
node = None

@app.route('/find_successor', methods=['GET'])
def find_successor():
    key = int(request.args.get('key'))
    successor_port = node.find_successor(key)
    return jsonify({
        'node_id': node.hash_key(str(successor_port)),
        'port': successor_port,
        'address': f'http://127.0.0.1:{successor_port}'
    })

@app.route('/join', methods=['POST'])
def join():
    existing_port = int(request.json.get('port'))
    if existing_port != node.port:
        existing_node = existing_port  # Función auxiliar para obtener nodos
    else:
        existing_node = None
    node.join(existing_node)
    return jsonify({'status': 'success'})

@app.route('/alive', methods=['GET'])
def alive():
    """
    Endpoint para verificar si el nodo está activo.
    """
    return jsonify({'status': 'alive'})

@app.route('/notify', methods=['POST'])
def notify():
    new_predecessor = int(request.args.get('port'))
    node.notify(new_predecessor)
    return jsonify({'status': 'notified'})

@app.route('/store', methods=['POST'])
def store():
    key = request.args.get('key')
    value = request.args.get('value')
    hashed_key = node.hash_key(str(key))
    successor = node.find_successor(hashed_key)

    if node.hash_key(str(successor)) == node.node_id:
        node.keys[hashed_key] = value
        return jsonify({'status': 'stored_locally'})
    else:
        # make_request('post', f'/store', [successor], json={'key': key, 'value': value})
        for attempt in range(4):
            try:
                # Construir la URL usando el puerto actual
                url = f"http://127.0.0.1:{successor}/store"
                response = requests.request('post', url, json={'key': key, 'value': node.keys[key]})
                response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                return jsonify({'status': 'forwarded'})
            except (ConnectionError, Timeout) as e:
                print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                delay = 2**attempt
                time.sleep(delay)
            except RequestException as e:
                print(f"Error en la solicitud a {url}: {e}")
                break  # No reintentar para otros errores
        
        print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
        return None

@app.route('/replicate', methods=['POST'])
def replicate():
    key = request.json.get('key')
    value = request.json.get('value')
    node.keys[key] = value
    return jsonify({'status': 'replicated'})

# @app.route('/retrieve', methods=['GET'])
# def retrieve():
#     key = request.args.get('key')
#     hashed_key = node.hash_key(str(key))
#     successor = node.find_successor(hashed_key)
#     if successor.node_id == node.node_id:
#         if hashed_key in node.keys:
#             return jsonify({'value': node.keys[hashed_key]})
#         else:
#             return jsonify({'error': 'Key not found'}), 404
#     else:
#         response = make_request('get', f'/retrieve?key={key}', [successor.port])
#         return response.json()

@app.route('/set_predecessor', methods=['POST'])
def set_predecessor():
    node_port = request.args.get('node_port')
    node.predecessor = node_port
    return jsonify({'status': 'updated'})

@app.route('/predecessor', methods=['GET'])
def predecessor():
    return f'{node.predecessor}'

@app.route('/keys', methods=['GET'])
def keys():
    return f'{node.keys}'

@app.route('/keys', methods=['DELETE'])
def delete_keys():
    key = request.args.get('key')
    node.keys.pop(key)
    return jsonify({'status': 'updated'})

@app.route('/closest_preceding_node', methods=['GET'])
def closest_preceding_node():
    id = request.args.get('id')
    response = node.closest_preceding_node(id)
    return f'{response}'

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1])
    node = ChordNode(port)
    app.run(port=port)
    node.listen_for_broadcast(port)