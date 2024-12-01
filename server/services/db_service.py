import mysql.connector
from config import DB_CONFIG

def save_url_to_db(url_data):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO URL (enlace, html) VALUES (%s, %s)
        """, (url_data['enlace'], url_data['html']))
        connection.commit()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_url_from_db(url_id):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM URL WHERE id=%s", (url_id,))
        return cursor.fetchone()
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_url_in_db(url_id, url_data):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE URL SET enlace=%s, html=%s WHERE id=%s
        """, (url_data['enlace'], url_data['html'], url_id))
        connection.commit()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_url_from_db(url_id):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM URL WHERE id=%s", (url_id,))
        connection.commit()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def save_link_to_db(link_data):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO Links (siteid, enlace) VALUES (%s, %s)
        """, (link_data['siteid'], link_data['enlace']))
        connection.commit()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_link_from_db(link_id):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Links WHERE id=%s", (link_id,))
        return cursor.fetchone()
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_link_in_db(link_id, link_data):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE Links SET siteid=%s, enlace=%s WHERE id=%s
        """, (link_data['siteid'], link_data['enlace'], link_id))
        connection.commit()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_link_from_db(link_id):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Links WHERE id=%s", (link_id,))
        connection.commit()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def save_file_to_db(file_data):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO Files (siteid, archivo) VALUES (%s, %s)
        """, (file_data['siteid'], file_data['archivo']))
        connection.commit()
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_file_from_db(file_id):
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Files WHERE id=%s", (file_id,))
        return cursor.fetchone()
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
         if connection.is_connected():
             cursor.close()
             connection.close()

def update_file_in_db(file_id, file_data):
   try:
       connection = mysql.connector.connect(**DB_CONFIG)
       cursor = connection.cursor()
       cursor.execute("""
           UPDATE Files SET siteid=%s, archivo=%s WHERE id=%s
       """, (file_data['siteid'], file_data['archivo'], file_id))
       connection.commit()
       return "Success"
   except Exception as e:
       return f"Error: {str(e)}"
   finally:
       if connection.is_connected():
           cursor.close()
           connection.close()

def delete_file_from_db(file_id):
   try:
       connection = mysql.connector.connect(**DB_CONFIG)
       cursor = connection.cursor()
       cursor.execute("DELETE FROM Files WHERE id=%s", (file_id,))
       connection.commit()
       return "Success"
   except Exception as e:
       return f"Error: {str(e)}"
   finally:
       if connection.is_connected():
           cursor.close()
           connection.close()
