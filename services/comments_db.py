import sqlite3
from pathlib import Path

DB_PATH = Path("data/sales_notes.db")


def init_db():

    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT,
            comment TEXT,
            user TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_comment(
    customer,
    comment,
    user,
    created_at
):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        INSERT INTO comments (
            customer,
            comment,
            user,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            customer,
            comment,
            user,
            created_at
        )
    )

    conn.commit()
    conn.close()


def get_comments(customer):

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            user,
            created_at,
            comment
        FROM comments
        WHERE customer = ?
        ORDER BY id DESC
        """,
        (customer,)
    )

    rows = cur.fetchall()

    conn.close()

    return rows


def delete_comment(comment_id):

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        DELETE FROM comments
        WHERE id = ?
        """,
        (comment_id,)
    )

    conn.commit()
    conn.close()

def get_all_comments():

    conn = sqlite3.connect(DB_PATH)

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            customer,
            user,
            created_at,
            comment
        FROM comments
        ORDER BY id DESC
        """
    )

    rows = cur.fetchall()

    conn.close()

    return rows