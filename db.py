import mysql.connector

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="06102003",
        database="ainhandang1"
    )
    return conn
