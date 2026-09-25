"""
Database configuration for WAMP's MySQL server.
Default WAMP MySQL credentials: user='root', password='' (empty), host='localhost', port=3306
Change these values if your WAMP setup uses different credentials.
"""

import mysql.connector
from mysql.connector import Error


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # default WAMP password is empty
    "database": "attendance_system",
    "port": 3306
}


def get_connection():
    """Returns a new MySQL connection using the config above."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] Could not connect to MySQL: {e}")
        raise
