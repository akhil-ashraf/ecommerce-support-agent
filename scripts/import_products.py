"""
Imports products from ANY public Shopify store's public product listing
into your own dev store.

How this works: most Shopify storefronts expose a public JSON endpoint at
    https://{store-domain}/products.json
This is the same product data visible to any customer browsing the store —
Shopify shows it by default as part of the public storefront, not private
admin data. Some merchants disable this, in which case the script will just
get an error for that store and you'd need to pick a different one.

Usage:
    python scripts/import_products.py allbirds.com 5

This pulls 5 products from allbirds.com's public listing and creates them
as new products in YOUR OWN Shopify dev store (using your .env credentials).

Note: this copies public titles/prices/images to populate your OWN dev store
with realistic-looking sample data for testing/demos. It isn't meant for,
and shouldn't be used for, republishing someone else's catalog as a real
competing store.
"""

import sys
import requests

sys.path.append(".")  # allows running this script from the project root
from app.shopify_client import create_product


def fetch_public_products(store_domain: str, limit: int = 5):
    url = f"https://{store_domain}/products.json"
    resp = requests.get(url, params={"limit": limit})
    resp.raise_for_status()
    return resp.json().get("products", [])


def import_products(store_domain: str, limit: int = 5):
    print(f"Fetching {limit} public products from {store_domain}...")
    products = fetch_public_products(store_domain, limit)

    if not products:
        print("No products found. This store may not expose a public products.json.")
        return

    for p in products:
        title = p["title"]
        variant = p["variants"][0]
        price = float(variant["price"])
        image_url = p["images"][0]["src"] if p.get("images") else None

        print(f"Importing: {title} (${price})")
        try:
            created = create_product(title=title, price=price, image_url=image_url)
            print(f"  -> Created in your store as product ID {created['id']}")
        except requests.HTTPError as e:
            print(f"  -> Failed to create '{title}': {e}")

    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_products.py <store-domain> [limit]")
        print("Example: python scripts/import_products.py allbirds.com 5")
        sys.exit(1)

    domain = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    import_products(domain, count)
