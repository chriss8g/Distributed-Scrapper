#!/bin/bash

# Nombre de las redes
CLIENTS_NET="clients"
SERVERS_NET="servers"

# Subredes de las redes
CLIENTS_SUBNET="10.0.10.0/24"
SERVERS_SUBNET="10.0.11.0/24"

# IPs específicas para los contenedores
ROUTER_IP_CLIENTS="10.0.10.1"
ROUTER_IP_SERVERS="10.0.11.1"
SERVER_IP="10.0.11.2"

# Rango de puertos para los clientes
START_PORT=3000
NUM_CLIENTS=5

# Verifica si las redes ya existen, y si no, créalas
echo "Verificando redes..."
docker network inspect $CLIENTS_NET >/dev/null 2>&1 || \
docker network create --subnet=$CLIENTS_SUBNET $CLIENTS_NET

docker network inspect $SERVERS_NET >/dev/null 2>&1 || \
docker network create --subnet=$SERVERS_SUBNET $SERVERS_NET

# Levanta el contenedor del router
echo "Iniciando router..."
docker run -d --name router --privileged \
  --network $CLIENTS_NET --ip $ROUTER_IP_CLIENTS router:latest

docker network connect $SERVERS_NET router --ip $ROUTER_IP_SERVERS

# Levanta múltiples contenedores de clientes
echo "Iniciando clientes..."
for i in $(seq 1 $NUM_CLIENTS); do
  CLIENT_IP="10.0.10.$((2 + i))"
  CLIENT_PORT=$(START_PORT)
  echo "Iniciando cliente$i en IP $CLIENT_IP y puerto $CLIENT_PORT..."
  docker run --rm -d --name client$i --cap-add NET_ADMIN \
    --network $CLIENTS_NET --ip $CLIENT_IP -p $CLIENT_PORT:3000 cliente:latest
done

# Levanta el contenedor del servidor
echo "Iniciando servidor..."
docker run --rm -d --name server1 --cap-add NET_ADMIN \
  --network $SERVERS_NET --ip $SERVER_IP -p 5000:5000 servidor:latest

# Configura reglas de iptables en el router
echo "Configurando reglas de iptables en el router..."
docker exec router sh -c "
  iptables -t nat -A PREROUTING -p tcp --dport 5000 -j DNAT --to-destination $SERVER_IP:5000;
  iptables -t nat -A POSTROUTING -j MASQUERADE
"

# Reglas de iptables para los clientes
for i in $(seq 1 $NUM_CLIENTS); do
  CLIENT_IP="10.0.10.$((2 + i))"
  CLIENT_PORT=$((START_PORT + i - 1))
  echo "Configurando iptables para cliente$i en puerto $CLIENT_PORT..."
  docker exec router sh -c "
    iptables -t nat -A PREROUTING -p tcp --dport $CLIENT_PORT -j DNAT --to-destination $CLIENT_IP:3000;
  "
done

echo "Sistema levantado con éxito!"
echo "Accede a:"
for i in $(seq 1 $NUM_CLIENTS); do
  CLIENT_PORT=$((START_PORT + i - 1))
  echo "  Cliente$i: http://10.0.10.2:$CLIENT_PORT"
done
echo "  Servidor: http://10.0.11.2:5000"
