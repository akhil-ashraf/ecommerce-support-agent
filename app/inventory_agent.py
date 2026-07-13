"""
The Inventory Agent — same LangGraph pattern as before, but now checking REAL
stock levels from your Shopify Dev Store instead of fake local numbers.

Business rules (threshold, reorder quantity, supplier info) still live in your
local database (inventory_db.py) — only the live stock count and the actual
stock update come from Shopify. This mirrors how a real system would work:
your own rules engine, synced against a live commerce platform.

Flow:
    1. check_stock     -> pull the item's real-time stock level from Shopify
    2. decide          -> is it below the reorder threshold (from our local rules)?
    3. place_order      -> if yes, 'send' a purchase order AND update the real
                          stock level in Shopify to reflect the restock
    4. respond          -> return a summary of what happened
"""

import os
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from app.inventory_db import get_item, save_purchase_order
from app.mock_supplier import send_purchase_order
from app.shopify_client import get_product_by_title, set_stock_level

load_dotenv()


class InventoryState(TypedDict):
    sku: str
    item: Optional[dict]           # our local business rules (threshold, supplier, etc.)
    shopify_data: Optional[dict]   # live data from Shopify (real stock, variant id, etc.)
    needs_reorder: Optional[bool]
    order_result: Optional[dict]
    summary: Optional[str]


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=os.environ.get("GROQ_API_KEY"),
)


def check_stock(state: InventoryState) -> InventoryState:
    item = get_item(state["sku"])
    state["item"] = item

    if item:
        state["shopify_data"] = get_product_by_title(item["product_name"])
    else:
        state["shopify_data"] = None

    return state


def decide(state: InventoryState) -> InventoryState:
    item = state["item"]
    shopify_data = state["shopify_data"]

    if not item or not shopify_data:
        state["needs_reorder"] = False
        return state

    state["needs_reorder"] = shopify_data["stock_count"] < item["reorder_threshold"]
    return state


def place_order(state: InventoryState) -> InventoryState:
    item = state["item"]
    shopify_data = state["shopify_data"]

    if not item or not shopify_data or not state["needs_reorder"]:
        state["order_result"] = None
        return state

    # 1. Simulate sending the purchase order to the supplier (still mocked, since
    #    a real supplier integration needs a real supplier account)
    result = send_purchase_order(
        supplier_name=item["supplier_name"],
        supplier_email=item["supplier_email"],
        product_name=item["product_name"],
        quantity=item["reorder_quantity"],
    )
    save_purchase_order(item["sku"], item["reorder_quantity"], item["supplier_name"])

    # 2. Actually update the REAL stock level in Shopify to reflect the restock
    new_stock = shopify_data["stock_count"] + item["reorder_quantity"]
    set_stock_level(shopify_data["inventory_item_id"], new_stock)
    shopify_data["stock_count"] = new_stock  # keep state in sync for the response step

    state["order_result"] = result
    return state


def respond(state: InventoryState) -> InventoryState:
    item = state["item"]
    shopify_data = state["shopify_data"]

    if not item:
        state["summary"] = f"No item found with SKU {state['sku']}."
        return state

    if not shopify_data:
        state["summary"] = (
            f"Couldn't find '{item['product_name']}' in Shopify. "
            f"Make sure a product with this exact title exists in your store."
        )
        return state

    if not state["needs_reorder"]:
        state["summary"] = (
            f"{item['product_name']} is fine — {shopify_data['stock_count']} units in stock "
            f"(threshold: {item['reorder_threshold']}). No action needed."
        )
        return state

    prompt = f"""
Write a short, friendly one-sentence internal notification for a store manager.

Facts:
- Product: {item['product_name']}
- Stock before reorder was below threshold of {item['reorder_threshold']}
- Action taken: automatically ordered {item['reorder_quantity']} more units from {item['supplier_name']}
- New live stock level in Shopify: {shopify_data['stock_count']}

Just write the one sentence notification, nothing else.
"""
    result = llm.invoke(prompt)
    state["summary"] = result.content.strip()
    return state


def build_inventory_graph():
    graph = StateGraph(InventoryState)

    graph.add_node("check_stock", check_stock)
    graph.add_node("decide", decide)
    graph.add_node("place_order", place_order)
    graph.add_node("respond", respond)

    graph.set_entry_point("check_stock")
    graph.add_edge("check_stock", "decide")
    graph.add_edge("decide", "place_order")
    graph.add_edge("place_order", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


inventory_agent = build_inventory_graph()


def run_inventory_agent(sku: str) -> str:
    result = inventory_agent.invoke({
        "sku": sku,
        "item": None,
        "shopify_data": None,
        "needs_reorder": None,
        "order_result": None,
        "summary": None,
    })
    return result["summary"]


def run_inventory_check_all() -> list:
    """Runs the agent across every item in inventory — useful for a daily cron-style check."""
    from app.inventory_db import get_all_inventory
    summaries = []
    for item in get_all_inventory():
        summaries.append({
            "sku": item["sku"],
            "product": item["product_name"],
            "summary": run_inventory_agent(item["sku"]),
        })
    return summaries
