#!/bin/bash

# Variables
NETWORK_SERVER="scraper-server-network"
NETWORK_CLIENT="scraper-client-network"
ROUTER_CONTAINER="scraper-router"
SERVER_IMAGE="scraper-server-image"
CLIENT_IMAGE="scraper-client-image"
ROUTER_IMAGE="scraper-router-image"
CLIENT_PORTS=(8080 8081)  # Puertos del host para mapear a los clientes
SERVER_PORTS=(8000 8001 8002 8003 8004 8005)  # Puertos del host para mapear a los clientes

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
docker ps -aq --filter name="scraper-" | xargs -r docker rm -f

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
for i in {1..1}; do
  SERVER_CONTAINER="scraper-server-$i"
  HOST_PORT=${SERVER_PORTS[$i]}
  docker run -d --name $SERVER_CONTAINER \
    --network $NETWORK_SERVER \
    --ip 192.168.1.$((i + 2)) \
    -v "$(pwd)/server:/app/src" \
    -p $HOST_PORT:5000 \
    $SERVER_IMAGE
done

# Paso 6: Unir los servidores al sistema distribuido
echo "Uniendo servidores al sistema distribuido..."
for i in {1..1}; do
  SERVER_IP="192.168.1.$((i + 2))"
  echo "Enviando solicitud al servidor $SERVER_IP..."
  curl -X POST http://$SERVER_IP:5000/join \
        -H "Content-Type: application/json" \
        -d '{"ip": "192.168.1.3"}'
done

# Paso 7: Iniciar clientes con mapeo de puertos
echo "Iniciando clientes con mapeo de puertos..."
for i in {0..0}; do  # Índices 0 y 1 para 2 clientes
  CLIENT_CONTAINER="scraper-client-$((i+1))"
  HOST_PORT=${CLIENT_PORTS[$i]}
  echo "Cliente $CLIENT_CONTAINER accesible en puerto $HOST_PORT"
  docker run --rm -d --name $CLIENT_CONTAINER \
    --network $NETWORK_CLIENT \
    --ip 192.168.2.$((i + 3)) \
    -v "$(pwd)/client:/app/src" \
    -p $HOST_PORT:3000 \
    $CLIENT_IMAGE
done

# Paso 8: Configurar enrutamiento (sin cambios)
echo "Configurando enrutamiento para los clientes..."
for i in {1..1}; do
  CLIENT_CONTAINER="scraper-client-$i"
  docker exec $CLIENT_CONTAINER sh -c "ip route add 192.168.1.0/24 via 192.168.2.2"
done

echo "Configuración completada."
echo -e "\nAccede a las aplicaciones web en:"
echo " - Cliente 1: http://localhost:${CLIENT_PORTS[0]}"
echo " - Cliente 2: http://localhost:${CLIENT_PORTS[1]}"