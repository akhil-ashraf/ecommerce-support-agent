import { useState } from "react";
import { sendSupportRequest } from "../api";

const SAMPLE_ORDERS = ["ORD1001", "ORD1002", "ORD1003", "ORD1004"];

export default function SupportPanel() {
  const [orderId, setOrderId] = useState("ORD1003");
  const [message, setMessage] = useState("My order is really late, I want a refund");
  const [reply, setReply] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReply(null);
    try {
      const result = await sendSupportRequest(orderId, message);
      setReply(result.reply);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <h2>🎧 Support Agent</h2>
      <p className="panel-description">
        Ask about an order — the agent checks live shipping status before deciding on a refund.
      </p>

      <form onSubmit={handleSubmit} className="panel-form">
        <label>
          Order ID
          <select value={orderId} onChange={(e) => setOrderId(e.target.value)}>
            {SAMPLE_ORDERS.map((id) => (
              <option key={id} value={id}>{id}</option>
            ))}
          </select>
        </label>

        <label>
          Customer message
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Thinking..." : "Send to Support Agent"}
        </button>
      </form>

      {error && <div className="error-box">⚠️ {error}</div>}
      {reply && (
        <div className="result-box">
          <strong>Agent reply:</strong>
          <p>{reply}</p>
        </div>
      )}
    </div>
  );
}
