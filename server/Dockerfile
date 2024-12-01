# Usa la imagen base previamente construida
FROM server:base

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos del proyecto al contenedor
COPY . /app

# Expone el puerto en el que Flask se ejecutará
EXPOSE 5000

# Comando para iniciar la aplicación
CMD ["python", "app.py"]
