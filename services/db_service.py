import mysql.connector
from config import DB_CONFIG

def save_to_db(news_list):
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = connection.cursor()
        for news in news_list:
            cursor.execute("""
                INSERT INTO news (seccion, titulo, enlace, resumen, comentarios, imagen)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (news['seccion'], news['titulo'], news['enlace'], news['resumen'], news['comentarios'], news['imagen']))
        connection.commit()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
