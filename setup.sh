#!/bin/bash

# Variables
NETWORK_SERVER="scraper-server-network"
NETWORK_CLIENT="scraper-client-network"
ROUTER_CONTAINER="scraper-router"
SERVER_IMAGE="scraper-server-image"
CLIENT_IMAGE="scraper-client-image"
ROUTER_IMAGE="scraper-router-image"

# Paso 1: Verificar y crear las redes Docker
echo "Verificando y creando redes Docker..."
if ! docker network inspect $NETWORK_SERVER &>/dev/null; then
  docker network create $NETWORK_SERVER --subnet=192.168.1.0/24
else
  echo "La red $NETWORK_SERVER ya existe."
fi

if ! docker network inspect $NETWORK_CLIENT &>/dev/null; then
  docker network create $NETWORK_CLIENT --subnet=192.168.2.0/24
else
  echo "La red $NETWORK_CLIENT ya existe."
fi

# Paso 2: Verificar y construir las imágenes
echo "Verificando y construyendo imágenes..."
if ! docker images --format "{{.Repository}}" | grep -q $SERVER_IMAGE; then
  echo "Construyendo imagen del servidor..."
  docker build -t $SERVER_IMAGE ./server
else
  echo "La imagen $SERVER_IMAGE ya existe."
fi

if ! docker images --format "{{.Repository}}" | grep -q $CLIENT_IMAGE; then
  echo "Construyendo imagen del cliente..."
  docker build -t $CLIENT_IMAGE ./client
else
  echo "La imagen $CLIENT_IMAGE ya existe."
fi

if ! docker images --format "{{.Repository}}" | grep -q $ROUTER_IMAGE; then
  echo "Construyendo imagen del router..."
  docker build -t $ROUTER_IMAGE ./router
else
  echo "La imagen $ROUTER_IMAGE ya existe."
fi

# Paso 3: Detener y eliminar contenedores existentes
echo "Deteniendo y eliminando contenedores existentes..."
for container in $(docker ps -aq --filter name="scraper-"); do
  docker stop $container
  docker rm $container
done

# Paso 4: Iniciar el router
echo "Iniciando el router..."
docker run -d --name $ROUTER_CONTAINER \
  --privileged \
  --network $NETWORK_SERVER \
  --ip 192.168.1.2 \
  $ROUTER_IMAGE

# Conectar el router a la red de clientes
docker network connect $NETWORK_CLIENT $ROUTER_CONTAINER --ip 192.168.2.2

# Paso 5: Iniciar los servidores
echo "Iniciando servidores..."
for i in {1..5}; do
  SERVER_CONTAINER="server-$i"
  docker run -d --name $SERVER_CONTAINER \
    --network $NETWORK_SERVER \
    --ip 192.168.1.$((i + 2)) \
    $SERVER_IMAGE
done

# Paso 6: Unir los servidores al sistema distribuido
echo "Uniendo servidores al sistema distribuido..."
for i in {1..5}; do
  SERVER_IP="192.168.1.$((i + 2))"
  echo "Enviando solicitud al servidor $SERVER_IP..."
  curl -X POST http://$SERVER_IP:5000/join \
        -H "Content-Type: application/json" \
        -d '{"ip": "192.168.1.3"}'
done

# Paso 7: Iniciar los clientes
echo "Iniciando clientes..."
for i in {1..2}; do
  CLIENT_CONTAINER="client-$i"
  docker run -d --name $CLIENT_CONTAINER \
    --network $NETWORK_CLIENT \
    --ip 192.168.2.$((i + 2)) \
    $CLIENT_IMAGE
done

# Paso 8: Configurar el enrutamiento para los clientes
echo "Configurando enrutamiento para los clientes..."
for i in {1..2}; do
  CLIENT_CONTAINER="client-$i"
  docker exec $CLIENT_CONTAINER sh -c "ip route add 192.168.1.0/24 via 192.168.2.2"
done

echo "Configuración completada."