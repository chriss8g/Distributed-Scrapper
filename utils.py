import hashlib
import os
import csv
import requests

bits = 12

class Node:
    def __init__(self, ip):
        self.ip = ip
        self.id = hash_key(ip)
        self.successor = self  # Sucesor en el anillo
        self.pos_successor = self
        self.pos_pos_successor = self

    def __repr__(self):
        return f"Node(IP={self.ip}, ID={self.id})"
    
    def check_connectivity(self):
        # Verifica la conectividad de los sucesores
        successor_status = self._check_node_connectivity(self.successor.ip)
        pos_successor_status = self._check_node_connectivity(self.pos_successor.ip)
        pos_pos_successor_status = self._check_node_connectivity(self.pos_pos_successor.ip)

        # Determinar cuál caso es
        if successor_status and pos_successor_status and pos_pos_successor_status:
            # Caso 7: Nadie ha fallado
            print("Caso 7: Nadie ha fallado")
        elif not successor_status and pos_successor_status and pos_pos_successor_status:
            # Caso 1: Solo el successor ha fallado
            print("Caso 1: Solo el successor ha fallado")
            self.successor = self.pos_successor
            self.pos_successor = self.pos_pos_successor
            response = requests.get(f"http://{self.successor.ip}/get_succesors", timeout=2)
            self.pos_pos_successor = Node(response["ip2"])
        elif successor_status and not pos_successor_status and pos_pos_successor_status:
            # Caso 2: Solo el pos_successor ha fallado
            print("Caso 2: Solo el pos_successor ha fallado")
            self.pos_successor = self.pos_pos_successor
            response = requests.get(f"http://{self.pos_successor.ip}/get_succesors", timeout=2)
            self.pos_pos_successor = Node(response["ip"])
        elif successor_status and pos_successor_status and not pos_pos_successor_status:
            # Caso 3: Solo el pos_pos_successor ha fallado
            print("Caso 3: Solo el pos_pos_successor ha fallado")
            response = requests.get(f"http://{self.successor.ip}/get_succesors", timeout=2)
            updated = self._check_node_connectivity(response["ip2"])
            if(updated):
                self.pos_pos_successor = Node(response["ip"])
            else:
                self.pos_pos_successor = Node(response["ip3"])
        elif not successor_status and not pos_successor_status and pos_pos_successor_status:
            # Caso 4: Solo el successor no ha fallado (pero el pos_successor y el pos_pos_successor sí)
            print("Caso 4: Solo el pos_pos_successor no ha fallado")
            self.successor = self.pos_pos_successor
            response = requests.get(f"http://{self.successor.ip}/get_succesors", timeout=2)
            self.pos_successor = Node(response["ip"])
            self.pos_pos_successor = Node(response["ip2"])
        elif not successor_status and pos_successor_status and not pos_pos_successor_status:
            # Caso 5: Solo el pos_successor no ha fallado (pero el successor y el pos_pos_successor sí)
            print("Caso 5: Solo el pos_successor no ha fallado")
            self.successor = self.pos_successor
            response = requests.get(f"http://{self.successor.ip}/get_succesors", timeout=2)
            updated = self._check_node_connectivity(response["ip"])
            if(updated):
                self.pos_successor = Node(response["ip"])
                self.pos_pos_successor = Node(response["ip2"])
            else:
                self.pos_successor = Node(response["ip2"])
                self.pos_pos_successor = Node(response["ip3"])
        elif successor_status and not pos_successor_status and not pos_pos_successor_status:
            # Caso 6: Solo el successor no ha fallado (pero el pos_successor y el pos_pos_successor sí)
            print("Caso 6: Solo el successor no ha fallado")
            response = requests.get(f"http://{self.successor.ip}/get_succesors", timeout=2)
            updated = self._check_node_connectivity(response["ip"])
            if(updated):
                self.pos_successor = Node(response["ip"])
                self.pos_pos_successor = Node(response["ip2"])
            else:
                self.pos_successor = Node(response["ip3"])
                response = requests.get(f"http://{self.pos_successor.ip}/get_succesors", timeout=2)
                self.pos_pos_successor = Node(response["ip"])
        else:
            # Caso adicional: Todos los nodos han fallado (aunque dijiste que solo pueden fallar dos a la vez)
            print(100*"\nErdiablo: Mis 3 nodos han fallado")

    def _check_node_connectivity(self, node_ip):
        # Verifica la conectividad de un nodo específico
        if node_ip == self.ip:
            return True  # El nodo actual siempre está conectado

        try:
            response = requests.get(f"http://{node_ip}/ping", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

   
def hash_key(key): #160 bits?
    """Hashea una clave usando SHA-1 y devuelve un identificador de 'bits' bits."""
    hash_hex = hashlib.sha1(key.encode()).hexdigest()
    hash_int = int(hash_hex, 16)
    return hash_int % (2 ** bits)

def is_responsible(key_id, node):
    """Verifica si el nodo es responsable de un identificador."""
    if node.id < node.successor.id:
        return node.id < int(key_id) < node.successor.id
    else:
        return (node.id < int(key_id) < 2**bits) or (0 < key_id < node.successor.id)

def load_data(index):
    """Carga los datos desde el archivo CSV."""
    CSV_FILE = f'{index}-data_storage.csv'
    if not os.path.exists(CSV_FILE):
        return {}
    with open(CSV_FILE, mode='r') as file:
        reader = csv.reader(file)
        return {rows[0]: rows[1] for rows in reader}

def save_data(index, data):
    """Guarda los datos en el archivo CSV."""
    CSV_FILE = f'{index}-data_storage.csv'
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        for url, url_id in data.items():
            writer.writerow([url, url_id])