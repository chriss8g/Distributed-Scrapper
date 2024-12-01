#!/bin/bash

# Configuración de las redes
CLIENTS_NET="clients"
SERVERS_NET="servers"
CLIENTS_SUBNET="10.0.10.0/24"
SERVERS_SUBNET="10.0.11.0/24"

# Configuración de contenedores
ROUTER_NAME="router"
ROUTER_CLIENTS_IP="10.0.10.1"
ROUTER_SERVERS_IP="10.0.11.1"

SERVER_NAME="server1"
SERVER_IP="10.0.11.2"
SERVER_PORT=5000

CLIENT_IMAGE="cliente:latest"
SERVER_IMAGE="servidor:latest"
ROUTER_IMAGE="router:latest"

CLIENT_BASE_IP="10.0.10."
CLIENT_START_PORT=3000
NUM_CLIENTS=3

# Directorios de los Dockerfiles
ROUTER_DIR="./router"
SERVER_DIR="./server"
CLIENT_DIR="./client"

# Función para crear una red si no existe
create_network_if_not_exists() {
  local net_name=$1
  local subnet=$2
  docker network inspect $net_name >/dev/null 2>&1 || \
  docker network create --subnet=$subnet $net_name
}

# Función para construir imágenes si no existen
build_image_if_not_exists() {
  local image_name=$1
  local build_dir=$2
  if [[ "$(docker images -q $image_name 2>/dev/null)" == "" ]]; then
    echo "Construyendo imagen $image_name desde $build_dir..."
    docker build -t $image_name $build_dir
  else
    echo "Imagen $image_name ya existe."
  fi
}

# Construir imágenes
echo "Verificando y construyendo imágenes si es necesario..."
build_image_if_not_exists $ROUTER_IMAGE $ROUTER_DIR
build_image_if_not_exists $SERVER_IMAGE $SERVER_DIR
build_image_if_not_exists $CLIENT_IMAGE $CLIENT_DIR

# Crear redes
echo "Verificando y creando redes si es necesario..."
create_network_if_not_exists $CLIENTS_NET $CLIENTS_SUBNET
create_network_if_not_exists $SERVERS_NET $SERVERS_SUBNET

# Iniciar el router
echo "Iniciando el router..."
docker run -d --name $ROUTER_NAME --privileged \
  --network $CLIENTS_NET --ip $ROUTER_CLIENTS_IP $ROUTER_IMAGE

docker network connect $SERVERS_NET $ROUTER_NAME --ip $ROUTER_SERVERS_IP

# Iniciar clientes
echo "Iniciando clientes..."
for i in $(seq 1 $NUM_CLIENTS); do
  CLIENT_NAME="client$i"
  CLIENT_IP="${CLIENT_BASE_IP}$((1 + i))"
  CLIENT_HOST_PORT=$((CLIENT_START_PORT + i - 1))
  echo "Iniciando $CLIENT_NAME en IP $CLIENT_IP y puerto $CLIENT_HOST_PORT..."
  docker run --rm -d --name $CLIENT_NAME --cap-add NET_ADMIN \
    --network $CLIENTS_NET --ip $CLIENT_IP -p $CLIENT_HOST_PORT:3000 $CLIENT_IMAGE
done

# Iniciar servidor
echo "Iniciando servidor..."
docker run --rm -d --name $SERVER_NAME --cap-add NET_ADMIN \
  --network $SERVERS_NET --ip $SERVER_IP -p $SERVER_PORT:$SERVER_PORT $SERVER_IMAGE

# Mensajes de éxito y accesos
echo "Sistema levantado con éxito!"
echo "Accede a los contenedores desde:"
for i in $(seq 1 $NUM_CLIENTS); do
  CLIENT_IP="${CLIENT_BASE_IP}$((1 + i))"
  CLIENT_HOST_PORT=$((CLIENT_START_PORT + i - 1))
  echo "  Cliente$i: http://$CLIENT_IP:$CLIENT_HOST_PORT"
done
echo "  Servidor: http://$SERVER_IP:$SERVER_PORT"
