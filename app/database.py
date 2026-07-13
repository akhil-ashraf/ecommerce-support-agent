"""
This file creates a small fake database (SQLite) with a few sample orders.
Think of this as pretending to be your Shopify store's order list.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "store.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db():
    """Creates the orders table and fills it with sample data (only runs once)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT,
            product TEXT,
            status TEXT,
            tracking_number TEXT,
            refunded INTEGER DEFAULT 0
        )
    """)

    # Only insert sample rows if the table is empty
    cur.execute("SELECT COUNT(*) FROM orders")
    if cur.fetchone()[0] == 0:
        sample_orders = [
            ("ORD1001", "Akhil Sharma", "Wireless Mouse", "shipped", "TRK111", 0),
            ("ORD1002", "Fatima Al Nuaimi", "Bluetooth Speaker", "delivered", "TRK222", 0),
            ("ORD1003", "John Miller", "Laptop Stand", "delayed", "TRK333", 0),
            ("ORD1004", "Sara Khan", "Phone Case", "delivered", "TRK444", 1),  # already refunded
        ]
        cur.executemany(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", sample_orders
        )

    conn.commit()
    conn.close()


def get_order(order_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_refunded(order_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET refunded = 1 WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()
