import requests
import random
import string

# Dirección IP y puerto del servidor Chord
SERVER_IP = "192.168.43.145"  # Cambia esto por la IP de tu servidor
SERVER_PORT = 5000        # Cambia esto por el puerto de tu servidor

# Dominio base para las URLs
BASE_DOMAIN = "https://example.com"

def generate_random_url():
    """Genera una URL aleatoria única."""
    random_path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))  # Genera un path aleatorio
    return f"{BASE_DOMAIN}/{random_path}"

def store_url(url):
    """Envía una solicitud POST para almacenar una URL en el servidor Chord."""
    try:
        response = requests.post(
            f"http://{SERVER_IP}:{SERVER_PORT}/store",
            json={"url": url},
            timeout=5  # Tiempo de espera para la solicitud
        )
        if response.status_code == 200:
            print(f"URL '{url}' almacenada correctamente.")
        else:
            print(f"Error al almacenar la URL '{url}': {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al almacenar la URL '{url}': {e}")

def main():
    """Genera 200 URLs únicas y las almacena en el servidor Chord."""
    unique_urls = set()  # Usamos un conjunto para asegurar que las URLs sean únicas
    while len(unique_urls) < 200:
        url = generate_random_url()
        unique_urls.add(url)  # Agrega la URL al conjunto (si ya existe, no se duplica)

    # Almacena las URLs en el servidor
    for url in unique_urls:
        store_url(url)

if __name__ == "__main__":
    main()