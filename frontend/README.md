# Ops Dashboard (Frontend)

A React frontend for the Autonomous E-Commerce Operations Manager backend.
Gives you a tabbed dashboard to interact with all three agents visually instead of using `/docs`.

## Setup

**1. Make sure the backend is running first** (in a separate terminal):
```bash
cd ../support-agent
uvicorn app.main:app --reload
```
It should be running at `http://127.0.0.1:8000`.

**2. Install frontend dependencies:**
```bash
npm install
```

**3. Run the dev server:**
```bash
npm run dev
```

Open the URL it gives you (usually `http://localhost:5173`).

## What you'll see

- **Support tab** — pick a sample order, type a message, and see the agent's decision
- **Inventory tab** — view live stock levels, check individual items or all at once, watch low-stock items get flagged and reordered
- **Pricing tab** — view prices/costs/margins, run a price check, see the agent adjust prices while respecting the safety floor

## Notes

- `src/api.js` has the backend URL hardcoded to `http://127.0.0.1:8000` — change this one line if you ever deploy the backend elsewhere.
- If you see CORS errors in the browser console, make sure your backend's `main.py` has `CORSMiddleware` added (already included if you're using the latest backend version).
