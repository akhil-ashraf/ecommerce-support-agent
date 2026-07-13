"""
Our store's own pricing data — what we currently charge and what it costs us,
so the agent can make sure any price change still keeps a healthy margin.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "store.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_pricing_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pricing (
            sku TEXT PRIMARY KEY,
            product_name TEXT,
            our_price REAL,
            our_cost REAL,
            min_margin_percent REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT,
            old_price REAL,
            new_price REAL,
            reason TEXT
        )
    """)

    cur.execute("SELECT COUNT(*) FROM pricing")
    if cur.fetchone()[0] == 0:
        # our_cost = what it costs us to buy/make it
        # min_margin_percent = the lowest profit margin we're willing to accept
        sample_prices = [
            ("SKU001", "Wireless Mouse", 15.99, 8.00, 30),
            ("SKU002", "Bluetooth Speaker", 39.99, 22.00, 25),
            ("SKU003", "Laptop Stand", 24.99, 10.00, 35),
            ("SKU004", "Phone Case", 12.99, 4.00, 40),
        ]
        cur.executemany(
            "INSERT INTO pricing VALUES (?, ?, ?, ?, ?)", sample_prices
        )

    conn.commit()
    conn.close()


def add_pricing_item(sku, product_name, our_cost, min_margin_percent):
    """Registers cost/margin rules for a new product (call this after adding the product in Shopify)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO pricing
            (sku, product_name, our_price, our_cost, min_margin_percent)
        VALUES (?, ?, 0, ?, ?)
        """,
        (sku, product_name, our_cost, min_margin_percent),
    )
    conn.commit()
    conn.close()


def get_price_info(sku: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pricing WHERE sku = ?", (sku,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_pricing():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pricing")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_price(sku: str, new_price: float, reason: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT our_price FROM pricing WHERE sku = ?", (sku,))
    old_price = cur.fetchone()["our_price"]

    cur.execute("UPDATE pricing SET our_price = ? WHERE sku = ?", (new_price, sku))
    cur.execute(
        "INSERT INTO price_history (sku, old_price, new_price, reason) VALUES (?, ?, ?, ?)",
        (sku, old_price, new_price, reason),
    )
    conn.commit()
    conn.close()
