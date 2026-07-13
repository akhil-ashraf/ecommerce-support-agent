# 🤖 Autonomous E-Commerce Operations Manager

A multi-agent system that automates three core e-commerce operations — customer support, inventory restocking, and competitive pricing — using **LangGraph** for agent orchestration and **Groq** for fast, free LLM inference.

Each agent follows the same design: gather real data → let the LLM reason over it → act on the decision → report back in plain English. No hardcoded if/else logic pretending to be "AI" — each agent genuinely uses an LLM to make a judgment call, with code-level guardrails where money is on the line.

## Why this project

Most beginner AI-agent demos are single-step chatbots. This project instead models a **realistic operations pipeline**: multiple independent agents, each with its own data source, decision logic, and side effects (updating a database, "sending" an email, adjusting a price) — the same shape as a production agent system, just running on free tools instead of paid infrastructure.

## The three agents

| Agent | What it does | Key engineering detail |
|---|---|---|
| 🎧 **Support Agent** | Reads an order + live shipping status, then approves/rejects refunds or gives a status update | Multi-step reasoning: won't approve a refund just because the customer asked — checks actual delivery status first |
| 📦 **Inventory Agent** | Monitors stock levels and automatically drafts a purchase order to the correct supplier when stock drops below threshold | Fully automated restocking loop — can run on a schedule with zero human input |
| 💲 **Pricing Agent** | Compares our price to competitor prices and adjusts dynamically | **Hard safety floor in code**: the LLM can suggest any price, but a non-negotiable guardrail (`apply_price` in `pricing_agent.py`) mathematically prevents it from ever pricing below our minimum profit margin — the AI proposes, the code disposes |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Support Agent   │     │ Inventory Agent  │     │  Pricing Agent  │
│                  │     │                  │     │                 │
│ order → tracking │     │ stock → threshold│     │ price → compare │
│   → LLM decide   │     │   → LLM decide   │     │  → LLM decide   │
│   → respond      │     │   → purchase PO  │     │  → safety floor │
└────────┬─────────┘     └────────┬─────────┘     └────────┬────────┘
         │                        │                         │
         └────────────────────────┴─────────────────────────┘
                                   │
                          FastAPI (single backend)
                                   │
                          SQLite (shared local DB)
```

Each agent is a small [LangGraph](https://github.com/langchain-ai/langgraph) state machine, exposed as its own FastAPI route, sharing one SQLite database that stands in for a real store's data.

## Tech stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — orchestrates each agent's multi-step reasoning as an explicit state graph (not just a single prompt call)
- **[Groq](https://console.groq.com)** — free, extremely fast LLM inference (`llama-3.1-8b-instant`)
- **FastAPI** — exposes each agent as a REST endpoint
- **SQLite** — lightweight local database standing in for a real store's order/inventory/pricing data
- **python-dotenv** — keeps API keys out of source control

## Project structure

```
support-agent/
├── app/
│   ├── main.py              # FastAPI app — all routes live here
│   │
│   ├── agent.py             # Support Agent (LangGraph state machine)
│   ├── database.py          # Order data (SQLite)
│   ├── mock_tracking.py     # Simulated shipping-carrier API
│   │
│   ├── inventory_agent.py   # Inventory Agent (LangGraph state machine)
│   ├── inventory_db.py      # Stock levels + purchase order history (SQLite)
│   ├── mock_supplier.py     # Simulated supplier ordering API
│   │
│   ├── pricing_agent.py     # Pricing Agent (LangGraph state machine + safety guardrail)
│   ├── pricing_db.py        # Prices, costs, margin rules + price history (SQLite)
│   └── mock_competitor.py   # Simulated competitor pricing data
│
├── requirements.txt
└── .gitignore
```

**A note on the `mock_*.py` files:** real integrations here (a live shipping API, a real supplier email, live competitor scraping) typically require paid accounts or business verification. These files simulate that external data with the same interface a real integration would have — so swapping in a real API later (e.g. Shippo, SendGrid, a scraping service) means changing one function, not the agent logic.

## Running it locally

**1. Get a free Groq API key** — [console.groq.com/keys](https://console.groq.com/keys) (no card required)

**2. Install dependencies**
```bash
cd support-agent
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**3. Add your key** — create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

**4. Run the server**
```bash
uvicorn app.main:app --reload
```

**5. Open the interactive docs** at `http://127.0.0.1:8000/docs` and try any endpoint below.

## API reference

### Support Agent
```
POST /support
{
  "order_id": "ORD1003",
  "message": "My order is really late, I want a refund"
}
```
Sample order IDs: `ORD1001` (in transit), `ORD1002` (delivered on time), `ORD1003` (delayed → approves refund), `ORD1004` (already refunded).

### Inventory Agent
```
GET  /inventory                     # view all stock levels
POST /inventory/check/{sku}         # check one item, reorder if needed
POST /inventory/check-all           # run across all items (e.g. daily cron)
```
`SKU003` is seeded below its reorder threshold — a good one to test first.

### Pricing Agent
```
GET  /pricing                       # view current prices, costs, margins
POST /pricing/check/{sku}           # compare to competitors, adjust price
POST /pricing/check-all             # run across all items
```

## Design decisions worth highlighting

- **LLMs make judgment calls, not final unchecked decisions.** The Pricing Agent is the clearest example: the LLM can suggest whatever it wants, but `apply_price()` clamps the result against a hard-coded minimum margin before it ever touches the database.
- **Each agent is a real multi-step graph, not a single prompt.** The Support Agent won't just take the customer's word for it — it independently checks shipping status before deciding.
- **Mocked externals, real logic.** The parts that cost money (shipping APIs, supplier integrations, competitor scraping) are simulated; the agent orchestration, state management, and decision logic are fully real and swappable to production APIs later.

## Roadmap

- [ ] Replace `mock_tracking.py` / `mock_supplier.py` / `mock_competitor.py` with real free-tier APIs
- [ ] Replace SQLite with a Shopify Dev Store via the Shopify Admin API
- [ ] Add a scheduler (GitHub Actions cron) to run inventory/pricing checks daily without manual triggering
- [ ] Deploy to Render/Railway free tier for a live public demo link