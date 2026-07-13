"""
A fake inventory table — stands in for your real Shopify/store inventory.
Each item has a current stock count and a "reorder threshold":
when stock drops below that number, the agent should reorder.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "store.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_inventory_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY,
            product_name TEXT,
            stock_count INTEGER,
            reorder_threshold INTEGER,
            reorder_quantity INTEGER,
            supplier_name TEXT,
            supplier_email TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            po_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT,
            quantity INTEGER,
            supplier_name TEXT,
            status TEXT
        )
    """)

    cur.execute("SELECT COUNT(*) FROM inventory")
    if cur.fetchone()[0] == 0:
        sample_items = [
            ("SKU001", "Wireless Mouse", 12, 10, 50, "TechSupply Co.", "orders@techsupply.example"),
            ("SKU002", "Bluetooth Speaker", 40, 15, 30, "AudioWorks Ltd.", "sales@audioworks.example"),
            ("SKU003", "Laptop Stand", 3, 10, 40, "DeskGear Inc.", "supply@deskgear.example"),
            ("SKU004", "Phone Case", 80, 20, 60, "CaseCraft", "orders@casecraft.example"),
        ]
        cur.executemany(
            "INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?)", sample_items
        )

    conn.commit()
    conn.close()


def get_all_inventory():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_item(sku: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE sku = ?", (sku,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_inventory_rule(sku, product_name, reorder_threshold, reorder_quantity, supplier_name, supplier_email):
    """Adds a new item's business rules (used for products imported from other stores)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO inventory (sku, product_name, stock_count, reorder_threshold, reorder_quantity, supplier_name, supplier_email) "
        "VALUES (?, ?, 0, ?, ?, ?, ?)",
        (sku, product_name, reorder_threshold, reorder_quantity, supplier_name, supplier_email),
    )
    conn.commit()
    conn.close()


def get_all_product_names():
    """Returns the set of product names already tracked locally (used to avoid duplicates)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT product_name FROM inventory")
    names = {row["product_name"] for row in cur.fetchall()}
    conn.close()
    return names


def save_purchase_order(sku: str, quantity: int, supplier_name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO purchase_orders (sku, quantity, supplier_name, status) VALUES (?, ?, ?, ?)",
        (sku, quantity, supplier_name, "sent"),
    )
    conn.commit()
    conn.close()
