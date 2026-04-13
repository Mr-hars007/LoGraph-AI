import { useState, useEffect } from 'react';
import { useApp } from './App';
import { api, fmt } from './api';

const STATUS_CONFIG = {
  processing: { label: 'Processing',  color: '#c8a84b', bg: 'rgba(200,168,75,0.1)',  icon: '⏳', steps: 1 },
  shipped:    { label: 'Shipped',     color: '#4a9a6a', bg: 'rgba(74,154,106,0.1)',  icon: '🚚', steps: 2 },
  delivered:  { label: 'Delivered',   color: '#5a8a4a', bg: 'rgba(90,138,74,0.12)', icon: '✓',  steps: 4 },
  cancelled:  { label: 'Cancelled',   color: '#9a4a2a', bg: 'rgba(154,74,42,0.1)',  icon: '✕',  steps: 0 },
};

const TRACK_STEPS = ['Order Placed', 'Confirmed', 'Shipped', 'Out for Delivery', 'Delivered'];

function TrackingBar({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.processing;
  return (
    <div style={{ marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
        {TRACK_STEPS.map((s, i) => (
          <div key={s} style={{ display: 'flex', alignItems: 'center', flex: i < TRACK_STEPS.length - 1 ? 1 : 'none' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flexShrink: 0 }}>
              <div style={{
                width: 28, height: 28, borderRadius: '50%',
                border: `1px solid ${i <= cfg.steps ? cfg.color : 'var(--border)'}`,
                background: i < cfg.steps ? cfg.color : i === cfg.steps ? 'rgba(200,168,75,0.1)' : 'transparent',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: i < cfg.steps ? 12 : 10,
                color: i < cfg.steps ? 'var(--bg)' : i === cfg.steps ? cfg.color : 'var(--muted)',
                transition: 'all 0.3s',
              }}>
                {i < cfg.steps ? '✓' : i + 1}
              </div>
              <span style={{ fontFamily: 'Cinzel, serif', fontSize: 8, letterSpacing: '0.08em', textTransform: 'uppercase', color: i <= cfg.steps ? cfg.color : 'var(--muted)', textAlign: 'center', maxWidth: 60 }}>{s}</span>
            </div>
            {i < TRACK_STEPS.length - 1 && (
              <div style={{ flex: 1, height: 1, background: i < cfg.steps ? cfg.color : 'var(--border)', margin: '0 4px', marginBottom: 22, transition: 'background 0.3s' }} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function OrderCard({ order, expanded, onToggle }) {
  const cfg = STATUS_CONFIG[order.status] || STATUS_CONFIG.processing;
  const placedDate = new Date(order.placedAt).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <div style={{
      background: 'var(--bg2)', border: `1px solid ${expanded ? 'var(--border2)' : 'var(--border)'}`,
      marginBottom: '1rem', transition: 'border 0.3s', overflow: 'hidden',
    }}>
      {/* Header */}
      <button onClick={onToggle} style={{
        width: '100%', background: 'none', display: 'flex',
        alignItems: 'center', justifyContent: 'space-between',
        padding: '1.3rem 1.5rem', cursor: 'pointer', textAlign: 'left',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
          <div>
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 4 }}>Order ID</p>
            <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.1rem', color: 'var(--cream)' }}>{order.id}</p>
          </div>
          <div>
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 4 }}>Placed</p>
            <p style={{ fontSize: 13, color: 'var(--sand)' }}>{placedDate}</p>
          </div>
          <div>
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 4 }}>Total</p>
            <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.15rem', color: 'var(--gold)' }}>{fmt(order.total)}</p>
          </div>
          <div>
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 4 }}>Items</p>
            <p style={{ fontSize: 13, color: 'var(--sand)' }}>{order.items.reduce((s, i) => s + i.qty, 0)}</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexShrink: 0 }}>
          <span style={{
            background: cfg.bg, color: cfg.color,
            border: `1px solid ${cfg.color}33`,
            fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.15em', textTransform: 'uppercase',
            padding: '5px 12px', display: 'flex', alignItems: 'center', gap: 6,
          }}>
            {cfg.icon} {cfg.label}
          </span>
          <span style={{ color: 'var(--muted)', fontSize: 16, transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.3s' }}>▾</span>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div style={{ padding: '0 1.5rem 1.5rem', borderTop: '1px solid var(--border)', animation: 'fadeUp 0.3s ease' }}>
          {/* Tracking */}
          <div style={{ padding: '1.5rem 0', borderBottom: '1px solid var(--border)' }}>
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: '1rem' }}>Tracking</p>
            <TrackingBar status={order.status} />
          </div>

          {/* Items */}
          <div style={{ paddingTop: '1.2rem' }}>
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: '1rem' }}>Items Ordered</p>
            {order.items.map(item => (
              <div key={item.id} style={{
                display: 'flex', alignItems: 'center', gap: 14, padding: '10px 0',
                borderBottom: '1px solid var(--border)',
              }}>
                <div style={{
                  width: 56, height: 56, background: 'var(--bg3)',
                  border: '1px solid var(--border)', flexShrink: 0,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
                }}>{item.emoji}</div>
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: 13, color: 'var(--cream)', marginBottom: 3 }}>{item.name}</p>
                  <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, color: 'var(--muted)', letterSpacing: '0.1em' }}>
                    {item.category} · Qty: {item.qty}
                  </p>
                </div>
                <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.1rem', color: 'var(--gold)' }}>
                  {fmt(item.price * item.qty)}
                </span>
              </div>
            ))}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '0.8rem', marginTop: '1.2rem', flexWrap: 'wrap' }}>
            {order.status === 'delivered' && (
              <button style={{
                background: 'transparent', color: 'var(--sand)',
                border: '1px solid var(--border2)', fontFamily: 'Cinzel, serif',
                fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', padding: '8px 18px',
              }}>Write Review</button>
            )}
            {order.status === 'delivered' && (
              <button style={{
                background: 'var(--gold)', color: 'var(--bg)',
                fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.15em',
                textTransform: 'uppercase', padding: '8px 18px', border: 'none',
              }}>Reorder</button>
            )}
            {order.status !== 'delivered' && order.status !== 'cancelled' && (
              <button style={{
                background: 'transparent', color: 'var(--muted)',
                border: '1px solid var(--border)', fontFamily: 'Cinzel, serif',
                fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', padding: '8px 18px',
              }}>Download Invoice</button>
            )}
            <button style={{
              background: 'transparent', color: 'var(--muted)',
              border: '1px solid var(--border)', fontFamily: 'Cinzel, serif',
              fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase', padding: '8px 18px',
            }}>Contact Support</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function OrdersPage() {
  const { user, setPage, completedOrder } = useApp();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    const load = async () => {
      const list = await api.getOrders();
      if (completedOrder) {
        setOrders([completedOrder, ...list]);
        setExpanded(completedOrder.id);
      } else {
        setOrders(list);
        if (list.length) setExpanded(list[0].id);
      }
      setLoading(false);
    };
    load();
  }, []);

  const filtered = filter === 'all' ? orders : orders.filter(o => o.status === filter);

  if (!user) {
    return (
      <div style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1.5rem', padding: '4rem' }}>
        <div style={{ fontSize: 56 }}>🔐</div>
        <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.4rem', fontStyle: 'italic', color: 'var(--muted)', textAlign: 'center' }}>
          Please log in to view your orders.<br />Your purchase history awaits.
        </p>
        <button onClick={() => setPage('auth')} style={{
          background: 'var(--gold)', color: 'var(--bg)',
          fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase',
          padding: '13px 28px', border: 'none',
        }}>Login to Continue</button>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', padding: '3.5rem 3rem' }}>
      <div style={{ maxWidth: 860, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2.5rem' }}>
          <p style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: 8 }}>My Account</p>
          <h1 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 'clamp(1.8rem,3vw,2.8rem)', fontWeight: 300, color: 'var(--cream)', marginBottom: '0.3rem' }}>Order History</h1>
          <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1rem', fontStyle: 'italic', color: 'var(--muted)' }}>
            A chronicle of your material acquisitions, {user.name}.
          </p>
        </div>

        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '1rem', marginBottom: '2rem' }}>
          {[
            ['Total Orders', orders.length],
            ['Delivered',    orders.filter(o => o.status === 'delivered').length],
            ['In Transit',   orders.filter(o => o.status === 'shipped').length],
            ['Processing',   orders.filter(o => o.status === 'processing').length],
          ].map(([label, val]) => (
            <div key={label} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', padding: '1.2rem', textAlign: 'center' }}>
              <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '2rem', color: 'var(--gold)', lineHeight: 1, marginBottom: 4 }}>{val}</p>
              <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'var(--muted)' }}>{label}</p>
            </div>
          ))}
        </div>

        {/* Filter tabs */}
        <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          {['all', 'processing', 'shipped', 'delivered'].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase',
              padding: '7px 16px',
              background: filter === f ? 'var(--gold)' : 'transparent',
              color: filter === f ? 'var(--bg)' : 'var(--muted)',
              border: `1px solid ${filter === f ? 'var(--gold)' : 'var(--border)'}`,
              cursor: 'pointer', transition: 'all 0.25s',
            }}>
              {f === 'all' ? 'All Orders' : STATUS_CONFIG[f].label}
            </button>
          ))}
        </div>

        {/* Orders */}
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {[1, 2, 3].map(i => <div key={i} style={{ height: 80 }} className="skeleton" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '5rem 0' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📦</div>
            <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.3rem', fontStyle: 'italic', color: 'var(--muted)' }}>
              No orders here yet. Your next masterpiece is waiting.
            </p>
            <button onClick={() => setPage('store')} style={{
              marginTop: '1.5rem', background: 'var(--gold)', color: 'var(--bg)',
              fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase',
              padding: '12px 24px', border: 'none',
            }}>Start Shopping</button>
          </div>
        ) : (
          filtered.map(order => (
            <OrderCard
              key={order.id}
              order={order}
              expanded={expanded === order.id}
              onToggle={() => setExpanded(expanded === order.id ? null : order.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
