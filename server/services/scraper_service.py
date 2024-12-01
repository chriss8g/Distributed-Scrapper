import requests
from bs4 import BeautifulSoup

def scrape_elements(url, elements = ["html", "enlaces", "archivos"]):
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Error al acceder al sitio"}
    
    soup = BeautifulSoup(response.content, 'html.parser')
    scraped_data = {}

    # Extraer elementos según la lista proporcionada
    for element in elements:
        if element == "html":
            scraped_data["html"] = str(soup)  # Extraer todo el HTML
        elif element == "links":
            links = [a['href'] for a in soup.find_all('a', href=True)]
            scraped_data["links"] = links  # Extraer todos los enlaces
        elif element == "files":
            files = []  # Extraer enlaces a documentos
            for a in soup.find_all('a', href=True):
                if a['href'].endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
                    files.append(a['href'])
            scraped_data["files"] = files  # Extraer enlaces a archivos

    return scraped_data

# # Ejemplo de uso
# url = "https://www.juventudrebelde.cu/"
# elements_to_scrape = ["html", "enlaces", "archivos"]
# result = scrape_elements(url, elements_to_scrape)
# print(result)
