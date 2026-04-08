// Root storefront application shell.
// Manages shared app state (auth, cart, navigation) and routes page components.

import { useState, createContext, useContext } from "react";
import StorePage    from "./StorePage";
import AuthPage     from "./AuthPage";
import OrdersPage   from "./OrdersPage";
import CheckoutPage from "./CheckoutPage";

export const AppCtx = createContext(null);
export const useApp = () => useContext(AppCtx);

export const PRODUCTS = [
  { id: "P01", name: "Wireless Headphones",  price: 2499, category: "Electronics", rating: 4.5, reviews: 128, img: "🎧", tag: "Bestseller" },
  { id: "P02", name: "Running Shoes",         price: 1899, category: "Fashion",     rating: 4.3, reviews: 94,  img: "👟", tag: "New" },
  { id: "P03", name: "Coffee Maker",          price: 3299, category: "Kitchen",     rating: 4.7, reviews: 203, img: "☕", tag: "Top Rated" },
  { id: "P04", name: "Yoga Mat",              price: 699,  category: "Sports",      rating: 4.2, reviews: 67,  img: "🧘", tag: null },
  { id: "P05", name: "Mechanical Keyboard",   price: 4599, category: "Electronics", rating: 4.8, reviews: 312, img: "⌨️", tag: "Bestseller" },
  { id: "P06", name: "Skincare Kit",          price: 1299, category: "Beauty",      rating: 4.4, reviews: 156, img: "🧴", tag: "New" },
  { id: "P07", name: "Steel Water Bottle",    price: 549,  category: "Sports",      rating: 4.6, reviews: 89,  img: "🍶", tag: null },
  { id: "P08", name: "Desk Lamp",             price: 899,  category: "Home",        rating: 4.1, reviews: 44,  img: "🪔", tag: null },
];

export default function App() {
  const [page, setPage]         = useState("store");
  const [user, setUser]         = useState(null);
  const [cart, setCart]         = useState([]);
  const [toast, setToast]       = useState(null);
  const [cartOpen, setCartOpen] = useState(false);

  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const addToCart = (product) => {
    setCart(prev => {
      const exists = prev.find(i => i.id === product.id);
      if (exists) return prev.map(i => i.id === product.id ? { ...i, qty: i.qty + 1 } : i);
      return [...prev, { ...product, qty: 1 }];
    });
    showToast(`${product.name} added to cart`);
  };

  const removeFromCart = (id) => setCart(prev => prev.filter(i => i.id !== id));
  const updateQty = (id, qty) => {
    if (qty < 1) return removeFromCart(id);
    setCart(prev => prev.map(i => i.id === id ? { ...i, qty } : i));
  };

  const cartCount = cart.reduce((s, i) => s + i.qty, 0);
  const cartTotal = cart.reduce((s, i) => s + i.price * i.qty, 0);
  const logout    = () => { setUser(null); showToast("Logged out"); setPage("store"); };
  const nav       = (p) => { setCartOpen(false); setPage(p); };

  return (
    <AppCtx.Provider value={{ user, setUser, cart, setCart, addToCart, removeFromCart, updateQty, cartTotal, cartCount, showToast, nav }}>
      <div style={{ fontFamily: "'DM Sans', 'Segoe UI', sans-serif", background: "#fafaf8", minHeight: "100vh", color: "#1a1a1a" }}>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet" />

        {/* NAV */}
        <nav style={{ background: "#fff", borderBottom: "1px solid #ede9e2", position: "sticky", top: 0, zIndex: 100, padding: "0 48px", display: "flex", alignItems: "center", justifyContent: "space-between", height: "64px" }}>
          <div onClick={() => nav("store")} style={{ cursor: "pointer", fontFamily: "'Playfair Display', serif", fontWeight: 800, fontSize: "24px", letterSpacing: "-0.02em" }}>
            MART<span style={{ color: "#c8a96e" }}>·</span>
          </div>
          <div style={{ display: "flex", gap: "32px" }}>
            {[["store","Shop"],["orders","My Orders"]].map(([p,label]) => (
              <button key={p} onClick={() => p === "orders" && !user ? nav("auth") : nav(p)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "14px", color: page === p ? "#1a1a1a" : "#9c9890", fontWeight: page === p ? 600 : 400, fontFamily: "inherit", borderBottom: page === p ? "2px solid #c8a96e" : "2px solid transparent", paddingBottom: "2px", transition: "all 0.2s" }}>{label}</button>
            ))}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {user ? (
              <>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: "#f5ede0", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px", fontWeight: 700, color: "#c8a96e" }}>{user.name?.[0]?.toUpperCase()}</div>
                  <span style={{ fontSize: "13px", color: "#5a5550" }}>{user.name?.split(" ")[0]}</span>
                </div>
                <button onClick={logout} style={{ background: "none", border: "1px solid #ede9e2", borderRadius: "7px", padding: "6px 14px", cursor: "pointer", fontSize: "12px", color: "#9c9890", fontFamily: "inherit" }}>Logout</button>
              </>
            ) : (
              <button onClick={() => nav("auth")} style={{ background: "#1a1a1a", border: "none", color: "#fff", padding: "9px 22px", borderRadius: "9px", cursor: "pointer", fontSize: "13px", fontFamily: "inherit", fontWeight: 500 }}>Sign In</button>
            )}
            <button onClick={() => setCartOpen(o => !o)} style={{ background: cartCount > 0 ? "#1a1a1a" : "#f5f3ef", border: "none", borderRadius: "10px", padding: "9px 16px", cursor: "pointer", display: "flex", alignItems: "center", gap: "8px", transition: "all 0.2s" }}>
              <span style={{ fontSize: "16px" }}>🛒</span>
              <span style={{ fontSize: "13px", fontWeight: 600, color: cartCount > 0 ? "#fff" : "#1a1a1a", fontFamily: "inherit" }}>{cartCount > 0 ? `${cartCount} · ₹${cartTotal.toLocaleString()}` : "Cart"}</span>
            </button>
          </div>
        </nav>

        {/* CART DRAWER */}
        {cartOpen && (
          <>
            <div onClick={() => setCartOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.25)", zIndex: 200 }} />
            <div style={{ position: "fixed", top: 0, right: 0, bottom: 0, width: "390px", background: "#fff", zIndex: 201, display: "flex", flexDirection: "column", animation: "slideIn .25s ease" }}>
              <div style={{ padding: "22px 24px", borderBottom: "1px solid #ede9e2", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontFamily: "'Playfair Display', serif", fontWeight: 700, fontSize: "20px" }}>Cart <span style={{ color: "#c8a96e" }}>({cartCount})</span></span>
                <button onClick={() => setCartOpen(false)} style={{ background: "#f5f3ef", border: "none", width: "32px", height: "32px", borderRadius: "50%", cursor: "pointer", fontSize: "18px", color: "#5a5550", display: "flex", alignItems: "center", justifyContent: "center" }}>×</button>
              </div>
              <div style={{ flex: 1, overflowY: "auto", padding: "8px 24px" }}>
                {cart.length === 0
                  ? <div style={{ textAlign: "center", padding: "60px 0", color: "#b0ada6" }}><div style={{ fontSize: "48px", marginBottom: "14px" }}>🛒</div><div>Your cart is empty</div></div>
                  : cart.map(item => (
                    <div key={item.id} style={{ display: "flex", gap: "14px", padding: "16px 0", borderBottom: "1px solid #f0ede8" }}>
                      <div style={{ width: "56px", height: "56px", borderRadius: "12px", background: "#f5f3ef", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "26px", flexShrink: 0 }}>{item.img}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "3px" }}>{item.name}</div>
                        <div style={{ fontSize: "14px", color: "#c8a96e", fontWeight: 600 }}>₹{item.price.toLocaleString()}</div>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "10px" }}>
                          {[[-1,"−"],[1,"+"]].map(([d, lbl]) => (
                            <button key={d} onClick={() => updateQty(item.id, item.qty + d)} style={{ width: "28px", height: "28px", borderRadius: "7px", border: "1px solid #ede9e2", background: "#fafaf8", cursor: "pointer", fontSize: "15px", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "inherit" }}>{lbl}</button>
                          ))}
                          <span style={{ fontSize: "14px", fontWeight: 600, minWidth: "22px", textAlign: "center" }}>{item.qty}</span>
                          <button onClick={() => removeFromCart(item.id)} style={{ marginLeft: "auto", background: "none", border: "none", color: "#c4968a", cursor: "pointer", fontSize: "12px", fontFamily: "inherit" }}>Remove</button>
                        </div>
                      </div>
                    </div>
                  ))
                }
              </div>
              {cart.length > 0 && (
                <div style={{ padding: "20px 24px", borderTop: "1px solid #ede9e2" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                    <span style={{ color: "#9c9890" }}>Subtotal</span>
                    <span style={{ fontWeight: 700, fontSize: "16px" }}>₹{cartTotal.toLocaleString()}</span>
                  </div>
                  <div style={{ fontSize: "12px", color: "#b0ada6", marginBottom: "16px" }}>Taxes and shipping calculated at checkout</div>
                  <button onClick={() => { setCartOpen(false); nav(user ? "checkout" : "auth"); }} style={{ width: "100%", background: "#1a1a1a", color: "#fff", border: "none", borderRadius: "10px", padding: "15px", fontSize: "15px", fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>
                    Proceed to Checkout →
                  </button>
                </div>
              )}
            </div>
          </>
        )}

        {/* TOAST */}
        {toast && (
          <div style={{ position: "fixed", bottom: "28px", left: "50%", transform: "translateX(-50%)", background: toast.type === "error" ? "#3d1f1f" : "#1a1a1a", color: "#fff", padding: "12px 26px", borderRadius: "100px", fontSize: "13px", fontWeight: 500, zIndex: 500, animation: "fadeUp .2s ease", whiteSpace: "nowrap", boxShadow: "0 4px 24px rgba(0,0,0,0.18)" }}>
            {toast.type === "error" ? "✕ " : "✓ "}{toast.msg}
          </div>
        )}

        {page === "store"    && <StorePage />}
        {page === "auth"     && <AuthPage />}
        {page === "orders"   && <OrdersPage />}
        {page === "checkout" && <CheckoutPage />}

        <style>{`
          @keyframes slideIn { from{transform:translateX(100%)} to{transform:translateX(0)} }
          @keyframes fadeUp  { from{opacity:0;transform:translateX(-50%) translateY(10px)} to{opacity:1;transform:translateX(-50%) translateY(0)} }
          * { box-sizing:border-box; margin:0; padding:0; }
          ::-webkit-scrollbar{width:5px} ::-webkit-scrollbar-thumb{background:#e0ddd7;border-radius:4px}
        `}</style>
      </div>
    </AppCtx.Provider>
  );
}
