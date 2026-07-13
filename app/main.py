"""
This turns your agent into a small web API using FastAPI.
Run it, then send it a customer message + order ID, and it replies.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from app.database import init_db
from app.agent import run_support_agent

app = FastAPI(title="Support Agent API")

# Create the fake database + sample orders the first time this starts
init_db()


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
