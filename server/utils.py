import hashlib
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout
import socket
import time

M = 160  # Número de bits para los identificadores

def is_node_alive(node_port):
    """
    Verifica si un nodo está vivo haciendo una solicitud al endpoint /alive.
    :param node_port: Puerto del nodo a verificar.
    :return: True si el nodo responde, False en caso contrario.
    """
    def generate_alive_url():
        return f'http://192.168.1.{node_port}:5000/alive'

    try:
        response = retry_request(requests.get, generate_alive_url, max_attempts=1)  # Solo un intento
        return response.status_code == 200
    except RequestException:
        return False

def send_broadcast(message, port):
    # Crear un socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Dirección de broadcast (generalmente 255.255.255.255)
    # broadcast_address = "255.255.255.255"
    broadcast_address = "192.168.1.255"

    # Enviar el mensaje
    sock.sendto(message.encode(), (broadcast_address, 5000))
    print(f"Broadcast enviado: {message}")
    sock.close()

def listen_for_broadcast(port, function):
    """
    Escucha mensajes de broadcast en un puerto específico.
    """
    # Crear un socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 5000))  # Escuchar en todas las interfaces

    while True:
        data, addr = sock.recvfrom(1024)  # Buffer de 1024 bytes
        print(f"Mensaje recibido desde {addr}: {data.decode()}")
        if data.decode():
            function(data.decode())

def in_interval(id, start, end):
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

def hash_key(key):
    '''
        hashea una key
    '''
    key = str(key)
    return int(hashlib.sha1(key.encode()).hexdigest(), 16) % (2**M)

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