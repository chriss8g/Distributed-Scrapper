from flask import Flask
from flask_cors import CORS
from controllers.scrape_controller import scrape_bp, task_queue, workers

app = Flask(__name__)
CORS(app)

# Registrar Blueprints
app.register_blueprint(scrape_bp)

def stop_workers():
    """
    Finaliza todos los trabajadores de forma ordenada al cerrar la aplicación.
    """
    for _ in workers:
        task_queue.put(None)  # Coloca un marcador para detener los hilos
    for worker in workers:
        worker.join()  # Espera a que terminen todos los hilos

if __name__ == "__main__":
    try:
        print("Iniciando aplicación Flask...")
        app.run(debug=True, use_reloader=False)  # `use_reloader=False` para evitar múltiples inicializaciones de hilos
    except KeyboardInterrupt:
        print("\nDeteniendo la aplicación...")
    finally:
        stop_workers()
        print("Aplicación cerrada.")
