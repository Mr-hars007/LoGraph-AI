import { useState, useEffect } from 'react';
import { useApp } from './App';
import { api, CATEGORIES, fmt } from './api';

// ── Product Card ──────────────────────────────────────────────────────────────
function ProductCard({ product, onAdd }) {
  const [hovered, setHovered] = useState(false);
  const [adding, setAdding] = useState(false);

  const handleAdd = async (e) => {
    e.stopPropagation();
    setAdding(true);
    onAdd(product);
    setTimeout(() => setAdding(false), 700);
  };

  const badgeStyle = {
    position: 'absolute', top: 12, left: 12,
    fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.15em',
    textTransform: 'uppercase', padding: '4px 10px',
    background: product.badge === 'sale' ? 'var(--rust)' :
                product.badge === 'new'  ? 'var(--forest2)' :
                'rgba(200,168,75,0.15)',
    color: product.badge === 'best' ? 'var(--gold)' : 'rgba(240,230,204,0.9)',
    border: product.badge === 'best' ? '1px solid rgba(200,168,75,0.3)' : 'none',
  };

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: 'var(--bg2)',
        border: `1px solid ${hovered ? 'var(--border2)' : 'var(--border)'}`,
        transform: hovered ? 'translateY(-4px)' : 'translateY(0)',
        transition: 'all 0.35s cubic-bezier(0.4,0,0.2,1)',
        cursor: 'pointer',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Image area */}
      <div style={{
        height: 220,
        background: 'var(--bg3)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative',
        overflow: 'hidden',
        flexShrink: 0,
      }}>
        <span style={{ fontSize: 64, filter: 'saturate(0.7)', transition: 'transform 0.4s', transform: hovered ? 'scale(1.1)' : 'scale(1)' }}>
          {product.emoji}
        </span>
        {product.badge && <span style={badgeStyle}>{product.badge === 'best' ? 'Bestseller' : product.badge === 'sale' ? 'Sale' : 'New'}</span>}

        {/* Hover overlay with quick-add */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'rgba(20,18,16,0.72)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          opacity: hovered ? 1 : 0,
          transition: 'opacity 0.3s',
        }}>
          <button onClick={handleAdd} style={{
            background: adding ? 'var(--forest2)' : 'var(--gold)',
            color: 'var(--bg)',
            fontFamily: 'Cinzel, serif', fontSize: 9,
            letterSpacing: '0.15em', textTransform: 'uppercase',
            padding: '9px 18px',
            transition: 'background 0.2s',
          }}>
            {adding ? 'Added ✓' : 'Add to Cart'}
          </button>
          <button style={{
            background: 'transparent',
            border: '1px solid rgba(240,230,204,0.3)',
            color: 'var(--cream)', fontSize: 16, padding: '8px 12px',
          }}>♡</button>
        </div>
      </div>

      {/* Info */}
      <div style={{ padding: '1.2rem', flex: 1, display: 'flex', flexDirection: 'column' }}>
        <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 6 }}>
          {product.category}
        </p>
        <p style={{ fontSize: 13, color: 'var(--cream)', lineHeight: 1.4, marginBottom: 6, fontWeight: 400 }}>
          {product.name}
        </p>
        <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 12, fontStyle: 'italic', color: 'var(--muted)', lineHeight: 1.5, marginBottom: 10, flex: 1 }}>
          {product.desc.slice(0, 80)}…
        </p>

        {/* Rating */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 10 }}>
          <span style={{ color: 'var(--gold)', fontSize: 11, letterSpacing: 1 }}>
            {'★'.repeat(Math.floor(product.rating))}{'☆'.repeat(5 - Math.floor(product.rating))}
          </span>
          <span style={{ fontFamily: 'Cinzel, serif', fontSize: 9, color: 'var(--muted)' }}>
            {product.rating} ({product.reviews.toLocaleString()})
          </span>
        </div>

        {/* Price + CTA */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.2rem', color: 'var(--gold)' }}>
              {fmt(product.price)}
            </span>
            {product.oldPrice && (
              <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '0.9rem', color: 'var(--muted)', textDecoration: 'line-through', marginLeft: 6 }}>
                {fmt(product.oldPrice)}
              </span>
            )}
          </div>
          <button onClick={handleAdd} style={{
            background: 'transparent',
            border: '1px solid var(--border2)',
            color: 'var(--sand)',
            fontFamily: 'Cinzel, serif', fontSize: 9,
            letterSpacing: '0.12em', textTransform: 'uppercase',
            padding: '6px 14px',
            transition: 'all 0.2s',
          }}>
            Add +
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Hero ──────────────────────────────────────────────────────────────────────
function Hero({ onShop }) {
  return (
    <div style={{
      background: 'var(--bg2)',
      borderBottom: '1px solid var(--border)',
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      minHeight: '72vh',
      overflow: 'hidden',
    }}>
      {/* Left */}
      <div style={{ padding: '5rem 4rem 5rem 5rem', display: 'flex', flexDirection: 'column', justifyContent: 'center', animation: 'fadeUp 0.8s ease both' }}>
        <p style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.35em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: '1.8rem', display: 'flex', alignItems: 'center', gap: 12 }}>
          New Arrivals
          <span style={{ display: 'inline-block', width: 40, height: 1, background: 'var(--gold)', opacity: 0.5 }} />
        </p>
        <h1 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 'clamp(2.4rem,4.5vw,4rem)', fontWeight: 300, lineHeight: 1.1, color: 'var(--cream)', marginBottom: '0.8rem' }}>
          Tech That Costs<br />
          More Than Your <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>Soul</em>
        </h1>
        <p style={{ fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '1.8rem' }}>
          Sacred Electronics · Probably Overpriced
        </p>
        <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.1rem', fontStyle: 'italic', color: 'var(--sand)', lineHeight: 1.8, maxWidth: 420, marginBottom: '2.5rem' }}>
          Curated gadgets for those who seek enlightenment through unboxing. Free shipping. No refunds on awakening.
        </p>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button onClick={onShop} style={{
            background: 'var(--gold)', color: 'var(--bg)',
            fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase',
            padding: '14px 32px', border: 'none', transition: 'background 0.3s',
          }}>Shop the Collection</button>
          <button style={{
            background: 'transparent', color: 'var(--sand)',
            fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.18em', textTransform: 'uppercase',
            padding: '14px 32px', border: '1px solid var(--border2)', transition: 'all 0.3s',
          }}>View Lookbook</button>
        </div>
      </div>

      {/* Right — decorative visual */}
      <div style={{
        background: 'var(--bg3)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Concentric rings */}
        {[280, 210, 140, 70].map((r, i) => (
          <div key={r} style={{
            position: 'absolute', width: r, height: r,
            border: `1px solid rgba(200,168,75,${0.04 + i * 0.03})`,
            borderRadius: '50%',
            top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)',
          }} />
        ))}
        <div style={{ textAlign: 'center', position: 'relative', zIndex: 2 }}>
          <div style={{ fontSize: 96, marginBottom: 16, filter: 'drop-shadow(0 0 30px rgba(200,168,75,0.2))' }}>📱</div>
          <div style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.8rem', color: 'var(--gold)', marginBottom: 4 }}>₹89,999</div>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'var(--muted)' }}>Samsang Galaxxy S69 Ultra</div>
        </div>
        {/* Corner ornaments */}
        <div style={{ position: 'absolute', top: '1.5rem', right: '1.5rem', width: 60, height: 60, border: '1px solid var(--border)', borderRadius: '50%', opacity: 0.4 }} />
        <div style={{ position: 'absolute', bottom: '1.5rem', left: '1.5rem', width: 36, height: 36, border: '1px solid var(--border)', borderRadius: '50%', opacity: 0.3 }} />
      </div>
    </div>
  );
}

// ── Trust Bar ─────────────────────────────────────────────────────────────────
function TrustBar() {
  const items = [
    { icon: '✓', text: '100% Authentic (allegedly)' },
    { icon: '→', text: 'Free Ship > ₹999' },
    { icon: '↻', text: '30-Day Returns (good luck)' },
    { icon: '⚡', text: 'Express Delivery' },
    { icon: '🔒', text: 'Secure Checkout' },
  ];
  return (
    <div style={{
      background: 'var(--forest)',
      borderBottom: '1px solid rgba(200,168,75,0.12)',
      padding: '1rem 3rem',
      display: 'flex', justifyContent: 'space-around', flexWrap: 'wrap', gap: '1rem',
    }}>
      {items.map(it => (
        <div key={it.text} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, color: 'var(--gold)' }}>{it.icon}</span>
          <span style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'rgba(240,230,204,0.65)' }}>{it.text}</span>
        </div>
      ))}
    </div>
  );
}

// ── Category Pill Row ─────────────────────────────────────────────────────────
const CAT_ICONS = { All: '∞', Phones: '📱', Laptops: '💻', Audio: '🎧', TVs: '📺', Wearables: '⌚', Gadgets: '⚡' };

// ── StorePage ────────────────────────────────────────────────────────────────
export default function StorePage() {
  const { addToCart } = useApp();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('All');
  const [sort, setSort] = useState('featured');
  const [search, setSearch] = useState('');
  const shopRef = { current: null };

  const load = async () => {
    setLoading(true);
    const list = await api.getProducts({ category, sort, search });
    setProducts(list);
    setLoading(false);
  };

  useEffect(() => { load(); }, [category, sort, search]);

  const scrollToShop = () => {
    document.getElementById('shop-section')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div>
      <Hero onShop={scrollToShop} />
      <TrustBar />

      {/* Category showcase */}
      <div style={{ padding: '4rem 3rem', background: 'var(--bg)', borderBottom: '1px solid var(--border)' }}>
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <p style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: '0.7rem' }}>Browse by Category</p>
          <h2 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 'clamp(1.6rem,3vw,2.6rem)', fontWeight: 300, color: 'var(--cream)' }}>
            Find What <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>Drains</em> Your Wallet
          </h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6,1fr)', gap: '1rem' }}>
          {CATEGORIES.filter(c => c !== 'All').map(cat => (
            <button key={cat} onClick={() => { setCategory(cat); scrollToShop(); }} style={{
              background: 'var(--bg2)', border: '1px solid var(--border)',
              padding: '2rem 1rem', textAlign: 'center',
              cursor: 'pointer', transition: 'all 0.3s',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10,
            }}>
              <span style={{ fontSize: 28 }}>{CAT_ICONS[cat]}</span>
              <span style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--sand)' }}>{cat}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Shop section */}
      <div id="shop-section" style={{ padding: '3rem 3rem 5rem', background: 'var(--bg)' }}>
        {/* Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', paddingBottom: '1.2rem', borderBottom: '1px solid var(--border)', flexWrap: 'wrap', gap: '1rem' }}>
          {/* Filter tabs */}
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
            {CATEGORIES.map(cat => (
              <button key={cat} onClick={() => setCategory(cat)} style={{
                fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.15em', textTransform: 'uppercase',
                padding: '7px 16px', background: category === cat ? 'var(--gold)' : 'transparent',
                color: category === cat ? 'var(--bg)' : 'var(--muted)',
                border: `1px solid ${category === cat ? 'var(--gold)' : 'var(--border)'}`,
                transition: 'all 0.25s', cursor: 'pointer',
              }}>
                {cat}
              </button>
            ))}
          </div>

          {/* Search + Sort */}
          <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg3)', border: '1px solid var(--border)', padding: '7px 12px', gap: 8 }}>
              <span style={{ color: 'var(--muted)', fontSize: 13 }}>⌕</span>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search..."
                style={{ background: 'none', border: 'none', outline: 'none', color: 'var(--cream)', fontSize: 12, width: 140, fontFamily: 'DM Sans, sans-serif' }}
              />
            </div>
            <select value={sort} onChange={e => setSort(e.target.value)} style={{
              background: 'var(--bg3)', border: '1px solid var(--border)',
              color: 'var(--sand)', padding: '7px 12px',
              fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.08em',
              outline: 'none', cursor: 'pointer',
            }}>
              <option value="featured">Featured</option>
              <option value="price-low">Price ↑</option>
              <option value="price-high">Price ↓</option>
              <option value="rating">Top Rated</option>
            </select>
          </div>
        </div>

        {/* Results count */}
        <p style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.1em', color: 'var(--muted)', marginBottom: '1.5rem' }}>
          {loading ? 'Loading...' : `${products.length} product${products.length !== 1 ? 's' : ''} found`}
        </p>

        {/* Grid */}
        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '1.5rem' }}>
            {Array(8).fill(0).map((_, i) => (
              <div key={i} style={{ height: 380 }} className="skeleton" />
            ))}
          </div>
        ) : products.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '5rem 0' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
            <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.3rem', fontStyle: 'italic', color: 'var(--muted)' }}>
              Nothing found. Even the algorithm is confused.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1.5rem' }}>
            {products.map((p, i) => (
              <div key={p.id} style={{ animation: `fadeUp 0.4s ease ${i * 0.06}s both` }}>
                <ProductCard product={p} onAdd={addToCart} />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Newsletter */}
      <div style={{
        background: 'var(--forest)', borderTop: '1px solid rgba(200,168,75,0.12)',
        borderBottom: '1px solid rgba(200,168,75,0.12)', padding: '5rem 3rem', textAlign: 'center',
      }}>
        <h2 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: 'clamp(1.5rem,3vw,2.4rem)', fontWeight: 300, color: 'var(--cream)', marginBottom: '0.5rem' }}>
          Get Notified When We <em style={{ fontStyle: 'italic', color: 'var(--gold)' }}>Overstock</em>
        </h2>
        <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1rem', fontStyle: 'italic', color: 'rgba(240,230,204,0.55)', marginBottom: '2rem' }}>
          Sales. Deals. Philosophical musings on depreciation.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', maxWidth: 460, margin: '0 auto' }}>
          <input placeholder="your@email.com" style={{
            flex: 1, background: 'rgba(20,18,16,0.6)', border: '1px solid var(--border2)',
            borderRight: 'none', color: 'var(--cream)', padding: '14px 18px',
            fontFamily: 'DM Sans, sans-serif', fontSize: 13, outline: 'none',
          }} />
          <button style={{
            background: 'var(--gold)', color: 'var(--bg)',
            fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase',
            padding: '14px 24px', flexShrink: 0,
          }}>Subscribe</button>
        </div>
      </div>

      {/* Footer */}
      <footer style={{ background: '#0c0a08', borderTop: '1px solid var(--border)', padding: '3.5rem 3rem 2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '3rem', marginBottom: '2.5rem' }}>
          <div>
            <div style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.4rem', fontStyle: 'italic', color: 'var(--gold)', marginBottom: '0.5rem' }}>Ishara</div>
            <div style={{ fontFamily: 'Cinzel, serif', fontSize: 8, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '1rem' }}>Sacred Tech Emporium</div>
            <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '0.9rem', fontStyle: 'italic', color: 'var(--muted)', lineHeight: 1.7, maxWidth: 260 }}>
              A curated portal for those who seek transcendence through next-day delivery.
            </p>
          </div>
          {[['Shop', ['Phones', 'Laptops', 'Audio', 'TVs', 'Wearables', 'Gadgets']],
            ['Help', ['Track Order', 'Returns', 'Shipping', 'FAQ', 'Contact']],
            ['Company', ['About Us', 'Blog', 'Careers', 'Privacy', 'Terms']]
          ].map(([title, links]) => (
            <div key={title}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: '1rem' }}>{title}</div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {links.map(l => (
                  <li key={l}><a href="#" style={{ fontFamily: 'DM Sans, sans-serif', fontSize: 12, color: 'var(--muted)', transition: 'color 0.2s' }}>{l}</a></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.1em', color: 'var(--muted)' }}>© 2025 Ishara Sacred Tech Emporium. Losses not included.</p>
          <div style={{ display: 'flex', gap: 8 }}>
            {['UPI', 'Visa', 'MC', 'Net'].map(p => (
              <span key={p} style={{ background: 'rgba(240,230,204,0.06)', border: '1px solid var(--border)', padding: '3px 9px', fontFamily: 'Cinzel, serif', fontSize: 9, color: 'var(--muted)' }}>{p}</span>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
