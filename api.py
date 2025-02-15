import hashlib
from flask import Flask, request, jsonify
import threading
import time
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

# def make_request(method, endpoint, port_ref, max_retries=4, retry_delay=2, **kwargs):
#     """
#     Realiza una solicitud HTTP con reintentos en caso de errores de conexión.
#     :param method: Método HTTP (get, post, put, delete, etc.).
#     :param endpoint: Endpoint de la solicitud (por ejemplo, '/predecessor').
#     :param port_ref: Referencia al puerto (lista de un solo elemento) para permitir actualizaciones dinámicas.
#     :param max_retries: Número máximo de reintentos.
#     :param retry_delay: Tiempo de espera (en segundos) entre reintentos.
#     :param kwargs: Argumentos adicionales para requests (params, json, headers, etc.).
#     :return: Respuesta de la solicitud o None si hay un error después de los reintentos.
#     """
#     for attempt in range(max_retries):
#         try:
#             # Construir la URL usando el puerto actual
#             url = f"http://127.0.0.1:{port_ref[0]}{endpoint}"
#             response = requests.request(method, url, **kwargs)
#             response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
#             return response
#         except (ConnectionError, Timeout) as e:
#             print(f"Intento {attempt + 1} de {max_retries}: Error de conexión o tiempo de espera en {url}. Reintentando en {retry_delay**attempt} segundos...")
#             delay = retry_delay**attempt
#             time.sleep(delay)
#         except RequestException as e:
#             print(f"Error en la solicitud a {url}: {e}")
#             break  # No reintentar para otros errores
    
#     print(f"Error: No se pudo completar la solicitud a {url} después de {max_retries} intentos.")
#     return None



# Configuración global
M = 160  # Número de bits para los identificadores
BASE_URL = "http://127.0.0.1:{}"  # URL base para los nodos
TOLERANCIA = 2

class ChordNode:
    def __init__(self, port):
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
        self.stabilize_thread.start()

        self.check_succ_thread = threading.Thread(target=self.check_succ_loop)
        self.check_succ_thread.daemon = True
        self.check_succ_thread.start()

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
        end = int(end)
        id = int(id)
        start = int(start)
        if start < end:
            return start < id <= end
        else:
            return id > start or id <= end

    def find_successor(self, id):
        '''
            le asigna un responsable a un id
        '''
        successor_id = self.hash_key(str(self.successor))
        if self.in_interval(id, self.node_id, successor_id):
            return self.successor # Si esta en el rango de mi sucesor, el se lo queda
        else:
            n_prime = self.closest_preceding_node(id)# Busca el nodo mas cercano a la key  y por detras de esta, para potencialmente asignarle su sucesor
            
            # successor = make_request('get', f'/find_successor?key={id}', [n_prime]).json()['port']
            for attempt in range(4):
                try:
                    # Construir la URL usando el puerto actual
                    url = f"http://127.0.0.1:{n_prime}/find_successor?key={id}"
                    response = requests.request('get', url)
                    response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                    return response.json()['port']
                except (ConnectionError, Timeout) as e:
                    print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                    delay = 2**attempt
                    time.sleep(delay)
                except RequestException as e:
                    print(f"Error en la solicitud a {url}: {e}")
                    break  # No reintentar para otros errores
            
            print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
            return None


    def find_predecessor(self, id):
        # Inicializar el nodo actual como este nodo
        current_node = self.port
        # Mientras el ID no esté en el intervalo (current_node, current_node.successor]
        successor_id = self.hash_key(str(self.successor))
        while not self.in_interval(id, self.hash_key(str(current_node)), successor_id):
            # Avanzar al nodo más cercano que precede a id
            # current_node = make_request('get', f'/closest_preceding_node?id={id}', [current_node]).text
            for attempt in range(4):
                try:
                    # Construir la URL usando el puerto actual
                    url = f"http://127.0.0.1:{current_node}/closest_preceding_node?id={id}"
                    response = requests.request('get', url)
                    response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                    current_node = response.text
                    break
                except (ConnectionError, Timeout) as e:
                    if (attempt == 3):
                        print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                        return None
                    print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                    delay = 2**attempt
                    time.sleep(delay)
                except RequestException as e:
                    print(f"Error en la solicitud a {url}: {e}")
                    break  # No reintentar para otros errores
            
            
        # Devolver el nodo actual (predecessor de id) !!!!!!!!!!!!
        return current_node

    def closest_preceding_node(self, id):
        '''
            Dada una key, busca el nodo en mi finger table q este mas cerca de la key, pero antes q esta
        '''
        for i in range(self.m-1, -1, -1):
            node_id = self.hash_key(str(self.finger_table[i]['node']))
            if self.finger_table[i]['node'] and \
               self.in_interval(node_id, self.node_id, id):
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
            time.sleep(3)
            print("Sucesor: ", self.successor)
            print("Antecesor: ", self.predecessor)

    def check_succ_loop(self):
        while True:
            time.sleep(1)
            self.successor = self.find_successor_with_replication(self.successor)


    def stabilize(self):

        # predecessor_port = make_request('get', f'/predecessor', [self.successor]).text
        for attempt in range(4):
            try:
                # Construir la URL usando el puerto actual
                url = f"http://127.0.0.1:{self.successor}/predecessor"
                response = requests.request('get', url)
                response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                predecessor_port = response.text
                break
            except (ConnectionError, Timeout) as e:
                if (attempt == 3):
                    print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                    predecessor_port = None
                    break
                print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                delay = 2**attempt
                time.sleep(delay)
            except RequestException as e:
                print(f"Error en la solicitud a {url}: {e}")
                break  # No reintentar para otros errores
        
       

        successor_id = self.hash_key(str(self.successor))

        x = self.hash_key(str(predecessor_port))
        if x and self.in_interval(x, self.node_id, successor_id):
            self.successor = predecessor_port
            # make_request('post', f'/notify?port={self.port}', [self.successor])
            for attempt in range(4):
                try:
                    # Construir la URL usando el puerto actual
                    url = f"http://127.0.0.1:{self.successor}/notify?port={self.port}"
                    response = requests.request('post', url)
                    response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                    break
                except (ConnectionError, Timeout) as e:
                    if (attempt == 3):
                        print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                        break
                    print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                    delay = 2**attempt
                    time.sleep(delay)
                except RequestException as e:
                    print(f"Error en la solicitud a {url}: {e}")
                    break  # No reintentar para otros errores
            
        
        # Actualizar la lista de sucesores
        self.update_successor_list()

    def update_successor_list(self):
        self.successor_list = []
        current_successor = self.successor
        for _ in range(TOLERANCIA):  # r es el número de sucesores a mantener
            if current_successor:
                self.successor_list.append(current_successor)
                # current_successor = make_request('get', f'/find_successor?key={current_successor}', [current_successor]).json()['port']
                for attempt in range(4):
                    try:
                        # Construir la URL usando el puerto actual
                        url = f"http://127.0.0.1:{current_successor}/find_successor?key={current_successor}"
                        response = requests.request('get', url)
                        response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                        current_successor = response.json()['port']
                        break
                    except (ConnectionError, Timeout) as e:
                        if (attempt == 3):
                            print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                            current_successor = None
                            break
                        print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                        delay = 2**attempt
                        time.sleep(delay)
                    except RequestException as e:
                        print(f"Error en la solicitud a {url}: {e}")
                        break  # No reintentar para otros errores
                

    def notify(self, node):
        '''
            actualiza mi predecessor
        '''
        predecessor_id = self.hash_key(str(self.predecessor))
        node_id = self.hash_key(str(node))
        if not self.predecessor or self.in_interval(node_id, predecessor_id, self.node_id):
            self.predecessor = node

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
            self.predecessor = self.port
            self.successor = self.port

    def init_finger_table(self, n_prime):
        '''
            Inicializa la finger table, asi como los valores de predecessor y successor

            n_prime(puerto) solo se utiliza para tener un nodo con su finger table y poder hacer las busquedas
        '''
        # successor = make_request('get', f'/find_successor?key={self.finger_table[0]['start']}', [n_prime]).json()
        for attempt in range(4):
            try:
                # Construir la URL usando el puerto actual
                url = f"http://127.0.0.1:{n_prime}/find_successor?key={self.finger_table[0]['start']}"
                response = requests.request('get', url)
                response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                successor = response.json()
                break
            except (ConnectionError, Timeout) as e:
                if (attempt == 3):
                    print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                    successor = None
                    break
                print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                delay = 2**attempt
                time.sleep(delay)
            except RequestException as e:
                print(f"Error en la solicitud a {url}: {e}")
                break  # No reintentar para otros errores
        
        
        
        self.finger_table[0]['node'] = successor['port']

        # predecessor = make_request('get', f'/predecessor', [self.finger_table[0]['node']]).text
        for attempt in range(4):
            try:
                # Construir la URL usando el puerto actual
                url = f"http://127.0.0.1:{self.finger_table[0]['node']}/predecessor"
                response = requests.request('get', url)
                response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                predecessor = response.text
                break
            except (ConnectionError, Timeout) as e:
                if (attempt == 3):
                    print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                    predecessor = None
                    break
                print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                delay = 2**attempt
                time.sleep(delay)
            except RequestException as e:
                print(f"Error en la solicitud a {url}: {e}")
                break  # No reintentar para otros errores
        
        
        
        
        
        self.predecessor = predecessor


        # make_request('post', f'/set_predecessor?node_port={self.port}', [self.finger_table[0]['node']])
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!1
        for attempt in range(4):
            try:
                # Construir la URL usando el puerto actual
                url = f"http://127.0.0.1:{self.finger_table[0]['node']}/set_predecessor?node_port={self.port}"
                response = requests.request('post', url)
                response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                break
            except (ConnectionError, Timeout) as e:
                if (attempt == 3):
                    print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                    break
                print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                delay = 2**attempt
                time.sleep(delay)
            except RequestException as e:
                print(f"Error en la solicitud a {url}: {e}")
                break  # No reintentar para otros errores
        
        




        self.successor = self.finger_table[0]['node']
        
        for i in range(self.m-1):
            start = self.finger_table[i+1]['start']

            node_id = self.hash_key(str(self.finger_table[i]['node']))
            if self.in_interval(start, self.node_id, node_id):
                self.finger_table[i+1]['node'] = self.finger_table[i]['node']
            else:
                # successor = make_request('get', f'/find_successor?key={start}', [n_prime]).json()
                for attempt in range(4):
                    try:
                        # Construir la URL usando el puerto actual
                        url = f"http://127.0.0.1:{n_prime}/find_successor?key={start}"
                        response = requests.request('get', url)
                        response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                        successor = response.json()
                        break
                    except (ConnectionError, Timeout) as e:
                        if (attempt == 3):
                            print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                            successor = None
                            break
                        print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                        delay = 2**attempt
                        time.sleep(delay)
                    except RequestException as e:
                        print(f"Error en la solicitud a {url}: {e}")
                        break  # No reintentar para otros errores
                
                
                
                
                
                self.finger_table[i+1]['node'] = successor['port']

    def update_others(self):
        for i in range(self.m):
            # Calcular el ID del predecessor que podría necesitar actualizar su finger table
            id = (self.node_id - 2**i) % (2**self.m)
            predecessor = self.find_predecessor(id)
            # Pedirle al predecessor que actualice su finger table
            # make_request('post', f'/update_finger_table?node_port={self.port}&index={i}', [predecessor])
            for attempt in range(4):
                try:
                    # Construir la URL usando el puerto actual
                    url = f"http://127.0.0.1:{predecessor}/update_finger_table?node_port={self.port}&index={i}"
                    response = requests.request('post', url)
                    response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                    break
                except (ConnectionError, Timeout) as e:
                    if (attempt == 3):
                        print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                        break
                    print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                    delay = 2**attempt
                    time.sleep(delay)
                except RequestException as e:
                    print(f"Error en la solicitud a {url}: {e}")
                    break  # No reintentar para otros errores
            
            

    def update_finger_table(self, s, i):
        # Verificar si el nuevo nodo s debe ser incluido en la entrada i de la finger table
        i = int(i)
        s_id = self.hash_key(str(s))
        node_id = self.hash_key(str(self.finger_table[i]['node']))
        if self.in_interval(s_id, self.node_id, node_id):
            # Actualizar la entrada de la finger table
            self.finger_table[i]['node'] = s
            # Pedirle al predecessor que también actualice su finger table
            if self.predecessor and self.predecessor != s:
                # make_request('post', f'/update_finger_table?node_port={s}&index={i}', [self.predecessor])
                for attempt in range(4):
                    try:
                        # Construir la URL usando el puerto actual
                        url = f"http://127.0.0.1:{self.predecessor}/update_finger_table?node_port={s}&index={i}"
                        response = requests.request('post', url)
                        response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                        break
                    except (ConnectionError, Timeout) as e:
                        if (attempt == 3):
                            print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                            break
                        print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                        delay = 2**attempt
                        time.sleep(delay)
                    except RequestException as e:
                        print(f"Error en la solicitud a {url}: {e}")
                        break  # No reintentar para otros errores
                
                


    def transfer_keys(self):
        if self.predecessor:
            # keys = make_request('get', f'/keys', [self.predecessor]).json()
            for attempt in range(4):
                try:
                    # Construir la URL usando el puerto actual
                    url = f"http://127.0.0.1:{self.predecessor}/keys"
                    response = requests.request('get', url)
                    response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                    keys = response.json()
                    break
                except (ConnectionError, Timeout) as e:
                    if (attempt == 3):
                        print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                        keys = None
                        break
                    print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                    delay = 2**attempt
                    time.sleep(delay)
                except RequestException as e:
                    print(f"Error en la solicitud a {url}: {e}")
                    break  # No reintentar para otros errores
            
            





            for key in keys.keys():
                predecessor_id = self.hash_key(str(self.predecessor))
                if self.in_interval(key, predecessor_id, self.node_id):
                    self.keys[key] = keys.pop(key)
                    # make_request('delete', f'/keys?key={key}', [self.predecessor])
                    for attempt in range(4):
                        try:
                            # Construir la URL usando el puerto actual
                            url = f"http://127.0.0.1:{self.predecessor}/keys?key={key}"
                            response = requests.request('delete', url)
                            response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                            break
                        except (ConnectionError, Timeout) as e:
                            if (attempt == 3):
                                print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                                break
                            print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                            delay = 2**attempt
                            time.sleep(delay)
                        except RequestException as e:
                            print(f"Error en la solicitud a {url}: {e}")
                            break  # No reintentar para otros errores
                    
                    







                    # Replicar la clave en los r sucesores
                    for i in range(len(self.successor_list)):
                        successor_port = self.successor_list[i]
                        # make_request('post', f'/replicate', [successor_port], json={'key': key, 'value': self.keys[key]})
                        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
                        for attempt in range(4):
                            try:
                                # Construir la URL usando el puerto actual
                                url = f"http://127.0.0.1:{successor_port}/replicate"
                                response = requests.request('post', url, json={'key': key, 'value': self.keys[key]})
                                response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                                break
                            except (ConnectionError, Timeout) as e:
                                if (attempt == 3):
                                    print(f"Error: No se pudo completar la solicitud a {url} después de {4} intentos.")
                                    break
                                print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                                delay = 2**attempt
                                time.sleep(delay)
                            except RequestException as e:
                                print(f"Error en la solicitud a {url}: {e}")
                                break  # No reintentar para otros errores
                        
                        

                        


    def find_successor_with_replication(self, successor):
    
        if self.is_node_alive(self.successor):
            return self.successor

        for i in range(len(self.successor_list)):
            replica_port = self.successor_list[i]
            if self.is_node_alive(replica_port):
                return replica_port

    def is_node_alive(self, node_port):
        """
        Verifica si un nodo está vivo haciendo una solicitud al endpoint /alive.
        :param node_port: Puerto del nodo a verificar.
        :return: True si el nodo responde, False en caso contrario.
        """
        try:
            # Intentar hacer la solicitud al endpoint /alive
            response = requests.get(f'http://127.0.0.1:{node_port}/alive')
            if response and response.status_code == 200:  # Verificar que la respuesta sea exitosa
                return True
        except (ConnectionError, Timeout, RequestException):
            # Capturar errores de conexión, tiempo de espera u otros problemas
            pass  # No hacer nada, simplemente continuar
        
        # Si llegamos aquí, el nodo no está disponible
        return False

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
                response = requests.request('post', url, json={'key': key, 'value': self.keys[key]})
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
    self.keys.pop(key)
    return jsonify({'status': 'updated'})

@app.route('/update_finger_table', methods=['POST'])
def update_finger_table():
    node_port = request.args.get('node_port')
    index = request.args.get('index')
    node.update_finger_table(node_port, index)
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