"""
This turns your agent into a small web API using FastAPI.
Run it, then send it a customer message + order ID, and it replies.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from app.database import init_db
from app.agent import run_support_agent
from app.inventory_db import init_inventory_db, get_all_inventory
from app.inventory_agent import run_inventory_agent, run_inventory_check_all
from app.pricing_db import init_pricing_db, get_all_pricing
from app.pricing_agent import run_pricing_agent, run_pricing_check_all

app = FastAPI(title="E-Commerce Operations Agents API")

# Create the fake databases + sample data the first time this starts
init_db()
init_inventory_db()
init_pricing_db()


class SupportRequest(BaseModel):
    order_id: str
    message: str


@app.get("/")
def health_check():
    return {"status": "Support Agent is running"}


@app.post("/support")
def handle_support_request(req: SupportRequest):
    reply = run_support_agent(req.order_id, req.message)
    return {"order_id": req.order_id, "reply": reply}


@app.get("/inventory")
def list_inventory():
    """See all inventory items and their current stock levels."""
    return get_all_inventory()


@app.post("/inventory/check/{sku}")
def check_single_item(sku: str):
    """Runs the Inventory Agent on one item — checks stock and reorders if needed."""
    summary = run_inventory_agent(sku)
    return {"sku": sku, "summary": summary}


@app.post("/inventory/check-all")
def check_all_items():
    """Runs the Inventory Agent across every item — like a daily automated check."""
    return run_inventory_check_all()


@app.get("/pricing")
def list_pricing():
    """See our current prices, costs, and margin rules."""
    return get_all_pricing()


@app.post("/pricing/check/{sku}")
def check_single_price(sku: str):
    """Runs the Pricing Agent on one item — compares to competitors and adjusts price."""
    summary = run_pricing_agent(sku)
    return {"sku": sku, "summary": summary}


@app.post("/pricing/check-all")
def check_all_prices():
    """Runs the Pricing Agent across every item."""
    return run_pricing_check_all()
