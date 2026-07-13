import { useState } from "react";
import SupportPanel from "./components/SupportPanel";
import InventoryPanel from "./components/InventoryPanel";
import PricingPanel from "./components/PricingPanel";
import "./App.css";

const TABS = [
  { id: "support", label: "🎧 Support", component: SupportPanel },
  { id: "inventory", label: "📦 Inventory", component: InventoryPanel },
  { id: "pricing", label: "💲 Pricing", component: PricingPanel },
];

export default function App() {
  const [activeTab, setActiveTab] = useState("support");
  const ActiveComponent = TABS.find((t) => t.id === activeTab).component;

  return (
    <div className="app">
      <header className="app-header">
        <h1>Autonomous E-Commerce Operations Manager</h1>
        <p>Three AI agents — support, inventory, and pricing — running on LangGraph + Groq.</p>
      </header>

      <nav className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="app-main">
        <ActiveComponent />
      </main>
    </div>
  );
}
