"""
The Inventory Agent — same LangGraph pattern as the Support Agent, but for stock.

Flow:
    1. check_stock     -> look up the item's current stock level
    2. decide          -> is it below the reorder threshold?
    3. place_order      -> if yes, draft & 'send' a purchase order to the supplier
    4. respond          -> return a summary of what happened

Note: this one doesn't strictly need an LLM (it's a simple number comparison),
but we use the LLM to write a friendly, human-readable summary message —
so it still demonstrates an "AI agent" making a judgment call, not just an if-statement.
This also gives you room to make the "decide" step smarter later (e.g. factoring in
sales velocity or seasonality) without changing the rest of the flow.
"""

import os
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from app.inventory_db import get_item, save_purchase_order
from app.mock_supplier import send_purchase_order

load_dotenv()


class InventoryState(TypedDict):
    sku: str
    item: Optional[dict]
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
    return state


def decide(state: InventoryState) -> InventoryState:
    item = state["item"]
    if not item:
        state["needs_reorder"] = False
        return state
    state["needs_reorder"] = item["stock_count"] < item["reorder_threshold"]
    return state


def place_order(state: InventoryState) -> InventoryState:
    item = state["item"]

    if not item:
        state["order_result"] = None
        return state

    if not state["needs_reorder"]:
        state["order_result"] = None
        return state

    result = send_purchase_order(
        supplier_name=item["supplier_name"],
        supplier_email=item["supplier_email"],
        product_name=item["product_name"],
        quantity=item["reorder_quantity"],
    )
    save_purchase_order(item["sku"], item["reorder_quantity"], item["supplier_name"])
    state["order_result"] = result
    return state


def respond(state: InventoryState) -> InventoryState:
    item = state["item"]

    if not item:
        state["summary"] = f"No item found with SKU {state['sku']}."
        return state

    if not state["needs_reorder"]:
        state["summary"] = (
            f"{item['product_name']} is fine — {item['stock_count']} units in stock "
            f"(threshold: {item['reorder_threshold']}). No action needed."
        )
        return state

    # Ask the LLM to phrase a nice summary of the action taken
    prompt = f"""
Write a short, friendly one-sentence internal notification for a store manager.

Facts:
- Product: {item['product_name']}
- Current stock: {item['stock_count']} (below threshold of {item['reorder_threshold']})
- Action taken: automatically ordered {item['reorder_quantity']} more units from {item['supplier_name']}

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
