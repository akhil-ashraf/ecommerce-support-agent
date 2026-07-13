"""
The Pricing Agent — same LangGraph pattern, but now checking and updating the
REAL price of the product in your Shopify Dev Store.

Business rules (cost, minimum margin) still live in your local database
(pricing_db.py) — only the live price comes from, and gets written back to,
Shopify. The margin safety floor still applies in code, unconditionally.

Flow:
    1. get_our_price        -> pull our current live price from Shopify + our cost/margin rules locally
    2. get_competitor_prices -> check what competitors are charging (fake data)
    3. decide                -> ask the LLM to suggest a new price
    4. apply_price            -> update the REAL price in Shopify (with a hard safety floor)
    5. respond                -> summarize what changed and why
"""

import os
import re
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from app.pricing_db import get_price_info, update_price as save_price_history
from app.mock_competitor import get_competitor_prices
from app.shopify_client import get_product_by_title, update_price as update_shopify_price

load_dotenv()


class PricingState(TypedDict):
    sku: str
    pricing_info: Optional[dict]     # our local cost/margin rules
    shopify_data: Optional[dict]     # live Shopify price + variant id
    competitor_data: Optional[dict]
    suggested_price: Optional[float]
    final_price: Optional[float]
    summary: Optional[str]


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=os.environ.get("GROQ_API_KEY"),
)


def get_our_price(state: PricingState) -> PricingState:
    info = get_price_info(state["sku"])
    state["pricing_info"] = info
    state["shopify_data"] = get_product_by_title(info["product_name"]) if info else None
    return state


def fetch_competitor_prices(state: PricingState) -> PricingState:
    state["competitor_data"] = get_competitor_prices(state["sku"])
    return state


def decide(state: PricingState) -> PricingState:
    info = state["pricing_info"]
    shopify_data = state["shopify_data"]
    comp = state["competitor_data"]

    if not info or not shopify_data or not comp["prices"]:
        state["suggested_price"] = None
        return state

    prompt = f"""
You are a pricing agent for an online store. Suggest a new price for this product.

Product: {info['product_name']}
Our current live price: ${shopify_data['price']}
Our cost: ${info['our_cost']}
Competitor prices seen: {comp['prices']}
Competitor average: ${comp['average']}
Competitor lowest: ${comp['lowest']}

Rules to balance:
- Stay competitive with the market (ideally near the average, or lower if margin allows)
- Never go below our cost
- Respond with ONLY the number, e.g. 19.99 — no dollar sign, no words.
"""
    result = llm.invoke(prompt)
    match = re.search(r"[\d.]+", result.content)
    state["suggested_price"] = float(match.group()) if match else shopify_data["price"]
    return state


def apply_price(state: PricingState) -> PricingState:
    info = state["pricing_info"]
    shopify_data = state["shopify_data"]

    if not info or not shopify_data or state["suggested_price"] is None:
        state["final_price"] = None
        return state

    # HARD SAFETY FLOOR: never below our minimum acceptable margin, no matter
    # what the LLM suggests. Enforced in code, not left to the prompt.
    floor_price = round(info["our_cost"] * (1 + info["min_margin_percent"] / 100), 2)
    final_price = max(state["suggested_price"], floor_price)
    final_price = round(final_price, 2)

    reason = "AI-suggested price based on competitor analysis"
    if final_price == floor_price and state["suggested_price"] < floor_price:
        reason = "AI suggestion was below minimum margin — clamped to price floor"

    # Write the new price back to the REAL Shopify product
    update_shopify_price(shopify_data["variant_id"], final_price)
    save_price_history(info["sku"], final_price, reason)

    state["final_price"] = final_price
    return state


def respond(state: PricingState) -> PricingState:
    info = state["pricing_info"]
    shopify_data = state["shopify_data"]

    if not info:
        state["summary"] = f"No pricing info found for SKU {state['sku']}."
        return state

    if not shopify_data:
        state["summary"] = (
            f"Couldn't find '{info['product_name']}' in Shopify. "
            f"Make sure a product with this exact title exists in your store."
        )
        return state

    if state["final_price"] is None:
        state["summary"] = f"No competitor data available for {info['product_name']}; price unchanged."
        return state

    state["summary"] = (
        f"{info['product_name']}: price updated from ${shopify_data['price']} to ${state['final_price']} "
        f"in Shopify (competitor average: ${state['competitor_data']['average']})."
    )
    return state


def build_pricing_graph():
    graph = StateGraph(PricingState)

    graph.add_node("get_our_price", get_our_price)
    graph.add_node("fetch_competitor_prices", fetch_competitor_prices)
    graph.add_node("decide", decide)
    graph.add_node("apply_price", apply_price)
    graph.add_node("respond", respond)

    graph.set_entry_point("get_our_price")
    graph.add_edge("get_our_price", "fetch_competitor_prices")
    graph.add_edge("fetch_competitor_prices", "decide")
    graph.add_edge("decide", "apply_price")
    graph.add_edge("apply_price", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


pricing_agent = build_pricing_graph()


def run_pricing_agent(sku: str) -> str:
    result = pricing_agent.invoke({
        "sku": sku,
        "pricing_info": None,
        "shopify_data": None,
        "competitor_data": None,
        "suggested_price": None,
        "final_price": None,
        "summary": None,
    })
    return result["summary"]


def run_pricing_check_all() -> list:
    from app.pricing_db import get_all_pricing
    summaries = []
    for item in get_all_pricing():
        summaries.append({
            "sku": item["sku"],
            "product": item["product_name"],
            "summary": run_pricing_agent(item["sku"]),
        })
    return summaries
