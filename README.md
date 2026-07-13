# Support Agent 

A working AI customer-support agent built with **FastAPI + LangGraph + Groq (free LLM API)**.
It reads a fake order database, checks a fake shipping tracker, and decides whether to
approve a refund, reject it, or just give a status update — all through an AI agent flow.

This is the first piece of a bigger "Autonomous E-Commerce Operations Manager" project.
Inventory Agent and Pricing Agent can be added later using the same pattern.

## What's inside

```
support-agent/
├── app/
│   ├── main.py          <- FastAPI server (the API you'll call)
│   ├── agent.py         <- The LangGraph agent (the "brain")
│   ├── database.py      <- Fake SQLite order database
│   └── mock_tracking.py <- Fake shipping tracker (stands in for Shippo/EasyPost)
├── requirements.txt
└── README.md
```

## Step 1 — Get a free Groq API key

1. Go to https://console.groq.com/keys
2. Sign up (free, no card needed)
3. Click "Create API Key" and copy it

## Step 2 — Install dependencies

```bash
cd support-agent
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3 — Set your API key

```bash
export GROQ_API_KEY="your_key_here"        # Mac/Linux
set GROQ_API_KEY=your_key_here             # Windows cmd
```

## Step 4 — Run the server

```bash
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000/docs — FastAPI gives you a free interactive UI to test the API.

## Step 5 — Try it

Send a POST request to `/support` with a body like:

```json
{
  "order_id": "ORD1003",
  "message": "My order is really late, I want a refund"
}
```

Try these sample order IDs (already seeded in the fake database):
- `ORD1001` — shipped, in transit
- `ORD1002` — delivered on time
- `ORD1003` — delayed (should get approved for refund)
- `ORD1004` — already refunded

## How the agent thinks (LangGraph flow)

```
look_up_order -> check_tracking -> decide -> respond
```

1. **look_up_order** — finds the order in the database
2. **check_tracking** — asks the (fake) shipping API for its live status
3. **decide** — sends order + tracking facts to the LLM, which picks one action
4. **respond** — turns that decision into a human-friendly reply, and updates the database if a refund was approved

## Next steps (once this works)

- Swap `mock_tracking.py` for a real API like Shippo's free developer tier
- Swap the SQLite database for a real Shopify Dev Store (also free) using Shopify's Admin API
- Add an Inventory Agent using the exact same LangGraph pattern, watching stock levels instead of orders
- Deploy free on Render.com or Railway's free tier so you have a live demo link for your resume/portfolio
