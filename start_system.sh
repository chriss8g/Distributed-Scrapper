#!/bin/bash

# Configuración de las redes
CLIENTS_NET="clients"
SERVERS_NET="servers"
CLIENTS_SUBNET="10.0.10.0/24"
SERVERS_SUBNET="10.0.11.0/24"

# Configuración de contenedores
ROUTER_NAME="router"
ROUTER_CLIENTS_IP="10.0.10.254"
ROUTER_SERVERS_IP="10.0.11.1"

SERVER_NAME="server1"
SERVER_IP="10.0.11.2"
SERVER_PORT=5000

CLIENT_IMAGE="cliente:latest"
SERVER_IMAGE="servidor:latest"
ROUTER_IMAGE="router:latest"
BASE_IMAGE="server:base"  # Nombre de la imagen base

CLIENT_BASE_IP="10.0.10."
CLIENT_START_PORT=3000
NUM_CLIENTS=3

# Directorios de los Dockerfiles
ROUTER_DIR="./router"
SERVER_DIR="./server"
CLIENT_DIR="./client"
BASE_DIR="./"  # Directorio del Dockerfile base

# Función para crear una red si no existe
create_network_if_not_exists() {
  local net_name=$1
  local subnet=$2
  docker network inspect $net_name >/dev/null 2>&1
  if [ $? -ne 0 ]; then
    docker network create --subnet=$subnet $net_name
  fi
}

# Función para construir imágenes si no existen
build_image_if_not_exists() {
  local image_name=$1
  local build_dir=$2
  if [[ "$(docker images -q $image_name 2>/dev/null)" == "" ]]; then
    echo "Construyendo imagen $image_name desde $build_dir..."
    docker build -t $image_name $build_dir || { echo "Error al construir la imagen $image_name";  }
  else
    echo "Imagen $image_name ya existe."
  fi
}

# Construir la imagen base si no existe
echo "Verificando y construyendo imagen base si es necesario..."
build_image_if_not_exists $BASE_IMAGE $BASE_DIR

# Construir las imágenes de cliente y servidor
echo "Verificando y construyendo imágenes si es necesario..."
build_image_if_not_exists $ROUTER_IMAGE $ROUTER_DIR
build_image_if_not_exists $SERVER_IMAGE $SERVER_DIR
build_image_if_not_exists $CLIENT_IMAGE $CLIENT_DIR

# Crear redes
echo "Verificando y creando redes si es necesario..."
create_network_if_not_exists $CLIENTS_NET $CLIENTS_SUBNET
create_network_if_not_exists $SERVERS_NET $SERVERS_SUBNET

echo "Iniciando el router..."
docker run -itd --rm --name $ROUTER_NAME $ROUTER_IMAGE
docker network connect --ip 10.0.10.254 $CLIENTS_NET $ROUTER_NAME
docker network connect --ip 10.0.11.254 $SERVERS_NET $ROUTER_NAME

# Iniciar clientes
echo "Iniciando clientes..."
for i in $(seq 1 $NUM_CLIENTS); do
  CLIENT_NAME="client$i"
  CLIENT_IP="${CLIENT_BASE_IP}$((1 + i))"
  CLIENT_HOST_PORT=$((CLIENT_START_PORT + i - 1))
  echo "Iniciando $CLIENT_NAME en IP $CLIENT_IP y puerto $CLIENT_HOST_PORT..."
  docker run --rm -d --name $CLIENT_NAME --cap-add NET_ADMIN \
    --network $CLIENTS_NET --ip $CLIENT_IP -p $CLIENT_HOST_PORT:3000 $CLIENT_IMAGE || { echo "Error al iniciar el cliente $CLIENT_NAME";  }
done

# Iniciar servidor
echo "Iniciando servidor..."
docker run --rm -d --name $SERVER_NAME --cap-add NET_ADMIN \
  --network $SERVERS_NET --ip $SERVER_IP -p $SERVER_PORT:$SERVER_PORT $SERVER_IMAGE || { echo "Error al iniciar el servidor";   }

# Configura reglas de iptables en el router
echo "Configurando reglas de iptables en el router..."
docker exec $ROUTER_NAME sh -c "iptables -t nat -A PREROUTING -p tcp --dport $SERVER_PORT -j DNAT --to-destination $SERVER_IP:$SERVER_PORT"
docker exec $ROUTER_NAME sh -c "iptables -t nat -A POSTROUTING -j MASQUERADE"

# Reglas de iptables para los clientes
for i in $(seq 1 $NUM_CLIENTS); do
  CLIENT_IP="10.0.10.$((1 + i))"
  CLIENT_PORT=$((CLIENT_START_PORT + i - 1))
  echo "Configurando iptables para cliente$i en puerto $CLIENT_PORT..."
  docker exec $ROUTER_NAME sh -c "
    iptables -t nat -A PREROUTING -p tcp --dport $CLIENT_PORT -j DNAT --to-destination $CLIENT_IP:3000;
  "
done

# Mensajes de éxito y accesos
echo "Sistema levantado con éxito!"
echo "Accede a los contenedores desde:"
for i in $(seq 1 $NUM_CLIENTS); do
  CLIENT_IP="${CLIENT_BASE_IP}$((1 + i))"
  CLIENT_HOST_PORT=$((CLIENT_START_PORT + i - 1))
  echo "  Cliente$i: http://$CLIENT_IP:$CLIENT_HOST_PORT"
done
echo "  Servidor: http://$SERVER_IP:$SERVER_PORT"
