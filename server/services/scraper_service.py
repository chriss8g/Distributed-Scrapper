import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def scrape_html(url):
    """
    Extrae el contenido HTML completo de la página.
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Error al acceder al sitio")
    return {"html": response.text}

def scrape_links(url):
    """
    Extrae todos los enlaces de una página web.
    """
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Error al acceder al sitio")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
    return {"links": links}

 
def scrape_files(url):
    """
    Extrae enlaces a archivos descargables comunes desde una página web,
    incluyendo imágenes, videos y archivos embebidos.
    """
    # Realizar la solicitud a la URL proporcionada
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Error al acceder al sitio")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    file_extensions = [
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
        '.jpg', '.png', '.jpeg', '.webp', 
        '.zip', '.mp4', '.mp3', '.avi', '.mkv', 
        '.ogg', '.wav', '.flac'
    ]
    files = []

    # Buscar archivos en enlaces (etiqueta <a>)
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(url, href)  # Convertir URL relativa a absoluta
        if any(full_url.lower().endswith(ext) for ext in file_extensions):
            files.append(full_url)

    # Buscar imágenes (etiqueta <img>)
    for img_tag in soup.find_all('img', src=True):
        src = img_tag['src']
        full_url = urljoin(url, src)  # Convertir URL relativa a absoluta
        if any(full_url.lower().endswith(ext) for ext in file_extensions):
            files.append(full_url)

    # Eliminar duplicados
    files = list(set(files))

    # Si no se encuentran archivos, retornar un mensaje
    if not files:
        return {"message": "No se encontraron archivos descargables en la página."}
    
    return {"files": files}