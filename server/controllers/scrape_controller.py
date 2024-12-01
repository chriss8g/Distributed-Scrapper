from flask import Blueprint, request, jsonify
from queue import Queue
from threading import Thread
from services.scraper_service import scrape_html, scrape_links, scrape_files

# Crear el Blueprint
scrape_bp = Blueprint('scrape', __name__)

# Crear la cola de tareas
task_queue = Queue()
workers = []
MAX_WORKERS = 5  # Número máximo de trabajadores

# Función para procesar la cola de tareas
def worker():
    while True:
        task = task_queue.get()
        if task is None:  # Finalizar el hilo
            break
        func, args, result_queue = task
        try:
            result = func(*args)
            result_queue.put(result)  # Enviar el resultado a la cola de respuesta
        except Exception as e:
            result_queue.put({"error": f"Scraping failed: {str(e)}"})
        finally:
            task_queue.task_done()

# Inicializar trabajadores
for _ in range(MAX_WORKERS):
    t = Thread(target=worker, daemon=True)
    workers.append(t)
    t.start()

# Endpoint de scraping que espera la respuesta
@scrape_bp.route('/scrape', methods=['GET'])
def enqueue_scrape_and_wait():
    url = request.args.get('url')
    scrape_type = request.args.get('type')  # Puede ser 'html', 'links' o 'files'

    if not url:
        return jsonify({"error": "URL is required"}), 400

    if scrape_type not in ['html', 'links', 'files']:
        return jsonify({"error": "Invalid scrape type"}), 400

    # Seleccionar la función de scraping correspondiente
    if scrape_type == 'html':
        scrape_func = scrape_html
    elif scrape_type == 'links':
        scrape_func = scrape_links
    elif scrape_type == 'files':
        scrape_func = scrape_files

    # Cola para almacenar el resultado
    result_queue = Queue()

    # Encolar la tarea con la función de scraping y la cola de resultados
    task_queue.put((scrape_func, [url], result_queue))

    # Bloquear hasta que la tarea se complete
    try:
        result = result_queue.get(timeout=30)  # Tiempo máximo de espera (30 segundos)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": "Task timed out or failed", "details": str(e)}), 500

# Finalizar trabajadores al cerrar la aplicación (si es necesario)
def stop_workers():
    for _ in workers:
        task_queue.put(None)
    for t in workers:
        t.join()
