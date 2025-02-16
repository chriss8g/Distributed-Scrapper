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

def retry_request(action, url_generator, max_attempts=4, **kwargs):
    """
    Intenta realizar una solicitud HTTP con reintentos.
    
    :param action: Función que realiza la solicitud (e.g., requests.get, requests.post).
    :param url_generator: Función que genera la URL en cada intento.
    :param max_attempts: Número máximo de intentos.
    :param kwargs: Argumentos adicionales para la función `action`.
    :return: Respuesta de la solicitud exitosa.
    :raises: Excepción si todos los intentos fallan.
    """
    for attempt in range(max_attempts):
        try:
            url = url_generator()  # Genera la URL actualizada
            response = action(url, **kwargs)
            response.raise_for_status()  # Lanza una excepción para códigos de estado 4xx/5xx
            return response
        except (ConnectionError, Timeout) as e:
            if attempt == max_attempts - 1:
                print(f"Error: No se pudo completar la solicitud después de {max_attempts} intentos.")
                raise
            delay = 2**attempt
            print(f"Intento {attempt + 1} de {max_attempts}: Error de conexión o tiempo de espera. Reintentando en {delay} segundos...")
            time.sleep(delay)
        except RequestException as e:
            print(f"Error en la solicitud: {e}")
            raise


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
        """
        Encuentra el sucesor de un ID dado.
        """
        successor_id = self.hash_key(str(self.successor))
        if self.in_interval(id, self.node_id, successor_id):
            return self.successor  # Si está en el rango de mi sucesor, él se lo queda
        else:
            n_prime = self.closest_preceding_node(id)  # Busca el nodo más cercano a la key y por detrás de esta

            if n_prime != self.port:
                def generate_url():
                    if str(self.port) == str(n_prime):
                        raise ValueError("No se necesita URL, se usa find_predecessor local.")
                    return f"http://127.0.0.1:{n_prime}/find_successor?key={id}"

                try:
                    response = retry_request(requests.get, generate_url)
                    return response.json()['port']
                except ValueError:
                    return self.find_predecessor(id)
            else:
                return self.find_successor(id)


    def find_predecessor(self, id):
        """
        Encuentra el predecesor de un ID dado.
        """
        current_node = self.port
        successor_id = self.hash_key(str(self.successor))

        while not self.in_interval(id, self.hash_key(str(current_node)), successor_id):
            def generate_url():
                if str(self.port) == str(current_node):
                    raise ValueError("No se necesita URL, se usa closest_preceding_node local.")
                return f"http://127.0.0.1:{current_node}/closest_preceding_node?id={id}"

            try:
                response = retry_request(requests.get, generate_url)
                current_node = response.text
            except ValueError:
                current_node = self.closest_preceding_node(id)

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
            print("Sucesor: ", self.successor)
            print("Antecesor: ", self.predecessor)

    def check_succ_loop(self):
        """
        Verifica periódicamente el sucesor y actualiza el predecesor del sucesor si es necesario.
        """
        while True:
            time.sleep(3)
            old_successor = self.successor
            self.successor = self.find_successor_with_replication(self.successor)
            
            if old_successor != self.successor:
                def generate_url():
                    return f"http://127.0.0.1:{self.successor}/set_predecessor?node_port={self.port}"

                try:
                    retry_request(requests.post, generate_url)
                except RequestException as e:
                    print(f"Error al notificar al sucesor {self.successor}: {e}")

    def stabilize(self):
        """
        Actualiza el sucesor y el predecesor del nodo para mantener la estabilidad del anillo.
        """
        if self.finger_table[0]['node'] != self.port:
            def generate_predecessor_url():
                return f"http://127.0.0.1:{self.successor}/predecessor"

            try:
                response = retry_request(requests.get, generate_predecessor_url)
                predecessor_port = response.text
            except RequestException as e:
                print(f"Error al obtener el predecesor del sucesor {self.successor}: {e}")
                predecessor_port = None
        else:
            predecessor_port = self.predecessor

        successor_id = self.hash_key(str(self.successor))
        x = self.hash_key(str(predecessor_port))

        if x and self.in_interval(x, self.node_id, successor_id):
            self.successor = predecessor_port

            if self.successor != self.port:
                def generate_notify_url():
                    return f"http://127.0.0.1:{self.successor}/notify?port={self.port}"

                try:
                    retry_request(requests.post, generate_notify_url)
                except RequestException as e:
                    print(f"Error al notificar al sucesor {self.successor}: {e}")
            else:
                self.notify(self.port)

        # Actualizar la lista de sucesores
        self.update_successor_list()

    def update_successor_list(self):
        """
        Actualiza la lista de sucesores del nodo.
        """
        self.successor_list = []
        current_successor = self.successor

        for _ in range(TOLERANCIA + 1):  # r es el número de sucesores a mantener
            if current_successor:
                print(current_successor)
                self.successor_list.append(current_successor)

                if str(current_successor) != str(self.port):
                    def generate_successor_url():
                        return f"http://127.0.0.1:{current_successor}/find_successor?key={(int(self.hash_key(str(current_successor))) + 1) % (2 ** self.m)}"

                    try:
                        response = retry_request(requests.get, generate_successor_url)
                        current_successor = response.json()['port']
                    except RequestException as e:
                        print(f"Error al obtener el sucesor de {current_successor}: {e}")
                        current_successor = None
                else:
                    current_successor = self.find_successor((int(self.hash_key(str(current_successor))) + 1) % (2 ** self.m))
                    
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
        """
        Une al nodo self al anillo donde ya estaba existing_node.
        """
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
        """
        Inicializa la finger table, así como los valores de predecessor y successor.

        n_prime (puerto) solo se utiliza para tener un nodo con su finger table y poder hacer las búsquedas.
        """
        if n_prime != self.port:
            def generate_successor_url():
                return f"http://127.0.0.1:{n_prime}/find_successor?key={self.finger_table[0]['start']}"

            try:
                response = retry_request(requests.get, generate_successor_url)
                successor = response.json()['port']
            except RequestException as e:
                print(f"Error al inicializar la finger table: {e}")
                successor = self.find_successor(self.finger_table[0]['start'])
        else:
            successor = self.find_successor(self.finger_table[0]['start'])

        self.finger_table[0]['node'] = successor

        if self.finger_table[0]['node'] != self.port:
            def generate_predecessor_url():
                return f"http://127.0.0.1:{self.finger_table[0]['node']}/predecessor"

            try:
                response = retry_request(requests.get, generate_predecessor_url)
                predecessor = response.text
            except RequestException as e:
                print(f"Error al obtener el predecesor del sucesor {self.finger_table[0]['node']}: {e}")
                predecessor = None
        else:
            predecessor = self.predecessor

        self.predecessor = predecessor

        if self.finger_table[0]['node'] != self.port:
            def generate_set_predecessor_url():
                return f"http://127.0.0.1:{self.finger_table[0]['node']}/set_predecessor?node_port={self.port}"

            try:
                retry_request(requests.post, generate_set_predecessor_url)
            except RequestException as e:
                print(f"Error al notificar al sucesor {self.finger_table[0]['node']}: {e}")

        self.successor = self.finger_table[0]['node']

        for i in range(self.m - 1):
            start = self.finger_table[i + 1]['start']
            node_id = self.finger_table[i]['node']

            if self.in_interval(start, self.node_id, node_id):
                self.finger_table[i + 1]['node'] = self.finger_table[i]['node']
            else:
                if n_prime != self.port:
                    def generate_finger_successor_url():
                        return f"http://127.0.0.1:{n_prime}/find_successor?key={self.hash_key(str(start))}"

                    try:
                        response = retry_request(requests.get, generate_finger_successor_url)
                        successor = response.json()['port']
                    except RequestException as e:
                        print(f"Error al inicializar la finger table: {e}")
                        successor = self.find_successor(self.hash_key(str(start)))
                else:
                    successor = self.find_successor(self.hash_key(str(start)))

                self.finger_table[i + 1]['node'] = successor
        

    def update_finger_table(self, n_prime):
        """
        Actualiza la finger table del nodo.
        """
        if n_prime != self.port:
            def generate_successor_url():
                return f"http://127.0.0.1:{n_prime}/find_successor?key={self.finger_table[0]['start']}"

            try:
                response = retry_request(requests.get, generate_successor_url)
                successor = response.json()['port']
            except RequestException as e:
                print(f"Error al actualizar la finger table: {e}")
                successor = self.find_successor(self.finger_table[0]['start'])
        else:
            successor = self.find_successor(self.finger_table[0]['start'])

        self.finger_table[0]['node'] = successor
        self.successor = self.finger_table[0]['node']

        for i in range(self.m - 1):
            start = self.finger_table[i + 1]['start']
            node_id = self.finger_table[i]['node']

            if self.in_interval(start, self.node_id, node_id):
                self.finger_table[i + 1]['node'] = self.finger_table[i]['node']
            else:
                if n_prime != self.port:
                    def generate_finger_successor_url():
                        return f"http://127.0.0.1:{n_prime}/find_successor?key={self.hash_key(str(start))}"

                    try:
                        response = retry_request(requests.get, generate_finger_successor_url)
                        successor = response.json()['port']
                    except RequestException as e:
                        print(f"Error al actualizar la finger table: {e}")
                        successor = self.find_successor(self.hash_key(str(start)))
                else:
                    successor = self.find_successor(self.hash_key(str(start)))

                self.finger_table[i + 1]['node'] = successor
                
    
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
        """
        Escucha mensajes de broadcast en un puerto específico.
        """
        # Crear un socket UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", port))  # Escuchar en todas las interfaces

        while True:
            data, addr = sock.recvfrom(1024)  # Buffer de 1024 bytes
            print(f"Mensaje recibido desde {addr}: {data.decode()}")
            if data.decode():
                self.update_finger_table(data.decode())

    def transfer_keys(self):
        """
        Transfiere las claves del predecesor al nodo actual.
        """
        if self.predecessor:
            def generate_keys_url():
                return f"http://127.0.0.1:{self.predecessor}/keys"

            try:
                response = retry_request(requests.get, generate_keys_url)
                keys = response.json()
            except RequestException as e:
                print(f"Error al obtener las claves del predecesor {self.predecessor}: {e}")
                keys = None

            if keys:
                for key in list(keys.keys()):  # Usamos list() para evitar modificar el diccionario durante la iteración
                    predecessor_id = self.hash_key(str(self.predecessor))
                    if self.in_interval(key, predecessor_id, self.node_id):
                        self.keys[key] = keys.pop(key)

                        def generate_delete_key_url():
                            return f"http://127.0.0.1:{self.predecessor}/keys?key={key}"

                        try:
                            retry_request(requests.delete, generate_delete_key_url)
                        except RequestException as e:
                            print(f"Error al eliminar la clave {key} del predecesor {self.predecessor}: {e}")

                        # Replicar la clave en los r sucesores
                        for successor_port in self.successor_list:
                            def generate_replicate_url():
                                return f"http://127.0.0.1:{successor_port}/replicate"

                            try:
                                retry_request(requests.post, generate_replicate_url, json={'key': key, 'value': self.keys[key]})
                            except RequestException as e:
                                print(f"Error al replicar la clave {key} en el sucesor {successor_port}: {e}")
                        


    def find_successor_with_replication(self, successor):
        """
        Encuentra un sucesor válido, utilizando la lista de sucesores como réplicas en caso de fallo.
        """
        if self.is_node_alive(self.successor):
            return self.successor

        for replica_port in self.successor_list:
            if self.is_node_alive(replica_port):
                return replica_port

        return None  # Si no se encuentra ningún sucesor válido
    
    def is_node_alive(self, node_port):
        """
        Verifica si un nodo está vivo haciendo una solicitud al endpoint /alive.
        :param node_port: Puerto del nodo a verificar.
        :return: True si el nodo responde, False en caso contrario.
        """
        def generate_alive_url():
            return f'http://127.0.0.1:{node_port}/alive'

        try:
            response = retry_request(requests.get, generate_alive_url, max_attempts=1)  # Solo un intento
            return response.status_code == 200
        except RequestException:
            return False