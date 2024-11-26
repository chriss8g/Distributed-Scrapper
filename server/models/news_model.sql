CREATE TABLE news (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seccion VARCHAR(50),
    titulo VARCHAR(255),
    enlace TEXT,
    resumen TEXT,
    comentarios VARCHAR(50),
    imagen TEXT
);