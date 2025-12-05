from typing import Dict, Any
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'fintech_db')
DB_USER = os.getenv('DB_USER', 'fintech_user')
DB_PASS = os.getenv('DB_PASS', 'fintech_pass')


def get_connection():
    """Return a new psycopg2 connection."""
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
    )
    return conn


def query(conn, sql: str, params: tuple = ()) -> list[Dict[str, Any]]:
    """Execute a query using the provided connection."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        try:
            rows = cur.fetchall()
        except psycopg2.ProgrammingError:
            rows = []
    return rows


def execute(sql: str, params: tuple = ()): 
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()
