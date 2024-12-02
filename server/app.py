from flask import Flask
from flask_cors import CORS
from controllers.scrape_controller import scrape_bp, stop_workers
from controllers.db_controller import db_bp

app = Flask(__name__)
CORS(app)

# Registrar Blueprints
app.register_blueprint(scrape_bp)
app.register_blueprint(db_bp)

# Agregar un endpoint / para verificar si la aplicación está corriendo
@app.route('/')
def health_check():
    return 'running'

if __name__ == "__main__":
    try:
        print("Iniciando aplicación Flask...")
        app.run(debug=True, host='0.0.0.0', use_reloader=False)  # `use_reloader=False` para evitar múltiples inicializaciones de hilos
    except KeyboardInterrupt:
        print("\nDeteniendo la aplicación...")
    finally:
        stop_workers()
        print("Aplicación cerrada.")
