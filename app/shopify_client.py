"""
Talks to your real Shopify Dev Store using the Admin API.
This replaces the fake stock/price numbers with live data from an actual store.

You'll need two values in your .env file:
    SHOPIFY_STORE_URL=akhil-ops-demo.myshopify.com
    SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxx

Both come from Settings -> Apps and sales channels -> Develop apps -> your app
-> API credentials, in your Shopify Partner dev store admin.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.environ.get("SHOPIFY_STORE_URL")  # e.g. akhil-ops-demo.myshopify.com
SHOPIFY_ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2024-10"

BASE_URL = f"https://{SHOPIFY_STORE_URL}/admin/api/{API_VERSION}"

HEADERS = {
    "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
    "Content-Type": "application/json",
}

_location_id_cache = None  # cached after first lookup, since it rarely changes


def get_primary_location_id():
    """Shopify tracks inventory per 'location' (like a warehouse). Dev stores have one by default."""
    global _location_id_cache
    if _location_id_cache:
        return _location_id_cache

    resp = requests.get(f"{BASE_URL}/locations.json", headers=HEADERS)
    resp.raise_for_status()
    locations = resp.json()["locations"]
    _location_id_cache = locations[0]["id"]
    return _location_id_cache


def get_product_by_title(title: str):
    """
    Finds a product in Shopify by its title and returns the key IDs/values
    our agents need: variant id, inventory item id, current price, and stock.
    """
    resp = requests.get(
        f"{BASE_URL}/products.json",
        headers=HEADERS,
        params={"title": title, "limit": 1},
    )
    resp.raise_for_status()
    products = resp.json()["products"]

    if not products:
        return None

    product = products[0]
    variant = product["variants"][0]  # assumes one variant per product, fine for this project

    inventory_item_id = variant["inventory_item_id"]
    stock = get_stock_level(inventory_item_id)

    return {
        "product_id": product["id"],
        "variant_id": variant["id"],
        "inventory_item_id": inventory_item_id,
        "price": float(variant["price"]),
        "stock_count": stock,
    }


def get_stock_level(inventory_item_id: int) -> int:
    """Looks up the current available stock for one inventory item."""
    location_id = get_primary_location_id()
    resp = requests.get(
        f"{BASE_URL}/inventory_levels.json",
        headers=HEADERS,
        params={"inventory_item_ids": inventory_item_id, "location_ids": location_id},
    )
    resp.raise_for_status()
    levels = resp.json()["inventory_levels"]
    return levels[0]["available"] if levels else 0


def set_stock_level(inventory_item_id: int, new_quantity: int):
    """Sets the absolute stock quantity for an item (used after a simulated reorder)."""
    location_id = get_primary_location_id()
    resp = requests.post(
        f"{BASE_URL}/inventory_levels/set.json",
        headers=HEADERS,
        json={
            "location_id": location_id,
            "inventory_item_id": inventory_item_id,
            "available": new_quantity,
        },
    )
    resp.raise_for_status()
    return resp.json()


def get_all_products():
    """Returns all products currently in your Shopify store (up to 250)."""
    resp = requests.get(f"{BASE_URL}/products.json", headers=HEADERS, params={"limit": 250})
    resp.raise_for_status()
    return resp.json()["products"]


def create_product(title: str, price: float, sku: str = None, image_url: str = None):
    """Creates a new product in YOUR store (used when importing sample products)."""
    variant = {"price": str(price)}
    if sku:
        variant["sku"] = sku

    payload = {
        "product": {
            "title": title,
            "variants": [variant],
        }
    }
    if image_url:
        payload["product"]["images"] = [{"src": image_url}]

    resp = requests.post(f"{BASE_URL}/products.json", headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["product"]


def update_price(variant_id: int, new_price: float):
    """Updates a product variant's price in Shopify."""
    resp = requests.put(
        f"{BASE_URL}/variants/{variant_id}.json",
        headers=HEADERS,
        json={"variant": {"id": variant_id, "price": str(new_price)}},
    )
    resp.raise_for_status()
    return resp.json()
