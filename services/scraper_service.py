import requests
from bs4 import BeautifulSoup

def scrape_news(keyword):
    url = "https://www.juventudrebelde.cu/"  # URL base
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Error al acceder al sitio"}
    
    soup = BeautifulSoup(response.content, 'html.parser')
    news_list = []

    # Buscar las noticias en el nuevo formato
    for noticia in soup.find_all('div', class_='item-news-box'):
        # Extraer sección
        section_element = noticia.find('span', class_='section')
        section = section_element.text.strip() if section_element else 'Sin sección'

        # Extraer título
        titulo_element = noticia.find('span', class_='title')
        titulo = titulo_element.text.strip() if titulo_element else 'Sin título'

        # Verificar si el título contiene la palabra clave
        if keyword.lower() not in titulo.lower():
            continue

        # Extraer enlace
        enlace_element = noticia.find('a', href=True)
        enlace = enlace_element['href'] if enlace_element else 'Sin enlace'

        # Extraer resumen
        resumen_element = noticia.find('p', class_='sumary')
        resumen = resumen_element.text.strip() if resumen_element else 'Sin resumen'

        # Extraer comentarios
        comentarios_element = noticia.find('span', class_='comments')
        comentarios = comentarios_element.text.strip() if comentarios_element else '0'

        # Extraer imagen
        imagen_element = noticia.find('img', class_='img-responsive')
        imagen = imagen_element['src'] if imagen_element else 'Sin imagen'

        # Añadir noticia a la lista
        news_list.append({
            "seccion": section,
            "titulo": titulo,
            "enlace": enlace,
            "resumen": resumen,
            "comentarios": comentarios,
            "imagen": imagen
        })

    return news_list

