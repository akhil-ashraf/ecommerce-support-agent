"""
Real shipping APIs (Shippo, EasyPost, etc.) need business verification or payment.
This file FAKES that API so your agent has something real to call.
Later, if you want, you just swap this function's body for a real API call —
nothing else in the project needs to change.
"""

# Pretend tracking data, keyed by tracking number
FAKE_TRACKING_DB = {
    "TRK111": {"status": "In Transit", "eta_days": 2, "location": "Dubai Hub"},
    "TRK222": {"status": "Delivered", "eta_days": 0, "location": "Customer Address"},
    "TRK333": {"status": "Delayed", "eta_days": 5, "location": "Customs"},
    "TRK444": {"status": "Delivered", "eta_days": 0, "location": "Customer Address"},
}


def get_tracking_status(tracking_number: str):
    """Simulates calling a shipping provider's API."""
    return FAKE_TRACKING_DB.get(
        tracking_number,
        {"status": "Unknown", "eta_days": None, "location": "Unknown"}
    )
