# import os
# from datetime import date, datetime
# from decimal import Decimal
# from pathlib import Path

# import mysql.connector
# from dotenv import load_dotenv

# load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# def connect():
#     """open a connection using the five DF_ settings from .env."""
#     return mysql.connector.connect(
#         host=os.getenv("DB_HOST", "localhost"),
#         port=int(os.getenv("DB_PORT", 3306)),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#         database=os.getenv("DB_NAME", "future_portfolio_db")
#     )

# def fetch_all(conn, sql, params=()):
#     """Run sql with its parameters (a tuple, values for each %s); return a list of dicts."""
#     with conn.cursor(dictionary=True) as cursor:
#         cursor.execute(sql, params)
#         return cursor.fetchall()

# def to_json_value(value):
#     """Turn vaules JSON can't hold into values it can: dates -> ISO text, Decimal -> float."""
#     if isinstance(value, (date, datetime)):
#         return value.isoformat()
#     if isinstance(value, Decimal):
#         return float(value)
#     raise TypeError(f"Cannot convert {type(value).__name__}to JSON")
































""""Shared database helpers for the scripts and, from module 6


connect()                
fetch_all()
to_json_value()
"""""


import os
from datetime import date, datetime
from decimal import Decimal




import mysql.connector
from dotenv import load_dotenv




load_dotenv()








def connect():
    """Open a connection using the five DB_ settings."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "123456"),
        database=os.getenv("DB_NAME", "future_portfolio_db"),
    )






def fetch_all(conn, sql, params=()):
    """Run SQL with its parameters (a tuple of values for each %s) and return all results as a list of dicts."""
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()








def to_json_value(value):
    """Turn values JSON can't hold into values it can: dates -> ISO text, Decimal -> float."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Cannot convert {type(value).__name__} to JSON")



def fetch_all(conn, sql, params=()):
    """Run a SELECT and return a list of dictionaries (one per row)."""
    with conn.cursor(dictionary=True) as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()

def execute(conn, sql, params=()):
    """Run an INSERT / UPDATE / DELETE. Returns (rows affected, new id)."""
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.rowcount,cursor.lastrowid
    


