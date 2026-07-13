import { useState, useEffect } from "react";
import { getPricing, checkPricingItem, checkAllPricing } from "../api";

export default function PricingPanel() {
  const [items, setItems] = useState([]);
  const [results, setResults] = useState({});
  const [loadingSku, setLoadingSku] = useState(null);
  const [loadingAll, setLoadingAll] = useState(false);
  const [error, setError] = useState(null);

  async function loadPricing() {
    try {
      const data = await getPricing();
      setItems(data);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadPricing();
  }, []);

  async function handleCheck(sku) {
    setLoadingSku(sku);
    setError(null);
    try {
      const result = await checkPricingItem(sku);
      setResults((prev) => ({ ...prev, [sku]: result.summary }));
      await loadPricing(); // refresh price in case it changed
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
      const data = await checkAllPricing();
      const newResults = {};
      data.forEach((r) => { newResults[r.sku] = r.summary; });
      setResults(newResults);
      await loadPricing();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingAll(false);
    }
  }

  return (
    <div className="panel">
      <h2>💲 Pricing Agent</h2>
      <p className="panel-description">
        Compares our price to competitors and adjusts it — a safety floor in code stops it from
        ever dropping below our minimum profit margin.
      </p>

      <button onClick={handleCheckAll} disabled={loadingAll} className="check-all-btn">
        {loadingAll ? "Checking all prices..." : "Run check on all prices"}
      </button>

      {error && <div className="error-box">⚠️ {error}</div>}

      <div className="item-grid">
        {items.map((item) => {
          const minPrice = (item.our_cost * (1 + item.min_margin_percent / 100)).toFixed(2);
          return (
            <div key={item.sku} className="item-card">
              <div className="item-header">
                <strong>{item.product_name}</strong>
                <span className="sku-tag">{item.sku}</span>
              </div>
              <div className="item-stats">
                <span>Price: ${item.our_price.toFixed(2)}</span>
                <span>Cost: ${item.our_cost.toFixed(2)}</span>
              </div>
              <div className="item-stats">
                <span>Min margin: {item.min_margin_percent}%</span>
                <span>Floor price: ${minPrice}</span>
              </div>
              <button
                onClick={() => handleCheck(item.sku)}
                disabled={loadingSku === item.sku}
              >
                {loadingSku === item.sku ? "Checking..." : "Check this price"}
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
