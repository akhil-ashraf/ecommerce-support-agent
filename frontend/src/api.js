// This file centralizes all calls to your FastAPI backend.
// If you deploy the backend somewhere later, you only need to change this one line.
const API_BASE = "http://127.0.0.1:8000";

async function apiCall(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

// ---- Support Agent ----
export function sendSupportRequest(orderId, message) {
  return apiCall("/support", {
    method: "POST",
    body: JSON.stringify({ order_id: orderId, message }),
  });
}

// ---- Inventory Agent ----
export function getInventory() {
  return apiCall("/inventory");
}
export function checkInventoryItem(sku) {
  return apiCall(`/inventory/check/${sku}`, { method: "POST" });
}
export function checkAllInventory() {
  return apiCall("/inventory/check-all", { method: "POST" });
}

// ---- Pricing Agent ----
export function getPricing() {
  return apiCall("/pricing");
}
export function checkPricingItem(sku) {
  return apiCall(`/pricing/check/${sku}`, { method: "POST" });
}
export function checkAllPricing() {
  return apiCall("/pricing/check-all", { method: "POST" });
}
