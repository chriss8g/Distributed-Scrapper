import hashlib
from flask import Flask, request, jsonify
import threading
import time
import requests

# Configuración global
M = 160  # Número de bits para los identificadores
BASE_URL = "http://127.0.0.1:{}"  # URL base para los nodos

class ChordNode:
    def __init__(self, port):
        self.m = M
        self.port = port
        self.node_id = self.hash_key(str(port))
        self.finger_table = [{
            'start': (self.node_id + 2**i) % (2**self.m),
            'interval': (self.node_id + 2**i, self.node_id + 2**(i+1)),
            'node': None
        } for i in range(self.m)]
        self.predecessor = None
        self.successor = None
        self.successor_list = []  # Lista de r sucesores
        self.keys = {}
        self.stabilize_thread = threading.Thread(target=self.stabilize_loop)
        self.stabilize_thread.daemon = True
        self.stabilize_thread.start()

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
        if self.in_interval(id, self.node_id, self.successor.node_id):
            return self.successor # Si esta en el rango de mi sucesor, el se lo queda
        else:
            n_prime = self.closest_preceding_node(id)# Busca el nodo mas cercano a la key  y por detras de esta, para potencialmente asignarle su sucesor
            return n_prime.find_successor(id)

    def closest_preceding_node(self, id):
        '''
            Dada una key, busca el nodo en mi finger table q este mas cerca de la key, pero antes q esta
        '''
        for i in range(self.m-1, -1, -1):
            if self.finger_table[i]['node'] and \
               self.in_interval(self.finger_table[i]['node'].node_id, self.node_id, id):
                return self.finger_table[i]['node']
        return self

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
            time.sleep(30)  # Cada 30 segundos

    def stabilize(self):
        '''
            Revisa si se agrego a alguien entre yo y mi sucesor, en tal caso actualiza la informacion de mi sucesor.

            Llama al metodo q actualiza el predecesor de mi sucesor q es mi nuevo sucesor
        '''
        x = self.successor.predecessor
        if x and self.in_interval(x.node_id, self.node_id, self.successor.node_id):
            self.successor = x
        self.successor.notify(self)

    def notify(self, node):
        '''
            actualiza mi predecesor
        '''
        if not self.predecessor or self.in_interval(node.node_id, self.predecessor.node_id, self.node_id):
            self.predecessor = node

    def fix_fingers(self):
        '''
            Itera por la tabla actualizando los responsables(fingers) de los inicions de intervalos
        '''
        for i in range(self.m):
            self.finger_table[i]['node'] = self.find_successor(self.finger_table[i]['start'])






    def join(self, existing_node):
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
        self.finger_table[0]['node'] = n_prime.find_successor(self.finger_table[0]['start'])
        self.predecessor = self.finger_table[0]['node'].predecessor
        self.finger_table[0]['node'].predecessor = self
        self.successor = self.finger_table[0]['node']
        
        for i in range(self.m-1):
            start = self.finger_table[i+1]['start']
            if self.in_interval(start, self.node_id, self.finger_table[i]['node'].node_id):
                self.finger_table[i+1]['node'] = self.finger_table[i]['node']
            else:
                self.finger_table[i+1]['node'] = n_prime.find_successor(start)

    def update_others(self):
        for i in range(self.m):
            predecessor = self.find_predecessor((self.node_id - 2**i) % (2**self.m))
            predecessor.update_finger_table(self, i)

    def update_finger_table(self, s, i):
        if self.in_interval(s.node_id, self.node_id, self.finger_table[i]['node'].node_id):
            self.finger_table[i]['node'] = s
            p = self.predecessor
            p.update_finger_table(s, i)

    def transfer_keys(self):
        if self.predecessor:
            for key in list(self.predecessor.keys):
                if self.in_interval(key, self.predecessor.node_id, self.node_id):
                    self.keys[key] = self.predecessor.keys.pop(key)







# Inicialización del servidor Flask
app = Flask(__name__)
node = None

@app.route('/find_successor', methods=['GET'])
def find_successor():
    key = int(request.args.get('key'))
    successor = node.find_successor(key)
    return jsonify({
        'node_id': successor.node_id,
        'port': successor.port,
        'address': f'http://127.0.0.1:{successor.port}'
    })

@app.route('/join', methods=['POST'])
def join():
    existing_port = int(request.json.get('existing_port'))
    existing_node = get_node(existing_port)  # Función auxiliar para obtener nodos
    node.join(existing_node)
    return jsonify({'status': 'success'})

@app.route('/notify', methods=['POST'])
def notify():
    new_predecessor = get_node(request.json.get('port'))
    node.notify(new_predecessor)
    return jsonify({'status': 'notified'})

@app.route('/store', methods=['POST'])
def store():
    key = request.json.get('key')
    value = request.json.get('value')
    hashed_key = node.hash_key(key)
    successor = node.find_successor(hashed_key)
    if successor.node_id == node.node_id:
        node.keys[hashed_key] = value
        return jsonify({'status': 'stored_locally'})
    else:
        requests.post(f'http://127.0.0.1:{successor.port}/store', json={'key': key, 'value': value})
        return jsonify({'status': 'forwarded'})

@app.route('/retrieve', methods=['GET'])
def retrieve():
    key = request.args.get('key')
    hashed_key = node.hash_key(key)
    successor = node.find_successor(hashed_key)
    if successor.node_id == node.node_id:
        if hashed_key in node.keys:
            return jsonify({'value': node.keys[hashed_key]})
        else:
            return jsonify({'error': 'Key not found'}), 404
    else:
        response = requests.get(f'http://127.0.0.1:{successor.port}/retrieve?key={key}')
        return response.json()

def get_node(port):
    # Función auxiliar para obtener un nodo por su puerto
    return ChordNode(port)

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1])
    node = ChordNode(port)
    app.run(port=port)