# **Web Scraping Tool con Arquitectura Chord**

## **1. Arquitectura del Sistema**

El sistema está diseñado para ejecutar tareas de scraping distribuido utilizando la arquitectura **Chord**.

### **Roles en el Sistema**

1. **Nodos Chord:**
   - Ejecutan crawling, scraping y almacenamiento local de datos.
   - Implementan operaciones de Chord.
2. **Router lógico:**
   - Coordina la transferencia de tareas y datos entre redes.

------

## **2. Procesos del Sistema**

### **Tipos de Procesos**

1. Procesos Computacionales:
   - Crawling, scraping y hashing de URLs.
2. Procesos de Comunicación:
   - Transferencia de datos entre nodos y redes.
3. Procesos de Almacenamiento:
   - Replicación y persistencia de datos extraídos.

### **Patrones de Diseño**

- Asincronía
- Hilos
- Diseño distribuido

------

## **3. Comunicación del Sistema**

### **Tipo de Comunicación**

- Peer-To-Peer

### **Tecnologías y Protocolos**

- Sockets TCP 

------

## **4. Coordinación del Sistema**


- Los nodos utilizan el protocolo Chord para mantener la consistencia del anillo.
- Se emplean mecanismos de bloqueo distribuido para evitar condiciones de carrera al actualizar datos compartidos.
- Las decisiones sobre replicación y reasignación de claves son tomadas localmente por cada nodo siguiendo las reglas de Chord.

------

## **5. Nombrado y Localización**

### **Identificación de Recursos**

- Cada URL se mapea a una clave hash mediante SHA-1.

### **Ubicación de Datos y Servicios**

- Las claves se asignan a nodos específicos según su posición en el anillo Chord.

------

## **6. Consistencia y Replicación**

- Los datos se distribuyen entre los nodos según la tabla hash.
- Cada dato se replica en los nodos sucesores para garantizar tolerancia a fallos.
- Los nodos realizan sincronización periódica para mantener la consistencia de las réplicas.

------

## **7. Tolerancia a Fallas**

- El sistema puede continuar operando mientras al menos un nodo por red esté disponible.
