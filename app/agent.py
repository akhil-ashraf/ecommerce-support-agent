"""
This is the AI agent itself, built with LangGraph.

Think of LangGraph as a flowchart: each "node" is a step, and the agent
moves through steps based on the data it finds. Our flow is:

    1. look_up_order      -> find the order in our fake database
    2. check_tracking     -> ask the (fake) shipping API for its status
    3. decide             -> ask the LLM: should we approve/reject the refund?
    4. respond             -> return a final answer to the customer

We use Groq (free, fast) instead of OpenAI so this costs nothing to run.
Get a free key at: https://console.groq.com/keys
"""

import os
from dotenv import load_dotenv

load_dotenv()
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from app.database import get_order, mark_refunded
from app.mock_tracking import get_tracking_status


# ---- 1. Define the "state" that flows through the graph ----
class SupportState(TypedDict):
    order_id: str
    customer_message: str
    order: Optional[dict]
    tracking: Optional[dict]
    decision: Optional[str]
    final_response: Optional[str]


# ---- 2. Set up the LLM (the agent's "brain") ----
llm = ChatGroq(
    model="llama-3.1-8b-instant",   # fast + free tier on Groq
    temperature=0,
    api_key=os.environ.get("GROQ_API_KEY"),
)


# ---- 3. Define each node (step) in the flow ----

def look_up_order(state: SupportState) -> SupportState:
    order = get_order(state["order_id"])
    state["order"] = order
    return state


def check_tracking(state: SupportState) -> SupportState:
    if not state["order"]:
        state["tracking"] = None
        return state
    tracking = get_tracking_status(state["order"]["tracking_number"])
    state["tracking"] = tracking
    return state


def decide(state: SupportState) -> SupportState:
    order = state["order"]

    if not order:
        state["decision"] = "no_order_found"
        return state

    if order["refunded"]:
        state["decision"] = "already_refunded"
        return state

    # Build a short prompt for the LLM with all the facts it needs
    prompt = f"""
You are a customer support agent for an online store.

Customer message: "{state['customer_message']}"

Order details:
- Product: {order['product']}
- Order status: {order['status']}
- Shipping status: {state['tracking']['status']}
- ETA (days): {state['tracking']['eta_days']}

Decide ONE action only, respond with exactly one word:
- "approve_refund" if the shipment is delayed or the customer has a valid complaint
- "reject_refund" if the order was already delivered on time and there's no valid issue
- "provide_update" if the customer just wants tracking info, not a refund
"""
    result = llm.invoke(prompt)
    decision_text = result.content.strip().lower()

    if "approve" in decision_text:
        state["decision"] = "approve_refund"
    elif "reject" in decision_text:
        state["decision"] = "reject_refund"
    else:
        state["decision"] = "provide_update"

    return state


def respond(state: SupportState) -> SupportState:
    decision = state["decision"]
    order = state["order"]

    if decision == "no_order_found":
        state["final_response"] = "I couldn't find that order. Could you double check the order ID?"
    elif decision == "already_refunded":
        state["final_response"] = "This order has already been refunded. Let me know if there's anything else!"
    elif decision == "approve_refund":
        mark_refunded(order["order_id"])
        state["final_response"] = (
            f"I'm sorry for the delay with your {order['product']}. "
            f"I've approved a full refund for order {order['order_id']}."
        )
    elif decision == "reject_refund":
        state["final_response"] = (
            f"Your {order['product']} was delivered on time, so a refund isn't applicable here. "
            f"Let me know if something arrived damaged, though!"
        )
    else:  # provide_update
        state["final_response"] = (
            f"Your {order['product']} is currently '{state['tracking']['status']}', "
            f"last seen at {state['tracking']['location']}."
        )

    return state


# ---- 4. Wire the nodes together into a graph ----
def build_graph():
    graph = StateGraph(SupportState)

    graph.add_node("look_up_order", look_up_order)
    graph.add_node("check_tracking", check_tracking)
    graph.add_node("decide", decide)
    graph.add_node("respond", respond)

    graph.set_entry_point("look_up_order")
    graph.add_edge("look_up_order", "check_tracking")
    graph.add_edge("check_tracking", "decide")
    graph.add_edge("decide", "respond")
    graph.add_edge("respond", END)

    return graph.compile()


support_agent = build_graph()


def run_support_agent(order_id: str, customer_message: str) -> str:
    result = support_agent.invoke({
        "order_id": order_id,
        "customer_message": customer_message,
        "order": None,
        "tracking": None,
        "decision": None,
        "final_response": None,
    })
    return result["final_response"]
