"""
Real competitor price scraping (Amazon, eBay, etc.) usually needs paid tools
or gets blocked without proxies. This file FAKES that data source instead —
a small sample of 'what competitors are charging' for the same products.

Later, you could swap this function's body for a real scraping/marketplace-API
call without changing anything else in the project.
"""

FAKE_COMPETITOR_PRICES = {
    "SKU001": [14.49, 16.99, 13.99],   # Wireless Mouse - seen at 3 competitors
    "SKU002": [42.00, 44.50, 45.99],   # Bluetooth Speaker
    "SKU003": [19.99, 21.50, 20.00],   # Laptop Stand
    "SKU004": [11.99, 13.49, 12.50],   # Phone Case
}


def get_competitor_prices(sku: str):
    """Simulates pulling live competitor prices from external marketplaces."""
    prices = FAKE_COMPETITOR_PRICES.get(sku, [])
    if not prices:
        return {"prices": [], "average": None, "lowest": None}
    return {
        "prices": prices,
        "average": round(sum(prices) / len(prices), 2),
        "lowest": min(prices),
    }
