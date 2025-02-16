import hashlib
import threading
import time
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
import socket

# Configuración global
M = 8  # Número de bits para los identificadores
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
        key = str(key)
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
            
            if n_prime != self.port:
                # successor = make_request('get', f'/find_successor?key={id}', [n_prime]).json()['port']
                for attempt in range(4):
                    try:
                        # Construir la URL usando el puerto actual
                        if str(self.port) == str(n_prime):
                            response = self.find_predecessor(id)
                        else:
                            url = f"http://127.0.0.1:{n_prime}/find_successor?key={id}"
                            response = requests.request('get', url)
                            response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                            response = response.json()
                        return response['port']
                    except (ConnectionError, Timeout) as e:
                        print(f"Intento {attempt + 1} de {4}: Error de conexión o tiempo de espera en {url}. Reintentando en {2**attempt} segundos...")
                        delay = 2**attempt
                        time.sleep(delay)
                    except RequestException as e:
                        print(f"Error en la solicitud a {url}: {e}")
                        break  # No reintentar para otros errores
            else:
                return self.find_successor(id)


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
                    if str(self.port) == str(current_node):
                        response = self.closest_preceding_node(id)
                    else:
                        url = f"http://127.0.0.1:{current_node}/closest_preceding_node?id={id}"
                        response = requests.request('get', url)
                        response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                        response = response.text
                    current_node = response
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
            node_id = self.hash_key(self.finger_table[i]['node'])
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
            time.sleep(5)
            # with open("archivo.txt", "a") as archivo:
            #     archivo.write("Este mensaje se añade al final.\n")
            print("Sucesor: ", self.successor)
            print("Antecesor: ", self.predecessor)

    def check_succ_loop(self):
        while True:
            time.sleep(3)
            a = self.successor
            self.successor = self.find_successor_with_replication(self.successor)
            if a != self.successor:
                    for attempt in range(4):
                        try:
                            # Construir la URL usando el puerto actual
                            url = f"http://127.0.0.1:{self.successor}/set_predecessor?node_port={self.port}"
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

    def stabilize(self):

        if self.finger_table[0]['node'] != self.port:

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
        else:
            predecessor_port = self.predecessor
       

        successor_id = self.hash_key(str(self.successor))

        x = self.hash_key(str(predecessor_port))
        if x and self.in_interval(x, self.node_id, successor_id):
            self.successor = predecessor_port

            if self.successor != self.port:
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
            else:
                self.notify(self.port)
        
        # Actualizar la lista de sucesores
        self.update_successor_list()

    def update_successor_list(self):
        self.successor_list = []
        current_successor = self.successor
        for _ in range(TOLERANCIA+1):  # r es el número de sucesores a mantener
            if current_successor:
                print(current_successor)
                self.successor_list.append(current_successor)
                # current_successor = make_request('get', f'/find_successor?key={(int(current_successor)+1)%2**self.m}', [current_successor]).json()['port']
                
                if str(current_successor)  != str(self.port):
                    for attempt in range(4):
                        try:
                            # Construir la URL usando el puerto actual
                            url = f"http://127.0.0.1:{current_successor}/find_successor?key={(int(self.hash_key(str(current_successor)))+1)%(2**self.m)}"
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
                else:
                    current_successor = self.find_successor((int(self.hash_key(str(current_successor)))+1)%(2**self.m))

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
            self.send_broadcast(str(existing_node), self.port)
            self.transfer_keys()
        else:
            for i in range(self.m):
                self.finger_table[i]['node'] = self.port
            self.predecessor = self.port
            self.successor = self.port

    def init_finger_table(self, n_prime):
        '''
            Inicializa la finger table, asi como los valores de predecessor y successor

            n_prime(puerto) solo se utiliza para tener un nodo con su finger table y poder hacer las busquedas
        '''
        if n_prime != self.port:
            # successor = make_request('get', f'/find_successor?key={self.finger_table[0]['start']}', [n_prime]).json()
            for attempt in range(4):
                try:
                    # Construir la URL usando el puerto actual
                    url = f"http://127.0.0.1:{n_prime}/find_successor?key={self.finger_table[0]['start']}"
                    response = requests.request('get', url)
                    response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                    successor = response.json()['port']
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
        
            else:
                successor = self.find_successor(self.finger_table[0]['start'])
        
        
        self.finger_table[0]['node'] = successor

        if self.finger_table[0]['node'] != self.port:
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
        else:
            predecessor = self.predecessor
        
        
        
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

            node_id = self.finger_table[i]['node']
            if self.in_interval(start, self.node_id, node_id):
                self.finger_table[i+1]['node'] = self.finger_table[i]['node']
            else:
                if n_prime != self.port:
                    # successor = make_request('get', f'/find_successor?key={start}', [n_prime]).json()
                    for attempt in range(4):
                        try:
                            # Construir la URL usando el puerto actual
                            url = f"http://127.0.0.1:{n_prime}/find_successor?key={self.hash_key(str(start))}"
                            response = requests.request('get', url)
                            response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                            successor = response.json()['port']
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
                else:
                    successor = self.find_successor(self.hash_key(str(start)))
            
                
                self.finger_table[i+1]['node'] = successor

        

    def update_finger_table(self, n_prime):

        if n_prime != self.port:
            # successor = make_request('get', f'/find_successor?key={self.finger_table[0]['start']}', [n_prime]).json()
            for attempt in range(4):
                try:
                    # Construir la URL usando el puerto actual
                    url = f"http://127.0.0.1:{n_prime}/find_successor?key={self.finger_table[0]['start']}"
                    response = requests.request('get', url)
                    response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                    successor = response.json()['port']
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
            
        else:
            successor = self.find_successor(self.finger_table[0]['start'])
        
        self.finger_table[0]['node'] = successor
        
        self.successor = self.finger_table[0]['node']
        
        for i in range(self.m-1):
            start = self.finger_table[i+1]['start']

            node_id = self.finger_table[i]['node']
            if self.in_interval(start, self.node_id, node_id):
                self.finger_table[i+1]['node'] = self.finger_table[i]['node']
            else:
                if n_prime != n_prime:
                    # successor = make_request('get', f'/find_successor?key={start}', [n_prime]).json()
                    for attempt in range(4):
                        try:
                            # Construir la URL usando el puerto actual
                            url = f"http://127.0.0.1:{n_prime}/find_successor?key={self.hash_key(str(start))}"
                            response = requests.request('get', url)
                            response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
                            successor = response.json()['port']
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
                
                else:
                    successor = self.find_successor(self.hash_key(str(start)))

                self.finger_table[i+1]['node'] = successor
                
                
    
    def send_broadcast(self, message, port):
        # Crear un socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Dirección de broadcast (generalmente 255.255.255.255)
        # broadcast_address = "255.255.255.255"
        broadcast_address = "127.0.0.1"

        # Enviar el mensaje
        sock.sendto(message.encode(), (broadcast_address, port))
        print(f"Broadcast enviado: {message}")
        sock.close()


    def listen_for_broadcast(self, port):
        # Crear un socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", port))  # Escuchar en todas las interfaces

        while True:
            data, addr = sock.recvfrom(1024)  # Buffer de 1024 bytes
            print(f"Mensaje recibido desde {addr}: {data.decode()}")
            if data.decode():
                self.update_finger_table(data.decode())


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
