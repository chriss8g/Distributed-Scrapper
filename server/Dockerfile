# Usar una imagen base de Python 3.9 (puedes ajustar la versión según tus necesidades)
FROM python:3.9-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo requirements.txt al contenedor
COPY requirements.txt .

# Instalar las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Crear un directorio para los archivos de la aplicación
RUN mkdir /app/src

# Copiar los archivos api.py, node.py y utils.py al directorio src
COPY api.py node.py utils.py /app/src/

# Configurar un volumen para los archivos de la aplicación
VOLUME /app/src

# Exponer el puerto en el que corre la aplicación Flask (por defecto 5000)
EXPOSE 5000

# Comando para ejecutar la aplicación Flask
CMD ["python", "/app/src/api.py"]