import { useState } from "react";
import { useApp, PRODUCTS } from "./App";

const CATEGORIES = ["All", "Electronics", "Fashion", "Kitchen", "Sports", "Beauty", "Home"];

const Stars = ({ rating }) => {
  const full = Math.floor(rating);
  const half = rating % 1 >= 0.5;
  return (
    <span style={{ fontSize: "12px", color: "#c8a96e", letterSpacing: "1px" }}>
      {"★".repeat(full)}{half ? "½" : ""}{"☆".repeat(5 - full - (half ? 1 : 0))}
    </span>
  );
};

export default function StorePage() {
  const { addToCart } = useApp();
  const [category, setCategory] = useState("All");
  const [search,   setSearch]   = useState("");
  const [added,    setAdded]    = useState({});

  const filtered = PRODUCTS.filter(p =>
    (category === "All" || p.category === category) &&
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  const handleAdd = (product) => {
    addToCart(product);
    setAdded(a => ({ ...a, [product.id]: true }));
    setTimeout(() => setAdded(a => ({ ...a, [product.id]: false })), 1200);
  };

  return (
    <div>
      {/* HERO */}
      <div style={{ background: "#1a1a1a", color: "#fff", padding: "72px 48px", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: "-60px", right: "-60px", width: "400px", height: "400px", borderRadius: "50%", background: "rgba(200,169,110,0.08)" }} />
        <div style={{ position: "absolute", bottom: "-80px", left: "30%", width: "300px", height: "300px", borderRadius: "50%", background: "rgba(200,169,110,0.05)" }} />
        <div style={{ position: "relative", maxWidth: "600px" }}>
          <div style={{ fontSize: "12px", letterSpacing: "0.2em", color: "#c8a96e", marginBottom: "16px", fontWeight: 600 }}>FREE DELIVERY OVER ₹999</div>
          <h1 style={{ fontFamily: "'Playfair Display', serif", fontWeight: 800, fontSize: "clamp(2.2rem, 5vw, 3.6rem)", lineHeight: 1.15, marginBottom: "20px", letterSpacing: "-0.02em" }}>
            Shop Everything<br /><span style={{ color: "#c8a96e" }}>You Love.</span>
          </h1>
          <p style={{ fontSize: "16px", color: "#a09d97", lineHeight: 1.7, marginBottom: "28px", maxWidth: "440px" }}>
            Curated products across electronics, fashion, kitchen, and more — delivered fast.
          </p>
          <div style={{ display: "flex", gap: "12px" }}>
            <div style={{ background: "#fff", borderRadius: "10px", padding: "12px 20px", display: "flex", gap: "10px", alignItems: "center", flex: 1, maxWidth: "360px" }}>
              <span style={{ fontSize: "16px" }}>🔍</span>
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search products…"
                style={{ border: "none", outline: "none", fontSize: "14px", background: "transparent", color: "#1a1a1a", flex: 1, fontFamily: "inherit" }}
              />
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: "1280px", margin: "0 auto", padding: "40px 48px" }}>
        {/* Category pills */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "32px", flexWrap: "wrap" }}>
          {CATEGORIES.map(cat => (
            <button key={cat} onClick={() => setCategory(cat)} style={{
              background: category === cat ? "#1a1a1a" : "#fff",
              color: category === cat ? "#fff" : "#5a5550",
              border: category === cat ? "none" : "1px solid #ede9e2",
              padding: "8px 20px", borderRadius: "100px", cursor: "pointer",
              fontSize: "13px", fontFamily: "inherit", fontWeight: category === cat ? 600 : 400,
              transition: "all 0.2s",
            }}>{cat}</button>
          ))}
          {search && <span style={{ fontSize: "13px", color: "#9c9890", alignSelf: "center", marginLeft: "4px" }}>Showing results for "<strong>{search}</strong>"</span>}
        </div>

        {/* Product grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "20px" }}>
          {filtered.map(product => (
            <div key={product.id} style={{ background: "#fff", borderRadius: "16px", overflow: "hidden", border: "1px solid #ede9e2", transition: "transform 0.2s, box-shadow 0.2s", cursor: "default" }}
              onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.boxShadow = "0 8px 32px rgba(0,0,0,0.08)"; }}
              onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}
            >
              {/* Product image area */}
              <div style={{ background: "#f5f3ef", height: "180px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "64px", position: "relative" }}>
                {product.img}
                {product.tag && (
                  <div style={{ position: "absolute", top: "12px", left: "12px", background: "#1a1a1a", color: "#fff", fontSize: "10px", fontWeight: 700, padding: "4px 10px", borderRadius: "100px", letterSpacing: "0.08em" }}>{product.tag}</div>
                )}
              </div>
              {/* Info */}
              <div style={{ padding: "16px 18px 18px" }}>
                <div style={{ fontSize: "11px", color: "#b0ada6", letterSpacing: "0.1em", marginBottom: "5px" }}>{product.category.toUpperCase()}</div>
                <div style={{ fontSize: "15px", fontWeight: 600, marginBottom: "8px", lineHeight: 1.3 }}>{product.name}</div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "14px" }}>
                  <Stars rating={product.rating} />
                  <span style={{ fontSize: "12px", color: "#b0ada6" }}>({product.reviews})</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontFamily: "'Playfair Display', serif", fontSize: "20px", fontWeight: 700, color: "#1a1a1a" }}>₹{product.price.toLocaleString()}</span>
                  <button onClick={() => handleAdd(product)} style={{
                    background: added[product.id] ? "#2d5a3d" : "#1a1a1a",
                    color: "#fff", border: "none", borderRadius: "9px",
                    padding: "9px 18px", cursor: "pointer", fontSize: "13px",
                    fontFamily: "inherit", fontWeight: 500, transition: "all 0.2s",
                    minWidth: "100px",
                  }}>
                    {added[product.id] ? "✓ Added" : "Add to Cart"}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filtered.length === 0 && (
          <div style={{ textAlign: "center", padding: "80px 0", color: "#b0ada6" }}>
            <div style={{ fontSize: "48px", marginBottom: "16px" }}>🔍</div>
            <div style={{ fontSize: "16px", marginBottom: "8px" }}>No products found</div>
            <div style={{ fontSize: "14px" }}>Try a different search or category</div>
          </div>
        )}
      </div>

      {/* FOOTER */}
      <footer style={{ background: "#1a1a1a", color: "#5a5550", padding: "40px 48px", marginTop: "60px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        <div style={{ fontFamily: "'Playfair Display', serif", fontWeight: 800, fontSize: "20px", color: "#fff" }}>MART<span style={{ color: "#c8a96e" }}>·</span></div>
        <div style={{ fontSize: "12px", letterSpacing: "0.05em" }}>Powered by User · Order · Payment microservices</div>
        <div style={{ fontSize: "12px" }}>© 2024 Mart. All rights reserved.</div>
      </footer>
    </div>
  );
}
