FROM alpine:latest

# Instala herramientas necesarias para el enrutamiento
RUN apk add --no-cache iptables iproute2

# Comando para habilitar el forwarding de paquetes
CMD ["sh", "-c", "echo 1 > /proc/sys/net/ipv4/ip_forward && tail -f /dev/null"]