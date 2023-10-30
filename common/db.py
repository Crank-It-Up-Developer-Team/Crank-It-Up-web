import sqlite3

from flask import abort


def get_db_connection():
    conn = sqlite3.connect("db/database.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_map(map_id):
    conn = get_db_connection()
    map = conn.execute("SELECT * FROM maps WHERE id = ?", (map_id,)).fetchone()
    conn.close()
    if map is None:
        abort(404)
    return map
