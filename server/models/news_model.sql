CREATE TABLE URL (
    id INT AUTO_INCREMENT PRIMARY KEY,
    enlace TEXT,
    html TEXT
);

CREATE TABLE Links (
    id INT AUTO_INCREMENT PRIMARY KEY,
    siteid INT,  
    enlace TEXT,
    FOREIGN KEY (siteid) REFERENCES URL(id)  
);

CREATE TABLE Files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    siteid INT,  
    archivo TEXT,
    FOREIGN KEY (siteid) REFERENCES URL(id)  
);
