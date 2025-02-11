# Distributed-Scrapper


This project deploys a Flask-based client and server on separate Docker networks, connected through a router.

## Setup

### Networks
- `clients`: Subnet `10.0.10.0/24`
- `servers`: Subnet `10.0.11.0/24`

### Router
- Name: `router`
- IPs: `10.0.10.254` (clients), `10.0.11.254` (servers)

### Services
- **Client**
  - Flask application in `clients` network
  - Listens on port `3000`
- **Server**
  - Flask application in `servers` network
  - Listens on port `5000`

## Commands

### Create Networks
```bash
docker network create clients --subnet 10.0.10.0/24
docker network create servers --subnet 10.0.11.0/24

Build Router

docker build -t router -f router/Dockerfile .

Run Router

docker run -itd --rm --name router router
docker network connect --ip 10.0.10.254 clients router
docker network connect --ip 10.0.11.254 servers router

Build and Run Client

docker build -t client -f client/Dockerfile .
docker run --rm -d --name client1 --cap-add NET_ADMIN --network clients client

Build and Run Server

docker build -t server -f server/Dockerfile .
docker run --rm -d --name server1 --cap-add NET_ADMIN --network servers server

Configure Router

docker exec -it router sh
iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

Endpoints

    Client: http://localhost:3000
    Server: http://localhost:5000