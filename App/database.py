# ─────────────────────────────────────────────
# RPR Automated — PostgreSQL Database Layer
# app/database.py
# ─────────────────────────────────────────────

import os
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv()

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "rpr_automated"),
            user=os.getenv("DB_USER", "rpr_user"),
            password=os.getenv("DB_PASSWORD", ""),
        )
    return _pool


def get_connection():
    return _get_pool().getconn()


def release_connection(conn):
    _get_pool().putconn(conn)


def test_connection() -> bool:
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        release_connection(conn)
        return True
    except Exception:
        return False
