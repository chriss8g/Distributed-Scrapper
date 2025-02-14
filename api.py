import hashlib
from flask import Flask, request, jsonify
import threading
import time
import requests

# Configuración global
M = 160  # Número de bits para los identificadores
BASE_URL = "http://127.0.0.1:{}"  # URL base para los nodos

class ChordNode:
    def __init__(self, port, should_stabilized=True):
        self.m = M
        self.port = port
        self.node_id = self.hash_key(str(port))
        self.finger_table = [{
            'start': (self.node_id + 2**i) % (2**self.m),
            'interval': (self.node_id + 2**i, self.node_id + 2**(i+1)),
            'node': self.port
        } for i in range(self.m)]
        self.predecessor = self.port
        self.successor = self.port
        self.successor_list = []  # Lista de r sucesores
        self.keys = {}
        self.stabilize_thread = threading.Thread(target=self.stabilize_loop)
        self.stabilize_thread.daemon = True
        if should_stabilized:
            self.stabilize_thread.start()

    def __str__(self):
        return f'{self.port}'

    def hash_key(self, key):
        '''
            hashea una key
        '''
        return int(hashlib.sha1(key.encode()).hexdigest(), 16) % (2**self.m)

    def in_interval(self, id, start, end):
        '''
            Chequea si un id pertenece al nodo con id=end
        '''
        if start < end:
            return start < id <= end
        else:
            return id > start or id <= end

    def find_successor(self, id):
        '''
            le asigna un responsable a un id
        '''
        successor_id = requests.get(f'http://127.0.0.1:{self.successor}/id')
        if self.in_interval(id, self.node_id, successor_id):
            return self.successor # Si esta en el rango de mi sucesor, el se lo queda
        else:
            n_prime = self.closest_preceding_node(id)# Busca el nodo mas cercano a la key  y por detras de esta, para potencialmente asignarle su sucesor
            return n_prime.find_successor(id)

    def find_predecessor(self, id):
        # Inicializar el nodo actual como este nodo
        current_node = self.port
        # Mientras el ID no esté en el intervalo (current_node, current_node.successor]
        successor_id = requests.get(f'http://127.0.0.1:{self.successor}/id')
        while not self.in_interval(id, self.hash_key(current_node), successor_id):
            # Avanzar al nodo más cercano que precede a id
            current_node = current_node.closest_preceding_node(id)
        # Devolver el nodo actual (predecessor de id)
        return current_node

    def closest_preceding_node(self, id):
        '''
            Dada una key, busca el nodo en mi finger table q este mas cerca de la key, pero antes q esta
        '''
        for i in range(self.m-1, -1, -1):
            if self.finger_table[i]['node'] and \
               self.in_interval(self.finger_table[i]['node'].node_id, self.node_id, id):
                return self.finger_table[i]['node']
        return self.port

    def stabilize_loop(self):
        '''
            Se ejecuta periodicamente para actualizar propiedades del nodo que puedan
            haber quedado corruptas por inserciones o fallos
            
            !!!!
            aqui debemos annadir la actualizacion con la replicacion
        '''
        while True:
            self.stabilize()
            self.fix_fingers()
            time.sleep(5)  # Cada 30 segundos

    def stabilize(self):
        '''
            Revisa si se agrego a alguien entre yo y mi sucesor, en tal caso actualiza la informacion de mi sucesor.

            Llama al metodo q actualiza el predecessor de mi sucesor q es mi nuevo sucesor
        '''
        predecessor_port = requests.get(f'http://127.0.0.1:{self.successor}/predecessor')
        successor_id = requests.get(f'http://127.0.0.1:{self.successor}/id')

        x = requests.get(f'http://127.0.0.1:{predecessor_port}/id')
        if x and self.in_interval(x, self.node_id, successor_id):
            self.successor = predecessor_port
            print(f'mi sucesor es {predecessor_port}')
        
        requests.post(f'http://127.0.0.1:{self.successor}/notify?port={self.port}')

    def notify(self, node):
        '''
            actualiza mi predecessor
        '''
        predecessor_id = requests.get(f'http://127.0.0.1:{self.predecessor}/id')
        node_id = requests.get(f'http://127.0.0.1:{node}/id')

        if not self.predecessor or self.in_interval(node_id, predecessor_id, self.node_id):
            self.predecessor = node
            print(f'mi predecessor es {node}')

    def fix_fingers(self):
        '''
            Itera por la tabla actualizando los responsables(fingers) de los inicios de intervalos
        '''
        for i in range(self.m):
            self.finger_table[i]['node'] = self.find_successor(self.finger_table[i]['start'])






    def join(self, existing_node):
        '''
            Une al nodo self al anillo donde ya estaba existing_node
        '''
        if existing_node:
            self.init_finger_table(existing_node)
            self.update_others()
            self.transfer_keys()
        else:
            for i in range(self.m):
                self.finger_table[i]['node'] = self
            self.predecessor = self
            self.successor = self

    def init_finger_table(self, n_prime):
        '''
            Inicializa la finger table, asi como los valores de predecessor y successor

            n_prime(puerto) solo se utiliza para tener un nodo con su finger table y poder hacer las busquedas
        '''
        successor = requests.get(f'http://127.0.0.1:{n_prime}/find_successor?key={self.finger_table[0]['start']}')

        self.finger_table[0]['node'] = successor['port']

        predecessor = requests.get(f'http://127.0.0.1:{self.finger_table[0]['node']}/predecessor')
        self.predecessor = predecessor
        self.finger_table[0]['node'].predecessor = self.port
        self.successor = self.finger_table[0]['node']
        
        for i in range(self.m-1):
            start = self.finger_table[i+1]['start']

            node_id = requests.get(f'http://127.0.0.1:{self.finger_table[i]['node']}/id')
            if self.in_interval(start, self.node_id, node_id):
                self.finger_table[i+1]['node'] = self.finger_table[i]['node']
            else:
                successor = requests.get(f'http://127.0.0.1:{n_prime}/find_successor?key={start}')
                self.finger_table[i+1]['node'] = successor['port']

    def update_others(self):
        for i in range(self.m):
            # Calcular el ID del predecessor que podría necesitar actualizar su finger table
            id = (self.node_id - 2**i) % (2**self.m)
            predecessor = self.find_predecessor(id)
            # Pedirle al predecessor que actualice su finger table
            requests.get(f'http://127.0.0.1:{predecessor}/update_finger_table?node_port={self.port}&index={i}')


    def update_finger_table(self, s, i):
        # Verificar si el nuevo nodo s debe ser incluido en la entrada i de la finger table
        s_id = requests.get(f'http://127.0.0.1:{s}/id')
        node_id = requests.get(f'http://127.0.0.1:{self.finger_table[i]['node']}/id')
        if self.in_interval(s_id, self.node_id, node_id):
            # Actualizar la entrada de la finger table
            self.finger_table[i]['node'] = s
            # Pedirle al predecessor que también actualice su finger table
            if self.predecessor and self.predecessor != s:
                requests.get(f'http://127.0.0.1:{self.predecessor}/update_finger_table?node_port={s}&index={i}')

    def transfer_keys(self):
        '''
            Asigname las llaves q m corresponden al unirme al anillo
        '''
        if self.predecessor:
            keys = requests.get(f'http://127.0.0.1:{self.predecessor}/keys')
            for key in list(keys):
                predecessor_id = requests.get(f'http://127.0.0.1:{self.predecessor}/id')
                if self.in_interval(key, predecessor_id, self.node_id):
                    self.keys[key] = keys.pop(key)
                    requests.delete(f'http://127.0.0.1:{self.predecessor}/keys?key={key}')






# Inicialización del servidor Flask
app = Flask(__name__)
node = None

@app.route('/find_successor', methods=['GET'])
def find_successor():
    key = int(request.args.get('key'))
    successor_port = node.find_successor(key)
    return jsonify({
        'node_id': node.hash_key(successor_port),
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

@app.route('/notify', methods=['POST']) #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
def notify():
    new_predecessor = int(request.json.get('port'))
    node.notify(new_predecessor)
    return jsonify({'status': 'notified'})

@app.route('/store', methods=['POST'])
def store():
    key = request.json.get('key')
    value = request.json.get('value')
    hashed_key = node.hash_key(key)
    successor = node.find_successor(hashed_key)

    if node.hash_key(successor) == node.node_id:
        node.keys[hashed_key] = value
        return jsonify({'status': 'stored_locally'})
    else:
        requests.post(f'http://127.0.0.1:{successor}/store', json={'key': key, 'value': value})
        return jsonify({'status': 'forwarded'})

# @app.route('/retrieve', methods=['GET'])
# def retrieve():
#     key = request.args.get('key')
#     hashed_key = node.hash_key(key)
#     successor = node.find_successor(hashed_key)
#     if successor.node_id == node.node_id:
#         if hashed_key in node.keys:
#             return jsonify({'value': node.keys[hashed_key]})
#         else:
#             return jsonify({'error': 'Key not found'}), 404
#     else:
#         response = requests.get(f'http://127.0.0.1:{successor.port}/retrieve?key={key}')
#         return response.json()

@app.route('/id', methods=['GET'])
def id():
    return node.node_id

@app.route('/predecessor', methods=['GET'])
def predecessor():
    return node.predecessor

@app.route('/key', methods=['GET'])
def key():
    return node.key

@app.route('/keys', methods=['DELETE'])
def keys():
    key = request.args.get('key')
    self.keys.pop(key)
    return jsonify({'status': 'updated'})

@app.route('/update_finger_table', methods=['POST'])
def update_finger_table():
    node_port = request.args.get('node_port')
    index = request.args.get('index')
    node.update_finger_table(node_port, index)
    return jsonify({'status': 'updated'})

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1])
    node = ChordNode(port)
    app.run(port=port)