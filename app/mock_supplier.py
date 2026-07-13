"""
Real supplier ordering usually means sending an email or hitting a supplier's
ordering API. Since we don't have a real supplier account, this file just
'pretends' to send the purchase order — it prints/logs it instead.

Later, you could swap this function's body for a real email send (e.g. using
a free service like SendGrid's free tier) without changing anything else.
"""


def send_purchase_order(supplier_name: str, supplier_email: str, product_name: str, quantity: int):
    """Simulates sending a purchase order to a supplier."""
    message = (
        f"[SIMULATED EMAIL to {supplier_email}]\n"
        f"To: {supplier_name}\n"
        f"Subject: Purchase Order - {product_name}\n"
        f"Body: Please supply {quantity} units of {product_name} at your earliest convenience."
    )
    print(message)  # in a real system, this would call an email API instead
    return {"status": "sent", "supplier": supplier_name, "quantity": quantity}
