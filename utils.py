import hashlib

bits = 12

class Node:
    def __init__(self, ip):
        self.ip = ip
        self.id = hash_key(ip)
        self.data = {}  # Almacena las URLs
        self.successor = None  # Sucesor en el anillo

    def __repr__(self):
        return f"Node(IP={self.ip}, ID={self.id})"

def hash_key(key): #160 bits?
    """Hashea una clave usando SHA-1 y devuelve un identificador de 'bits' bits."""
    hash_hex = hashlib.sha1(key.encode()).hexdigest()
    hash_int = int(hash_hex, 16)
    return hash_int % (2 ** bits)

def is_responsible(key_id, node):
    """Verifica si el nodo es responsable de un identificador."""
    if node.id < node.successor.id:
        return node.id < key_id < node.successor.id
    else:
        return (node.id < key_id < 2**bits) or (0 < key_id < node.successor.id)

def transfer_keys(new_node):
    """Transfiere las claves que ahora corresponden al nuevo nodo."""
    global current_node
    keys_to_transfer = {}
    for url, url_id in list(current_node.data.items()):
        if is_responsible(url_id, new_node):
            keys_to_transfer[url] = url_id
            del current_node.data[url]
    if keys_to_transfer:
        requests.post(f"http://{new_node.ip}/receive_keys", json=keys_to_transfer)

