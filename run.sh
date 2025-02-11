#!/bin/bash

# Nombre de la imagen y el contenedor
IMAGE_NAME="chord-node"
CONTAINER_NAME="chord-node-container"

# Verificar si la imagen ya está construida
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
  echo "Construyendo la imagen Docker..."
  docker build -t $IMAGE_NAME .
else
  echo "La imagen Docker ya está construida."
fi

# Detener y eliminar el contenedor si ya existe
if [[ "$(docker ps -a -q -f name=$CONTAINER_NAME 2> /dev/null)" != "" ]]; then
  echo "Eliminando el contenedor antiguo..."
  docker stop $CONTAINER_NAME
  docker rm $CONTAINER_NAME
fi

# Levantar un nuevo contenedor
echo "Levantando un nuevo contenedor..."
docker run -d \
  --name $CONTAINER_NAME \
  -p 5000:5000 \
  -v $(pwd):/app \
  $IMAGE_NAME

echo "Contenedor levantado correctamente."