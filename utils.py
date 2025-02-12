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

# Nombre del archivo CSV
CSV_FILE = 'data_storage.csv'

def load_data():
    """Carga los datos desde el archivo CSV."""
    if not os.path.exists(CSV_FILE):
        return {}
    with open(CSV_FILE, mode='r') as file:
        reader = csv.reader(file)
        return {rows[0]: rows[1] for rows in reader}

def save_data(data):
    """Guarda los datos en el archivo CSV."""
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        for url, url_id in data.items():
            writer.writerow([url, url_id])