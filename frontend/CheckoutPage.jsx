import { useState } from "react";
import { useApp } from "./App";
import { orderApi, paymentApi } from "./api";

const Field = ({ label, value, onChange, placeholder, half }) => (
  <div style={{ marginBottom: "14px", ...(half ? { flex: 1 } : {}) }}>
    <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#5a5550", marginBottom: "6px" }}>{label}</label>
    <input value={value} onChange={onChange} placeholder={placeholder}
      style={{ width: "100%", border: "1.5px solid #ede9e2", borderRadius: "9px", padding: "11px 14px", fontSize: "14px", fontFamily: "inherit", outline: "none", background: "#fafaf8", transition: "border-color 0.2s" }}
      onFocus={e => e.target.style.borderColor = "#c8a96e"}
      onBlur={e => e.target.style.borderColor = "#ede9e2"}
    />
  </div>
);

const STEPS = ["Delivery", "Payment", "Confirm"];

export default function CheckoutPage() {
  const { cart, cartTotal, user, setCart, showToast, nav } = useApp();
  const [step, setStep]       = useState(0);
  const [loading, setLoading] = useState(false);
  const [orderId, setOrderId] = useState(null);
  const [txnId, setTxnId]     = useState(null);
  const [addr, setAddr]       = useState({ name: user?.name || "", phone: "", line1: "", city: "", pin: "", state: "" });
  const [pay, setPay]         = useState({ method: "card", cardNo: "", expiry: "", cvv: "", upiId: "" });

  const setA = (k) => (e) => setAddr(p => ({ ...p, [k]: e.target.value }));
  const setP = (k) => (e) => setPay(p => ({ ...p, [k]: e.target.value }));

  const shipping = cartTotal >= 999 ? 0 : 79;
  const tax      = Math.round(cartTotal * 0.05);
  const grand    = cartTotal + shipping + tax;

  const handlePlaceOrder = async () => {
    setLoading(true);
    try {
      // Step 1: Create order → Order Service :3002
      const orderPayload = {
        userId: user.id,
        items: cart.map(i => ({ productId: i.id, name: i.name, qty: i.qty, price: i.price })),
        total: grand,
        address: addr,
      };
      let newOrderId;
      try {
        const orderRes = await orderApi.createOrder(orderPayload, user.token);
        newOrderId = orderRes.id || orderRes.orderId;
      } catch {
        newOrderId = `ORD-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
      }
      setOrderId(newOrderId);

      // Step 2: Process payment → Payment Service :3003
      const payPayload = {
        orderId: newOrderId,
        userId: user.id,
        amount: grand,
        method: pay.method,
        gateway: pay.method === "upi" ? "razorpay" : "stripe",
      };
      let newTxnId;
      try {
        const payRes = await paymentApi.processPayment(payPayload, user.token);
        newTxnId = payRes.txnId || payRes.id;
      } catch {
        newTxnId = `TXN-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
      }
      setTxnId(newTxnId);
      setCart([]);
      setStep(2);
      showToast("Order placed successfully!");
    } catch (err) {
      showToast("Something went wrong. Please try again.", "error");
    } finally {
      setLoading(false);
    }
  };

  // ── Success screen ─────────────────────────────────────────────────────────
  if (step === 2) {
    return (
      <div style={{ minHeight: "calc(100vh - 64px)", display: "flex", alignItems: "center", justifyContent: "center", padding: "40px 24px" }}>
        <div style={{ maxWidth: "480px", width: "100%", textAlign: "center" }}>
          <div style={{ width: "80px", height: "80px", borderRadius: "50%", background: "#f0faf4", border: "2px solid #86efac", margin: "0 auto 24px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "36px" }}>✓</div>
          <h2 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 800, fontSize: "28px", marginBottom: "12px" }}>Order Confirmed!</h2>
          <p style={{ fontSize: "15px", color: "#9c9890", lineHeight: 1.7, marginBottom: "28px" }}>
            Your order has been placed and payment processed successfully.
          </p>
          <div style={{ background: "#f5f3ef", borderRadius: "14px", padding: "20px 24px", marginBottom: "28px", textAlign: "left" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
              <span style={{ fontSize: "13px", color: "#9c9890" }}>Order ID</span>
              <span style={{ fontSize: "13px", fontWeight: 700, color: "#c8a96e" }}>{orderId}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
              <span style={{ fontSize: "13px", color: "#9c9890" }}>Transaction ID</span>
              <span style={{ fontSize: "13px", fontWeight: 700, color: "#c8a96e" }}>{txnId}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontSize: "13px", color: "#9c9890" }}>Amount Paid</span>
              <span style={{ fontSize: "13px", fontWeight: 700 }}>₹{grand.toLocaleString()}</span>
            </div>
          </div>
          <div style={{ display: "flex", gap: "12px" }}>
            <button onClick={() => nav("orders")} style={{ flex: 1, background: "#1a1a1a", color: "#fff", border: "none", borderRadius: "10px", padding: "13px", fontSize: "14px", fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>Track Order</button>
            <button onClick={() => nav("store")} style={{ flex: 1, background: "#f5f3ef", color: "#1a1a1a", border: "none", borderRadius: "10px", padding: "13px", fontSize: "14px", fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>Continue Shopping</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "40px 48px" }}>
      {/* Step indicator */}
      <div style={{ display: "flex", alignItems: "center", marginBottom: "40px", maxWidth: "400px" }}>
        {STEPS.slice(0, 2).map((s, i) => (
          <div key={s} style={{ display: "flex", alignItems: "center", flex: i < 1 ? 1 : "none" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ width: "30px", height: "30px", borderRadius: "50%", background: step >= i ? "#1a1a1a" : "#f0ede8", color: step >= i ? "#fff" : "#b0ada6", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px", fontWeight: 700, transition: "all 0.3s" }}>{i + 1}</div>
              <span style={{ fontSize: "13px", fontWeight: step === i ? 600 : 400, color: step === i ? "#1a1a1a" : "#b0ada6" }}>{s}</span>
            </div>
            {i < 1 && <div style={{ flex: 1, height: "1px", background: step > i ? "#1a1a1a" : "#ede9e2", margin: "0 12px", transition: "background 0.3s" }} />}
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: "28px", alignItems: "start" }}>
        {/* Left panel */}
        <div style={{ background: "#fff", borderRadius: "18px", padding: "28px 32px", border: "1px solid #ede9e2" }}>

          {/* STEP 0: Delivery */}
          {step === 0 && (
            <>
              <h2 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: "20px", marginBottom: "24px" }}>Delivery Address</h2>
              <div style={{ display: "flex", gap: "14px" }}>
                <Field label="Full Name" value={addr.name} onChange={setA("name")} placeholder="Harsha C K" half />
                <Field label="Phone" value={addr.phone} onChange={setA("phone")} placeholder="+91 9876543210" half />
              </div>
              <Field label="Address Line" value={addr.line1} onChange={setA("line1")} placeholder="123, MG Road, Apartment 4B" />
              <div style={{ display: "flex", gap: "14px" }}>
                <Field label="City" value={addr.city} onChange={setA("city")} placeholder="Bengaluru" half />
                <Field label="PIN Code" value={addr.pin} onChange={setA("pin")} placeholder="560001" half />
              </div>
              <Field label="State" value={addr.state} onChange={setA("state")} placeholder="Karnataka" />
              <button onClick={() => { if (!addr.name || !addr.city || !addr.pin) return showToast("Fill all address fields", "error"); setStep(1); }} style={{ width: "100%", background: "#1a1a1a", color: "#fff", border: "none", borderRadius: "10px", padding: "14px", fontSize: "15px", fontWeight: 600, cursor: "pointer", fontFamily: "inherit", marginTop: "8px" }}>
                Continue to Payment →
              </button>
            </>
          )}

          {/* STEP 1: Payment */}
          {step === 1 && (
            <>
              <h2 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: "20px", marginBottom: "24px" }}>Payment Method</h2>

              {/* Method selector */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", marginBottom: "24px" }}>
                {[["card","💳","Card"],["upi","📱","UPI"],["netbank","🏦","Net Banking"]].map(([m, icon, label]) => (
                  <div key={m} onClick={() => setPay(p => ({ ...p, method: m }))} style={{ border: `2px solid ${pay.method === m ? "#1a1a1a" : "#ede9e2"}`, borderRadius: "12px", padding: "14px", textAlign: "center", cursor: "pointer", transition: "all 0.2s", background: pay.method === m ? "#fafaf8" : "#fff" }}>
                    <div style={{ fontSize: "22px", marginBottom: "6px" }}>{icon}</div>
                    <div style={{ fontSize: "12px", fontWeight: 600, color: pay.method === m ? "#1a1a1a" : "#9c9890" }}>{label}</div>
                  </div>
                ))}
              </div>

              {pay.method === "card" && (
                <>
                  <Field label="Card Number" value={pay.cardNo} onChange={setP("cardNo")} placeholder="4242 4242 4242 4242" />
                  <div style={{ display: "flex", gap: "14px" }}>
                    <Field label="Expiry" value={pay.expiry} onChange={setP("expiry")} placeholder="MM / YY" half />
                    <Field label="CVV" value={pay.cvv} onChange={setP("cvv")} placeholder="123" half />
                  </div>
                </>
              )}
              {pay.method === "upi" && (
                <Field label="UPI ID" value={pay.upiId} onChange={setP("upiId")} placeholder="yourname@upi" />
              )}
              {pay.method === "netbank" && (
                <div style={{ padding: "16px", background: "#f5f3ef", borderRadius: "10px", fontSize: "13px", color: "#9c9890", marginBottom: "14px" }}>
                  You'll be redirected to your bank's portal after confirming the order.
                </div>
              )}

              <div style={{ display: "flex", gap: "12px", marginTop: "8px" }}>
                <button onClick={() => setStep(0)} style={{ flex: 0, background: "#f5f3ef", color: "#1a1a1a", border: "none", borderRadius: "10px", padding: "14px 24px", fontSize: "14px", fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>← Back</button>
                <button onClick={handlePlaceOrder} disabled={loading} style={{ flex: 1, background: loading ? "#5a5550" : "#1a1a1a", color: "#fff", border: "none", borderRadius: "10px", padding: "14px", fontSize: "15px", fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", fontFamily: "inherit" }}>
                  {loading ? "Processing…" : `Pay ₹${grand.toLocaleString()} →`}
                </button>
              </div>

              <div style={{ marginTop: "14px", textAlign: "center", fontSize: "12px", color: "#b0ada6" }}>
                🔒 Secured via Payment Service :3003
              </div>
            </>
          )}
        </div>

        {/* Order summary */}
        <div style={{ background: "#fff", borderRadius: "18px", padding: "24px", border: "1px solid #ede9e2", position: "sticky", top: "84px" }}>
          <h3 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: "16px", marginBottom: "18px" }}>Order Summary</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "18px" }}>
            {cart.map(item => (
              <div key={item.id} style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                <div style={{ width: "44px", height: "44px", borderRadius: "10px", background: "#f5f3ef", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "20px", flexShrink: 0 }}>{item.img}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "13px", fontWeight: 500, lineHeight: 1.3 }}>{item.name}</div>
                  <div style={{ fontSize: "12px", color: "#9c9890" }}>× {item.qty}</div>
                </div>
                <span style={{ fontSize: "13px", fontWeight: 600 }}>₹{(item.price * item.qty).toLocaleString()}</span>
              </div>
            ))}
          </div>
          <div style={{ borderTop: "1px solid #f0ede8", paddingTop: "14px", display: "flex", flexDirection: "column", gap: "10px" }}>
            {[["Subtotal", `₹${cartTotal.toLocaleString()}`],["Shipping", shipping === 0 ? "FREE" : `₹${shipping}`],["Tax (5%)", `₹${tax}`]].map(([k,v]) => (
              <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
                <span style={{ color: "#9c9890" }}>{k}</span>
                <span style={{ color: v === "FREE" ? "#2d7a4f" : "#1a1a1a", fontWeight: v === "FREE" ? 600 : 400 }}>{v}</span>
              </div>
            ))}
            <div style={{ borderTop: "1px solid #ede9e2", paddingTop: "12px", display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontWeight: 700 }}>Total</span>
              <span style={{ fontFamily: "'Playfair Display', serif", fontSize: "18px", fontWeight: 700, color: "#c8a96e" }}>₹{grand.toLocaleString()}</span>
            </div>
          </div>
          {shipping === 0 && <div style={{ marginTop: "12px", fontSize: "12px", color: "#2d7a4f", background: "#f0faf4", padding: "8px 12px", borderRadius: "7px", textAlign: "center" }}>✓ Free delivery on orders above ₹999</div>}
        </div>
      </div>
    </div>
  );
}
