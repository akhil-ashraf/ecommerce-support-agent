import { useState, useEffect } from "react";
import { getInventory, checkInventoryItem, checkAllInventory } from "../api";

export default function InventoryPanel() {
  const [items, setItems] = useState([]);
  const [results, setResults] = useState({});
  const [loadingSku, setLoadingSku] = useState(null);
  const [loadingAll, setLoadingAll] = useState(false);
  const [error, setError] = useState(null);

  async function loadInventory() {
    try {
      const data = await getInventory();
      setItems(data);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadInventory();
  }, []);

  async function handleCheck(sku) {
    setLoadingSku(sku);
    setError(null);
    try {
      const result = await checkInventoryItem(sku);
      setResults((prev) => ({ ...prev, [sku]: result.summary }));
      await loadInventory(); // refresh stock counts in case a reorder happened
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingSku(null);
    }
  }

  async function handleCheckAll() {
    setLoadingAll(true);
    setError(null);
    try {
      const data = await checkAllInventory();
      const newResults = {};
      data.forEach((r) => { newResults[r.sku] = r.summary; });
      setResults(newResults);
      await loadInventory();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingAll(false);
    }
  }

  return (
    <div className="panel">
      <h2>📦 Inventory Agent</h2>
      <p className="panel-description">
        Watches stock levels and automatically drafts a purchase order when an item runs low.
      </p>

      <button onClick={handleCheckAll} disabled={loadingAll} className="check-all-btn">
        {loadingAll ? "Checking all items..." : "Run check on all items"}
      </button>

      {error && <div className="error-box">⚠️ {error}</div>}

      <div className="item-grid">
        {items.map((item) => {
          const isLow = item.stock_count < item.reorder_threshold;
          return (
            <div key={item.sku} className={`item-card ${isLow ? "low-stock" : ""}`}>
              <div className="item-header">
                <strong>{item.product_name}</strong>
                <span className="sku-tag">{item.sku}</span>
              </div>
              <div className="item-stats">
                <span>Stock: {item.stock_count}</span>
                <span>Threshold: {item.reorder_threshold}</span>
              </div>
              {isLow && <div className="low-badge">Low stock</div>}
              <button
                onClick={() => handleCheck(item.sku)}
                disabled={loadingSku === item.sku}
              >
                {loadingSku === item.sku ? "Checking..." : "Check this item"}
              </button>
              {results[item.sku] && (
                <div className="result-box small">{results[item.sku]}</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
