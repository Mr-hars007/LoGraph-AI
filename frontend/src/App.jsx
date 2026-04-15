import { useState, useEffect, createContext, useContext } from 'react';
import StorePage from './StorePage';
import CheckoutPage from './CheckoutPage';
import AuthPage from './AuthPage';
import OrdersPage from './OrdersPage';
import { api } from './api';

// ── Global Context ────────────────────────────────────────────────────────────
export const AppContext = createContext(null);
export const useApp = () => useContext(AppContext);

// ── Global Styles (injected once) ────────────────────────────────────────────
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Cinzel:wght@400;500;600&family=DM+Sans:wght@300;400;500&display=swap');

  *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg:      #141210;
    --bg2:     #1c1916;
    --bg3:     #242018;
    --bg4:     #2e2820;
    --gold:    #c8a84b;
    --gold2:   #e2c86e;
    --cream:   #f0e6cc;
    --sand:    #b8a880;
    --muted:   #7a6e5a;
    --forest:  #1e3a1e;
    --forest2: #2d5a2d;
    --rust:    #7a2e10;
    --border:  rgba(200,168,75,0.15);
    --border2: rgba(200,168,75,0.35);
    --border3: rgba(200,168,75,0.55);
    --radius:  2px;
  }

  html { scroll-behavior: smooth; }
  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--cream);
    min-height: 100vh;
    overflow-x: hidden;
    -webkit-font-smoothing: antialiased;
  }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--gold); }

  ::selection { background: rgba(200,168,75,0.25); color: var(--cream); }

  button { cursor: pointer; border: none; font-family: inherit; }
  input, select, textarea { font-family: inherit; }
  a { text-decoration: none; color: inherit; }

  .serif { font-family: 'Cormorant Garamond', serif; }
  .cinzel { font-family: 'Cinzel', serif; }

  /* Animations */
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes fadeIn {
    from { opacity: 0; } to { opacity: 1; }
  }
  @keyframes slideRight {
    from { transform: translateX(100%); } to { transform: translateX(0); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; } 50% { opacity: 0.5; }
  }
  @keyframes spin {
    from { transform: rotate(0deg); } to { transform: rotate(360deg); }
  }
  @keyframes shimmer {
    0%   { background-position: -600px 0; }
    100% { background-position: 600px 0; }
  }

  .fade-up { animation: fadeUp 0.5s ease both; }
  .fade-in { animation: fadeIn 0.4s ease both; }

  /* Skeleton loader */
  .skeleton {
    background: linear-gradient(90deg, var(--bg3) 25%, var(--bg4) 50%, var(--bg3) 75%);
    background-size: 600px 100%;
    animation: shimmer 1.4s infinite;
    border-radius: var(--radius);
  }

  /* Toast */
  .toast-stack { position: fixed; bottom: 1.5rem; left: 50%; transform: translateX(-50%); z-index: 9999; display: flex; flex-direction: column; gap: 8px; pointer-events: none; }
  .toast {
    background: var(--forest);
    border: 1px solid var(--border2);
    color: var(--cream);
    font-family: 'Cinzel', serif;
    font-size: 11px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding: 12px 24px;
    white-space: nowrap;
    animation: fadeUp 0.35s ease;
    pointer-events: all;
  }
  .toast.error { background: var(--rust); border-color: rgba(255,100,60,0.4); }

  /* Divider */
  .divider { width: 100%; height: 1px; background: var(--border); margin: 2rem 0; }
  .divider-gold { background: var(--border2); }

  /* Ornament */
  .ornament { text-align: center; color: var(--gold); opacity: 0.35; letter-spacing: 0.5em; font-size: 11px; }
`;

function injectStyles() {
  if (document.getElementById('ishara-global')) return;
  const s = document.createElement('style');
  s.id = 'ishara-global';
  s.textContent = GLOBAL_CSS;
  document.head.appendChild(s);
}

// ── Topbar ────────────────────────────────────────────────────────────────────
function Topbar() {
  return (
    <div style={{
      background: 'var(--forest)',
      padding: '7px 0',
      textAlign: 'center',
      borderBottom: '1px solid rgba(200,168,75,0.12)',
    }}>
      <p style={{
        fontFamily: 'Cinzel, serif',
        fontSize: 10,
        letterSpacing: '0.22em',
        textTransform: 'uppercase',
        color: 'rgba(240,230,204,0.75)',
      }}>
        Free shipping above ₹999 &nbsp;·&nbsp; 100% Authentic Fakes &nbsp;·&nbsp; Returns: LOL good luck
      </p>
    </div>
  );
}

// ── Navbar ────────────────────────────────────────────────────────────────────
function Navbar({ page, setPage, cartCount, user, onLogout, onCartOpen }) {
  const navLinks = [
    { label: 'Store', key: 'store' },
    { label: 'Orders', key: 'orders' },
  ];
  return (
    <nav style={{
      background: 'rgba(20,18,16,0.97)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border)',
      padding: '0 3rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      height: 68,
      position: 'sticky',
      top: 0,
      zIndex: 500,
    }}>
      {/* Logo */}
      <button onClick={() => setPage('store')} style={{ background: 'none', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 1 }}>
        <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.55rem', fontWeight: 400, fontStyle: 'italic', color: 'var(--gold)', lineHeight: 1 }}>
          Ishara
        </span>
        <span style={{ fontFamily: 'Cinzel, serif', fontSize: 8, letterSpacing: '0.35em', textTransform: 'uppercase', color: 'var(--muted)' }}>
          Sacred Tech Emporium
        </span>
      </button>

      {/* Links */}
      <div style={{ display: 'flex', gap: '2.5rem', alignItems: 'center' }}>
        {navLinks.map(l => (
          <button key={l.key} onClick={() => setPage(l.key)} style={{
            background: 'none',
            fontFamily: 'Cinzel, serif',
            fontSize: 11,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            color: page === l.key ? 'var(--gold)' : 'var(--sand)',
            borderBottom: page === l.key ? '1px solid var(--gold)' : '1px solid transparent',
            paddingBottom: 2,
            transition: 'all 0.25s',
          }}>
            {l.label}
          </button>
        ))}
      </div>

      {/* Right side */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {user ? (
          <>
            <span style={{ fontFamily: 'Cinzel, serif', fontSize: 10, color: 'var(--muted)', letterSpacing: '0.1em' }}>
              {user.name}
            </span>
            <button onClick={onLogout} style={{
              background: 'none',
              fontFamily: 'Cinzel, serif',
              fontSize: 10,
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: 'var(--muted)',
              border: '1px solid var(--border)',
              padding: '6px 14px',
              transition: 'all 0.2s',
            }}>
              Logout
            </button>
          </>
        ) : (
          <button onClick={() => setPage('auth')} style={{
            background: 'none',
            fontFamily: 'Cinzel, serif',
            fontSize: 10,
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            color: 'var(--sand)',
            border: '1px solid var(--border)',
            padding: '6px 14px',
            transition: 'all 0.2s',
          }}>
            Login
          </button>
        )}

        {/* Cart */}
        <button onClick={onCartOpen} style={{
          background: 'none',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          border: '1px solid var(--border2)',
          padding: '7px 16px',
          fontFamily: 'Cinzel, serif',
          fontSize: 10,
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          color: 'var(--gold)',
          transition: 'all 0.25s',
        }}>
          <span>🛒</span>
          Cart
          {cartCount > 0 && (
            <span style={{
              background: 'var(--gold)',
              color: 'var(--bg)',
              borderRadius: '50%',
              width: 18,
              height: 18,
              fontSize: 9,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              {cartCount}
            </span>
          )}
        </button>
      </div>
    </nav>
  );
}

// ── Cart Drawer ───────────────────────────────────────────────────────────────
function CartDrawer({ open, onClose, cart, onQty, onCheckout }) {
  const total = cart.reduce((s, i) => s + i.price * i.qty, 0);

  return (
    <>
      {/* Overlay */}
      {open && (
        <div onClick={onClose} style={{
          position: 'fixed', inset: 0,
          background: 'rgba(10,8,6,0.75)',
          zIndex: 800,
          animation: 'fadeIn 0.3s ease',
        }} />
      )}

      {/* Drawer */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0,
        width: 400,
        background: 'var(--bg2)',
        borderLeft: '1px solid var(--border2)',
        zIndex: 900,
        display: 'flex',
        flexDirection: 'column',
        transform: open ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform 0.4s cubic-bezier(0.4,0,0.2,1)',
      }}>
        {/* Header */}
        <div style={{ padding: '1.4rem 1.5rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
          <span style={{ fontFamily: 'Cinzel, serif', fontSize: 12, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'var(--cream)' }}>
            Your Cart ({cart.reduce((s, i) => s + i.qty, 0)})
          </span>
          <button onClick={onClose} style={{ background: 'none', color: 'var(--muted)', fontSize: 20, lineHeight: 1 }}>×</button>
        </div>

        {/* Items */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1rem 1.5rem' }}>
          {cart.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '4rem 0' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>🛒</div>
              <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.2rem', fontStyle: 'italic', color: 'var(--muted)' }}>
                Your cart is as empty as<br />a monk's wardrobe
              </p>
            </div>
          ) : cart.map(item => (
            <div key={item.id} style={{
              display: 'flex', gap: 12, padding: '14px 0',
              borderBottom: '1px solid var(--border)',
            }}>
              <div style={{
                width: 68, height: 82, background: 'var(--bg3)',
                border: '1px solid var(--border)', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 28,
              }}>{item.emoji}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 13, color: 'var(--cream)', lineHeight: 1.35, marginBottom: 4 }}>{item.name}</p>
                <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, color: 'var(--muted)', letterSpacing: '0.1em', marginBottom: 8 }}>{item.category}</p>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.1rem', color: 'var(--gold)' }}>
                    ₹{(item.price * item.qty).toLocaleString('en-IN')}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <button onClick={() => onQty(item.id, -1)} style={{
                      background: 'var(--bg3)', border: '1px solid var(--border)',
                      color: 'var(--sand)', width: 26, height: 26, fontSize: 16,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>−</button>
                    <span style={{ fontFamily: 'Cinzel, serif', fontSize: 12, minWidth: 18, textAlign: 'center' }}>{item.qty}</span>
                    <button onClick={() => onQty(item.id, 1)} style={{
                      background: 'var(--bg3)', border: '1px solid var(--border)',
                      color: 'var(--sand)', width: 26, height: 26, fontSize: 16,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>+</button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{ padding: '1.2rem 1.5rem', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span style={{ fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'var(--muted)' }}>Subtotal</span>
            <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.5rem', color: 'var(--gold)' }}>
              ₹{total.toLocaleString('en-IN')}
            </span>
          </div>
          <button
            onClick={() => { onClose(); onCheckout(); }}
            disabled={cart.length === 0}
            style={{
              width: '100%', background: cart.length ? 'var(--gold)' : 'var(--bg3)',
              color: cart.length ? 'var(--bg)' : 'var(--muted)',
              fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em',
              textTransform: 'uppercase', padding: '15px',
              marginBottom: 8, transition: 'background 0.25s',
            }}>
            Proceed to Checkout
          </button>
          <button onClick={onClose} style={{
            width: '100%', background: 'transparent',
            color: 'var(--muted)', fontFamily: 'Cinzel, serif', fontSize: 10,
            letterSpacing: '0.15em', textTransform: 'uppercase', padding: '10px',
            border: '1px solid var(--border)',
          }}>
            Continue Shopping
          </button>
        </div>
      </div>
    </>
  );
}

// ── Toast Manager ─────────────────────────────────────────────────────────────
function ToastStack({ toasts }) {
  return (
    <div className="toast-stack">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type === 'error' ? 'error' : ''}`}>{t.msg}</div>
      ))}
    </div>
  );
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  injectStyles();

  const [page, setPage] = useState('store');
  const [cart, setCart] = useState([]);
  const [user, setUser] = useState(null);
  const [cartOpen, setCartOpen] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [completedOrder, setCompletedOrder] = useState(null);

  const toast = (msg, type = 'success') => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 2800);
  };

  const addToCart = (product) => {
    setCart(c => {
      const ex = c.find(i => i.id === product.id);
      if (ex) return c.map(i => i.id === product.id ? { ...i, qty: i.qty + 1 } : i);
      return [...c, { ...product, qty: 1 }];
    });
    toast(`${product.name.slice(0, 30)}… added`);
    setCartOpen(true);
  };

  const changeQty = (id, delta) => {
    setCart(c => {
      const updated = c.map(i => i.id === id ? { ...i, qty: i.qty + delta } : i);
      return updated.filter(i => i.qty > 0);
    });
  };

  const clearCart = () => setCart([]);

  const handleLogout = async () => {
    await api.logout();
    setUser(null);
<<<<<<< HEAD
    toast('Logged out. Snack break mode activated.');
=======
    toast('Logged out. The void awaits.');
>>>>>>> 6f15b6f (attented enlightment)
    setPage('store');
  };

  const handleOrderComplete = (order) => {
    setCompletedOrder(order);
    clearCart();
    toast(`Order ${order.id} placed! May it arrive before you change your mind.`);
    setPage('orders');
  };

  const cartCount = cart.reduce((s, i) => s + i.qty, 0);

  const ctx = { cart, addToCart, changeQty, clearCart, user, setUser, toast, setPage, completedOrder };

  const renderPage = () => {
    switch (page) {
      case 'store':    return <StorePage />;
      case 'auth':     return <AuthPage onSuccess={(u) => { setUser(u); setPage('store'); }} />;
      case 'checkout': return <CheckoutPage onComplete={handleOrderComplete} />;
      case 'orders':   return <OrdersPage />;
      default:         return <StorePage />;
    }
  };

  return (
    <AppContext.Provider value={ctx}>
      <Topbar />
      <Navbar
        page={page}
        setPage={setPage}
        cartCount={cartCount}
        user={user}
        onLogout={handleLogout}
        onCartOpen={() => setCartOpen(true)}
      />
      <main style={{ minHeight: 'calc(100vh - 110px)' }}>
        {renderPage()}
      </main>
      <CartDrawer
        open={cartOpen}
        onClose={() => setCartOpen(false)}
        cart={cart}
        onQty={changeQty}
        onCheckout={() => setPage('checkout')}
      />
      <ToastStack toasts={toasts} />
    </AppContext.Provider>
  );
}
