from flask import Flask, request, jsonify
import requests
from requests.exceptions import RequestException
from node import ChordNode
from utils import listen_for_broadcast, hash_key, retry_request, in_interval

# Inicialización del servidor Flask
app = Flask(__name__)
node = None

@app.route('/find_successor', methods=['GET'])
def find_successor():
    key = int(request.args.get('key'))
    successor_port = node.find_successor(key)
    return jsonify({
        'node_id': hash_key(str(successor_port)),
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
    hashed_key = hash_key(str(key))
    
    # Encontrar el nodo responsable usando la lógica Chord
    predecessor_id = hash_key(str(node.predecessor))
    current_node_id = node.node_id

    if in_interval(hashed_key, predecessor_id, current_node_id):
        # Almacenar localmente si somos responsables
        node.keys[hashed_key] = value
        
        # Replicar en los sucesores
        for successor_port in node.successor_list[:-1]:
            def generate_replicate_url():
                return f"http://127.0.0.1:{successor_port}/replicate"
            
            try:
                retry_request(requests.post, generate_replicate_url, 
                            json={'key': hashed_key, 'value': value})
            except RequestException:
                continue
        
        return jsonify({'status': 'stored_locally'})
    else:
        # Buscar el nodo más cercano en la finger table
        closest_node = node.closest_preceding_node(hashed_key)
        
        if closest_node == node.port:
            # Si el más cercano somos nosotros, usar nuestro sucesor
            def generate_forward_url():
                return f"http://127.0.0.1:{node.successor}/store?key={key}&value={value}"
        else:
            # Reenviar al nodo más cercano encontrado
            def generate_forward_url():
                return f"http://127.0.0.1:{closest_node}/store?key={key}&value={value}"

        try:
            response = retry_request(requests.post, generate_forward_url)
            return response.json()
        except RequestException as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        
@app.route('/replicate', methods=['POST'])
def replicate():
    key = request.json.get('key')
    value = request.json.get('value')
    node.keys[key] = value
    return jsonify({'status': 'replicated'})

# @app.route('/retrieve', methods=['GET'])
# def retrieve():
#     key = request.args.get('key')
#     hashed_key = hash_key(str(key))
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
    listen_for_broadcast(port, node.update_finger_table)