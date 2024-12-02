# Imagen base de Python
FROM python:3.9-slim

# Instalar curl y ping
RUN apt-get update && apt-get install -y curl iputils-ping

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia solo el archivo de dependencias primero (para aprovechar la cache de Docker)
COPY requirements.txt /app/

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt
