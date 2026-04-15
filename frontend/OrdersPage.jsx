import { useState, useEffect } from "react";
import { useApp } from "./App";
import { orderApi } from "./api";

const STATUS_META = {
  pending:    { color: "#d97706", bg: "#fef3c7", label: "Pending",    icon: "⏳" },
  processing: { color: "#2563eb", bg: "#eff6ff", label: "Processing", icon: "⚙️" },
  shipped:    { color: "#0891b2", bg: "#e0f7fa", label: "Shipped",    icon: "🚚" },
  delivered:  { color: "#16a34a", bg: "#f0fdf4", label: "Delivered",  icon: "✓"  },
  failed:     { color: "#dc2626", bg: "#fef2f2", label: "Failed",     icon: "✕"  },
  cancelled:  { color: "#7c3aed", bg: "#f5f3ff", label: "Cancelled",  icon: "✗"  },
};

const PIPELINE = ["pending","processing","shipped","delivered"];

// Demo orders shown when no backend
const DEMO_ORDERS = [
  { id: "ORD-7A3F", items: [{ name: "Wireless Headphones", qty: 1, price: 2499 }], total: 2578, status: "delivered", created: "2024-03-01" },
  { id: "ORD-2B9C", items: [{ name: "Running Shoes", qty: 2, price: 1899 }, { name: "Yoga Mat", qty: 1, price: 699 }], total: 5097, status: "shipped", created: "2024-03-10" },
  { id: "ORD-5D1E", items: [{ name: "Coffee Maker", qty: 1, price: 3299 }], total: 3378, status: "processing", created: "2024-03-14" },
];

export default function OrdersPage() {
  const { user, nav } = useApp();
  const [orders, setOrders]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    if (!user) { nav("auth"); return; }
    const load = async () => {
      try {
        // GET /api/orders?userId=... → Order Service :3002
        const data = await orderApi.getOrders(user.id, user.token);
        setOrders(Array.isArray(data) ? data : data.orders || []);
      } catch {
        setOrders(DEMO_ORDERS);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
      <div style={{ textAlign: "center", color: "#9c9890" }}>
        <div style={{ fontSize: "32px", marginBottom: "12px", animation: "spin 1s linear infinite", display: "inline-block" }}>⟳</div>
        <div>Loading your orders…</div>
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
      </div>
    </div>
  );

  if (orders.length === 0) return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "60vh", gap: "16px" }}>
      <div style={{ fontSize: "64px" }}>📦</div>
      <h2 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: "22px" }}>No orders yet</h2>
      <p style={{ color: "#9c9890", fontSize: "14px" }}>Your order history will appear here once you shop.</p>
      <button onClick={() => nav("store")} style={{ background: "#1a1a1a", color: "#fff", border: "none", borderRadius: "10px", padding: "12px 28px", fontSize: "14px", fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>Start Shopping →</button>
    </div>
  );

  return (
    <div style={{ maxWidth: "960px", margin: "0 auto", padding: "40px 48px" }}>
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 800, fontSize: "28px", marginBottom: "6px" }}>My Orders</h1>
        <p style={{ fontSize: "14px", color: "#9c9890" }}>{orders.length} order{orders.length !== 1 ? "s" : ""} · via Order Service :3002</p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {orders.map(order => {
          const meta = STATUS_META[order.status] || STATUS_META.pending;
          const isOpen = selected === order.id;
          const stepIdx = PIPELINE.indexOf(order.status);

          return (
            <div key={order.id} style={{ background: "#fff", borderRadius: "16px", border: "1px solid #ede9e2", overflow: "hidden", transition: "box-shadow 0.2s", boxShadow: isOpen ? "0 4px 20px rgba(0,0,0,0.06)" : "none" }}>
              {/* Header row */}
              <div onClick={() => setSelected(isOpen ? null : order.id)} style={{ padding: "20px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer", gap: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                  <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: meta.bg, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px", flexShrink: 0 }}>{meta.icon}</div>
                  <div>
                    <div style={{ fontSize: "14px", fontWeight: 700, marginBottom: "3px", color: "#c8a96e" }}>{order.id}</div>
                    <div style={{ fontSize: "13px", color: "#5a5550" }}>
                      {order.items?.length} item{order.items?.length !== 1 ? "s" : ""} · {order.created}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
                  <span style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: "18px" }}>₹{order.total?.toLocaleString()}</span>
                  <span style={{ fontSize: "12px", fontWeight: 700, padding: "5px 12px", borderRadius: "100px", background: meta.bg, color: meta.color, letterSpacing: "0.04em" }}>{meta.label}</span>
                  <span style={{ color: "#b0ada6", fontSize: "16px", transform: isOpen ? "rotate(180deg)" : "none", display: "inline-block", transition: "transform 0.2s" }}>▾</span>
                </div>
              </div>

              {/* Expanded detail */}
              {isOpen && (
                <div style={{ padding: "0 24px 24px", borderTop: "1px solid #f5f3ef" }}>
                  {/* Pipeline bar */}
                  {order.status !== "failed" && order.status !== "cancelled" && (
                    <div style={{ display: "flex", alignItems: "center", gap: "0", margin: "20px 0 24px", overflow: "hidden" }}>
                      {PIPELINE.map((step, i) => {
                        const done = stepIdx >= i;
                        const active = stepIdx === i;
                        return (
                          <div key={step} style={{ display: "flex", alignItems: "center", flex: 1 }}>
                            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
                              <div style={{ width: "28px", height: "28px", borderRadius: "50%", background: done ? "#1a1a1a" : "#f0ede8", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", color: done ? "#fff" : "#b0ada6", border: active ? "2px solid #c8a96e" : "none", transition: "all 0.3s" }}>
                                {done && !active ? "✓" : i + 1}
                              </div>
                              <span style={{ fontSize: "11px", color: done ? "#1a1a1a" : "#b0ada6", fontWeight: done ? 600 : 400, textTransform: "capitalize", whiteSpace: "nowrap" }}>{step}</span>
                            </div>
                            {i < PIPELINE.length - 1 && (
                              <div style={{ flex: 1, height: "2px", background: stepIdx > i ? "#1a1a1a" : "#f0ede8", margin: "0 4px", marginBottom: "22px", transition: "background 0.3s" }} />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Items */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {order.items?.map((item, i) => (
                      <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", background: "#fafaf8", borderRadius: "10px", fontSize: "14px" }}>
                        <span style={{ fontWeight: 500 }}>{item.name}</span>
                        <div style={{ display: "flex", gap: "20px", color: "#9c9890" }}>
                          <span>× {item.qty}</span>
                          <span style={{ fontWeight: 600, color: "#1a1a1a" }}>₹{(item.price * item.qty).toLocaleString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: "16px", paddingTop: "14px", borderTop: "1px solid #f0ede8" }}>
                    <span style={{ fontSize: "13px", color: "#9c9890" }}>Total paid</span>
                    <span style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: "17px", color: "#c8a96e" }}>₹{order.total?.toLocaleString()}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
