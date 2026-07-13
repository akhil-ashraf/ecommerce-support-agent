"""
Scans your Shopify store for any products that don't yet have local business
rules (threshold, supplier, cost, margin) and adds sensible defaults for them —
so the Inventory and Pricing agents can manage them too.

Run this any time after importing new products:
    python scripts/sync_new_products.py
"""

import sys
sys.path.append(".")

from app.shopify_client import get_all_products
from app.inventory_db import init_inventory_db, add_inventory_rule, get_all_product_names
from app.pricing_db import init_pricing_db, add_pricing_item

# Defaults applied to any newly discovered product.
# Feel free to tweak these before running, or edit individual rows afterward
# directly in Shopify admin / via the /inventory and /pricing endpoints.
DEFAULT_REORDER_THRESHOLD = 10
DEFAULT_REORDER_QUANTITY = 30
DEFAULT_SUPPLIER_NAME = "General Import Supplier"
DEFAULT_SUPPLIER_EMAIL = "orders@general-supplier.example"
DEFAULT_MIN_MARGIN_PERCENT = 30
COST_AS_PERCENT_OF_PRICE = 0.5  # assumes cost is ~50% of the listed price


def next_sku_number(existing_names: set) -> int:
    # Our original 4 sample products used SKU001-SKU004, so start new ones at 5
    return len(existing_names) + 1


def main():
    init_inventory_db()
    init_pricing_db()

    existing_names = get_all_product_names()
    shopify_products = get_all_products()

    added = 0
    sku_counter = next_sku_number(existing_names)

    for product in shopify_products:
        title = product["title"]

        if title in existing_names:
            continue  # already tracked, skip

        variant = product["variants"][0]
        price = float(variant["price"])
        cost = round(price * COST_AS_PERCENT_OF_PRICE, 2)

        sku = f"SKU{sku_counter:03d}"
        sku_counter += 1

        add_inventory_rule(
            sku=sku,
            product_name=title,
            reorder_threshold=DEFAULT_REORDER_THRESHOLD,
            reorder_quantity=DEFAULT_REORDER_QUANTITY,
            supplier_name=DEFAULT_SUPPLIER_NAME,
            supplier_email=DEFAULT_SUPPLIER_EMAIL,
        )
        add_pricing_item(
            sku=sku,
            product_name=title,
            our_cost=cost,
            min_margin_percent=DEFAULT_MIN_MARGIN_PERCENT,
        )

        print(f"Added rules for '{title}' as {sku} (price ${price}, assumed cost ${cost})")
        added += 1

    print(f"\nDone. Added business rules for {added} new product(s).")
    if added == 0:
        print("Nothing new to add — every Shopify product is already tracked locally.")


if __name__ == "__main__":
    main()
