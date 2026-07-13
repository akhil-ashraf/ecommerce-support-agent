# 🤖 Autonomous E-Commerce Operations Manager

A multi-agent system that automates three core e-commerce operations — customer support, inventory restocking, and competitive pricing — using **LangGraph** for agent orchestration, **Groq** for fast free LLM inference, and a **real Shopify Dev Store** as the live commerce backend.

**🔗 Live demo:** [autonomous-ecommerce-manager.vercel.app](https://autonomous-ecommerce-manager.vercel.app)
*(Backend runs on Render's free tier and may take ~30-50s to wake up on the first request after inactivity.)*

Each agent follows the same design: gather real data → let the LLM reason over it → act on the decision → write the result back to a live system → report back in plain English. No hardcoded if/else logic pretending to be "AI" — each agent genuinely uses an LLM to make a judgment call, with code-level guardrails where money is on the line.

## Why this project

Most beginner AI-agent demos are single-step chatbots against fake data. This project goes a step further on both fronts: it's a **realistic multi-agent operations pipeline** (each agent has its own data source, decision logic, and side effects), and it's wired up to **a real e-commerce platform** — the Inventory and Pricing agents read live stock and price data from an actual Shopify store and write real changes back to it, the same way a production integration would.

## The three agents

| Agent | What it does | Key engineering detail |
|---|---|---|
| 🎧 **Support Agent** | Reads an order + live shipping status, then approves/rejects refunds or gives a status update | Multi-step reasoning: won't approve a refund just because the customer asked — checks actual delivery status first |
| 📦 **Inventory Agent** | Monitors **real Shopify stock levels** and automatically restocks (writes the new quantity back to Shopify) when stock drops below threshold | Live read + live write against Shopify's Admin API — not a local fake number |
| 💲 **Pricing Agent** | Compares our **real Shopify price** to competitor prices and adjusts it, writing the new price back to the live store | **Hard safety floor in code**: the LLM can suggest any price, but a non-negotiable guardrail (`apply_price` in `pricing_agent.py`) mathematically prevents it from ever pricing below our minimum profit margin — the AI proposes, the code disposes |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Support Agent   │     │ Inventory Agent  │     │  Pricing Agent  │
│                  │     │                  │     │                 │
│ order → tracking │     │ stock → threshold│     │ price → compare │
│   → LLM decide   │     │   → LLM decide   │     │  → LLM decide   │
│   → respond      │     │  → write stock   │     │  → write price  │
└────────┬─────────┘     └────────┬─────────┘     └────────┬────────┘
         │                        │                         │
         │               ┌────────┴────────┐                │
         │               │  Shopify Admin  │────────────────┘
         │               │  API (live)     │
         │               └─────────────────┘
         │                        │
         └────────────────────────┴─────────────────────────┘
                                   │
                          FastAPI (single backend)
                                   │
                    SQLite (business rules: thresholds,
                      supplier info, cost, margins)
                                   │
                     React frontend (tabbed dashboard)
```

Each agent is a small [LangGraph](https://github.com/langchain-ai/langgraph) state machine, exposed as its own FastAPI route. Local SQLite holds business rules (reorder thresholds, supplier contacts, cost, minimum margin); live stock and price numbers are read from — and written back to — a real Shopify Dev Store via the Admin API.

## Tech stack

**Backend**
- **[LangGraph](https://github.com/langchain-ai/langgraph)** — orchestrates each agent's multi-step reasoning as an explicit state graph (not just a single prompt call)
- **[Groq](https://console.groq.com)** — free, extremely fast LLM inference (`llama-3.1-8b-instant`)
- **FastAPI** — exposes each agent as a REST endpoint
- **Shopify Admin API** — real product, inventory, and pricing data on a free Shopify Dev Store
- **SQLite** — local business rules (thresholds, supplier info, cost, margin) and order data
- **python-dotenv** — keeps API keys out of source control

**Frontend**
- **React + Vite** — tabbed dashboard for all three agents
- Plain `fetch` calls to the FastAPI backend, no state library needed for this scope

**Deployment**
- **Render** (free tier) — hosts the FastAPI backend
- **Vercel** (free tier) — hosts the React frontend

## Project structure

```
support-agent/
├── app/
│   ├── main.py              # FastAPI app — all routes + CORS live here
│   │
│   ├── agent.py             # Support Agent (LangGraph state machine)
│   ├── database.py          # Order data (SQLite)
│   ├── mock_tracking.py     # Simulated shipping-carrier API
│   │
│   ├── inventory_agent.py   # Inventory Agent — reads/writes REAL Shopify stock
│   ├── inventory_db.py      # Reorder thresholds, supplier info (SQLite)
│   ├── mock_supplier.py     # Simulated supplier ordering API
│   │
│   ├── pricing_agent.py     # Pricing Agent — reads/writes REAL Shopify price
│   ├── pricing_db.py        # Cost + minimum margin rules (SQLite)
│   ├── mock_competitor.py   # Simulated competitor pricing data
│   │
│   └── shopify_client.py    # Shopify Admin API wrapper (products, inventory, pricing)
│
├── frontend/                # React + Vite dashboard
│   └── src/
│       ├── api.js           # Calls to the FastAPI backend
│       ├── App.jsx          # Tab navigation
│       └── components/      # SupportPanel, InventoryPanel, PricingPanel
│
├── runtime.txt              # Pins Python version for Render deployment
├── requirements.txt
└── .gitignore
```

**A note on the `mock_*.py` files:** shipping tracking, supplier emailing, and competitor price scraping still require paid accounts or business verification, so those stay simulated with the same interface a real integration would have. Inventory and pricing, however, are **fully real** — connected to an actual Shopify store via the Admin API.

## Running it locally

**1. Get a free Groq API key** — [console.groq.com/keys](https://console.groq.com/keys) (no card required)

**2. Set up a free Shopify Dev Store**
- Create a free account at [partners.shopify.com](https://partners.shopify.com)
- Create a **Development Store**
- Under Settings → Apps and sales channels → Develop apps, create a custom app and enable `read_products`, `write_products`, `read_inventory`, `write_inventory` scopes
- Install the app and copy the Admin API access token

**3. Install backend dependencies**
```bash
cd support-agent
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**4. Add your keys** — create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_key_here
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_shopify_token_here
```

**5. Run the backend**
```bash
uvicorn app.main:app --reload
```

**6. Run the frontend** (separate terminal)
```bash
cd frontend
npm install
npm run dev
```

Open the frontend URL it gives you (usually `http://localhost:5173`), or use `http://127.0.0.1:8000/docs` for the raw API.

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
GET  /inventory                     # view local business rules per SKU
POST /inventory/check/{sku}         # check REAL Shopify stock, reorder if needed
POST /inventory/check-all           # run across all items (e.g. daily cron)
```
Product titles in Shopify must match the `product_name` values seeded in `inventory_db.py` exactly.

### Pricing Agent
```
GET  /pricing                       # view local cost/margin rules per SKU
POST /pricing/check/{sku}           # compare REAL Shopify price to competitors, adjust it
POST /pricing/check-all             # run across all items
```

## Design decisions worth highlighting

- **LLMs make judgment calls, not final unchecked decisions.** The Pricing Agent is the clearest example: the LLM can suggest whatever it wants, but `apply_price()` clamps the result against a hard-coded minimum margin before it's ever written to Shopify.
- **Own business rules stay separate from the external platform's data.** Thresholds, supplier contacts, cost, and margin rules live in a local database the business controls; only the live, fast-changing numbers (stock, price) are read from and written to Shopify. This mirrors how real integrations are architected — you don't let an external platform own your business logic.
- **Each agent is a real multi-step graph, not a single prompt.** The Support Agent won't just take the customer's word for it — it independently checks shipping status before deciding.
- **Mocked where it needs to be, real where it counts.** Shipping tracking, supplier emailing, and competitor scraping stay simulated since they require paid accounts; inventory and pricing are fully live against a real commerce platform.

## Roadmap

- [x] Connect Inventory and Pricing agents to a real Shopify Dev Store
- [x] Deploy backend (Render) and frontend (Vercel) live
- [ ] Replace `mock_tracking.py`, `mock_supplier.py`, `mock_competitor.py` with real free-tier APIs
- [ ] Add a scheduler (GitHub Actions cron) to run inventory/pricing checks daily without manual triggering
- [ ] Sync Support Agent against real Shopify orders instead of local sample data