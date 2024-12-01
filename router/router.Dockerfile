# Usa la imagen de Alpine como base
FROM alpine

# Instala iproute2 y utilidades necesarias para configurar el reenvío de IP
RUN apk update && apk add --no-cache iproute2 iputils

# Habilita el reenvío de IP en el contenedor
RUN echo "net.ipv4.ip_forward=1" | tee -a /etc/sysctl.conf
RUN sysctl -p

# El contenedor no necesita hacer nada más, solo habilitar el reenvío de IP
# Ejecutar el router en modo de shell
CMD ["/bin/sh"]
