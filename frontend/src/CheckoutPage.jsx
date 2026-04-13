import { useState } from 'react';
import { useApp } from './App';
import { api, fmt } from './api';

const STEPS = ['Address', 'Payment', 'Review'];

function StepIndicator({ current }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0, marginBottom: '3rem' }}>
      {STEPS.map((s, i) => (
        <div key={s} style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
            <div style={{
              width: 34, height: 34, borderRadius: '50%',
              border: `1px solid ${i <= current ? 'var(--gold)' : 'var(--border)'}`,
              background: i < current ? 'var(--gold)' : 'transparent',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: 'Cinzel, serif', fontSize: 11,
              color: i < current ? 'var(--bg)' : i === current ? 'var(--gold)' : 'var(--muted)',
              transition: 'all 0.3s',
            }}>
              {i < current ? '✓' : i + 1}
            </div>
            <span style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.15em', textTransform: 'uppercase', color: i === current ? 'var(--gold)' : 'var(--muted)' }}>
              {s}
            </span>
          </div>
          {i < STEPS.length - 1 && (
            <div style={{ width: 80, height: 1, background: i < current ? 'var(--gold)' : 'var(--border)', margin: '0 12px', marginBottom: 22, transition: 'background 0.3s' }} />
          )}
        </div>
      ))}
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', placeholder = '' }) {
  return (
    <div style={{ marginBottom: '1.2rem' }}>
      <label style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)', display: 'block', marginBottom: 6 }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: '100%', background: 'var(--bg3)',
          border: '1px solid var(--border)', color: 'var(--cream)',
          padding: '12px 14px', fontSize: 13,
          fontFamily: 'DM Sans, sans-serif', outline: 'none',
        }}
      />
    </div>
  );
}

function AddressStep({ data, onChange, onNext }) {
  return (
    <div>
      <h2 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.8rem', fontWeight: 300, color: 'var(--cream)', marginBottom: '0.3rem' }}>Delivery Address</h2>
      <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1rem', fontStyle: 'italic', color: 'var(--muted)', marginBottom: '2rem' }}>Where shall we dispatch your material desires?</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 1.2rem' }}>
        <Field label="Full Name" value={data.name} onChange={v => onChange('name', v)} placeholder="Enlightened Kumar" />
        <Field label="Phone" value={data.phone} onChange={v => onChange('phone', v)} placeholder="+91 98765 43210" type="tel" />
      </div>
      <Field label="Address Line 1" value={data.line1} onChange={v => onChange('line1', v)} placeholder="123 Nirvana Street" />
      <Field label="Address Line 2 (optional)" value={data.line2} onChange={v => onChange('line2', v)} placeholder="Apt 4B, Karma Complex" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0 1.2rem' }}>
        <Field label="City" value={data.city} onChange={v => onChange('city', v)} placeholder="Bangalore" />
        <Field label="State" value={data.state} onChange={v => onChange('state', v)} placeholder="Karnataka" />
        <Field label="PIN Code" value={data.pin} onChange={v => onChange('pin', v)} placeholder="560001" />
      </div>
      <button onClick={onNext} style={{
        marginTop: '1rem', background: 'var(--gold)', color: 'var(--bg)',
        fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase',
        padding: '14px 32px', border: 'none', transition: 'background 0.25s',
      }}>
        Continue to Payment →
      </button>
    </div>
  );
}

const PAYMENT_METHODS = [
  { id: 'upi',  label: 'UPI',          icon: '⚡', desc: 'GPay, PhonePe, Paytm, BHIM' },
  { id: 'card', label: 'Card',         icon: '💳', desc: 'Credit or Debit Card' },
  { id: 'cod',  label: 'Cash on Delivery', icon: '💰', desc: 'Pay when it arrives (hopefully)' },
  { id: 'emi',  label: 'EMI',          icon: '📆', desc: 'No-cost EMI on select cards' },
];

function PaymentStep({ data, onChange, onNext, onBack }) {
  return (
    <div>
      <h2 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.8rem', fontWeight: 300, color: 'var(--cream)', marginBottom: '0.3rem' }}>Payment</h2>
      <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1rem', fontStyle: 'italic', color: 'var(--muted)', marginBottom: '2rem' }}>The moment of reckoning. Choose your sacrifice.</p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', marginBottom: '2rem' }}>
        {PAYMENT_METHODS.map(m => (
          <button key={m.id} onClick={() => onChange('method', m.id)} style={{
            display: 'flex', alignItems: 'center', gap: 16, padding: '1.2rem 1.4rem',
            background: data.method === m.id ? 'rgba(200,168,75,0.08)' : 'var(--bg3)',
            border: `1px solid ${data.method === m.id ? 'var(--border2)' : 'var(--border)'}`,
            cursor: 'pointer', transition: 'all 0.25s', textAlign: 'left', width: '100%',
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: '50%',
              border: `1px solid ${data.method === m.id ? 'var(--gold)' : 'var(--border)'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0,
            }}>{m.icon}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.12em', color: data.method === m.id ? 'var(--gold)' : 'var(--cream)', marginBottom: 2 }}>{m.label}</div>
              <div style={{ fontFamily: 'DM Sans, sans-serif', fontSize: 12, color: 'var(--muted)' }}>{m.desc}</div>
            </div>
            <div style={{
              width: 18, height: 18, borderRadius: '50%',
              border: `1px solid ${data.method === m.id ? 'var(--gold)' : 'var(--border)'}`,
              background: data.method === m.id ? 'var(--gold)' : 'transparent',
              flexShrink: 0,
            }} />
          </button>
        ))}
      </div>

      {data.method === 'card' && (
        <div style={{ padding: '1.5rem', border: '1px solid var(--border)', background: 'var(--bg2)', marginBottom: '1.5rem', animation: 'fadeUp 0.3s ease' }}>
          <Field label="Card Number" value={data.cardNum || ''} onChange={v => onChange('cardNum', v)} placeholder="4242 4242 4242 4242" />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 1.2rem' }}>
            <Field label="Expiry" value={data.expiry || ''} onChange={v => onChange('expiry', v)} placeholder="MM/YY" />
            <Field label="CVV" value={data.cvv || ''} onChange={v => onChange('cvv', v)} placeholder="•••" type="password" />
          </div>
          <Field label="Name on Card" value={data.cardName || ''} onChange={v => onChange('cardName', v)} placeholder="A. Kumar" />
        </div>
      )}

      {data.method === 'upi' && (
        <div style={{ padding: '1.5rem', border: '1px solid var(--border)', background: 'var(--bg2)', marginBottom: '1.5rem', animation: 'fadeUp 0.3s ease' }}>
          <Field label="UPI ID" value={data.upiId || ''} onChange={v => onChange('upiId', v)} placeholder="seeker@upi" />
        </div>
      )}

      <div style={{ display: 'flex', gap: '1rem' }}>
        <button onClick={onBack} style={{
          background: 'transparent', color: 'var(--muted)',
          border: '1px solid var(--border)', fontFamily: 'Cinzel, serif',
          fontSize: 11, letterSpacing: '0.15em', textTransform: 'uppercase', padding: '14px 24px',
        }}>← Back</button>
        <button onClick={onNext} style={{
          flex: 1, background: 'var(--gold)', color: 'var(--bg)',
          fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase',
          padding: '14px 32px', border: 'none',
        }}>Review Order →</button>
      </div>
    </div>
  );
}

function ReviewStep({ cart, address, payment, onBack, onPlace, loading }) {
  const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
  const shipping = total >= 999 ? 0 : 99;
  const methodLabel = PAYMENT_METHODS.find(m => m.id === payment.method)?.label || payment.method;

  return (
    <div>
      <h2 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.8rem', fontWeight: 300, color: 'var(--cream)', marginBottom: '0.3rem' }}>Review Order</h2>
      <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1rem', fontStyle: 'italic', color: 'var(--muted)', marginBottom: '2rem' }}>Last chance to contemplate your choices.</p>

      {/* Items */}
      <div style={{ border: '1px solid var(--border)', marginBottom: '1.5rem', overflow: 'hidden' }}>
        {cart.map((item, i) => (
          <div key={item.id} style={{
            display: 'flex', gap: 14, padding: '1rem 1.2rem',
            borderBottom: i < cart.length - 1 ? '1px solid var(--border)' : 'none',
          }}>
            <span style={{ fontSize: 32, flexShrink: 0 }}>{item.emoji}</span>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: 13, color: 'var(--cream)', marginBottom: 3 }}>{item.name}</p>
              <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, color: 'var(--muted)', letterSpacing: '0.1em' }}>Qty: {item.qty}</p>
            </div>
            <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.1rem', color: 'var(--gold)' }}>
              {fmt(item.price * item.qty)}
            </span>
          </div>
        ))}
      </div>

      {/* Summary grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ padding: '1.2rem', background: 'var(--bg2)', border: '1px solid var(--border)' }}>
          <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: 8 }}>Delivery To</p>
          <p style={{ fontSize: 13, color: 'var(--cream)', lineHeight: 1.5 }}>{address.name}</p>
          <p style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.5 }}>{address.line1}{address.line2 ? ', ' + address.line2 : ''}</p>
          <p style={{ fontSize: 12, color: 'var(--muted)' }}>{address.city}, {address.state} — {address.pin}</p>
        </div>
        <div style={{ padding: '1.2rem', background: 'var(--bg2)', border: '1px solid var(--border)' }}>
          <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: 8 }}>Payment</p>
          <p style={{ fontSize: 13, color: 'var(--cream)' }}>{methodLabel}</p>
          {payment.upiId && <p style={{ fontSize: 12, color: 'var(--muted)' }}>{payment.upiId}</p>}
          {payment.cardNum && <p style={{ fontSize: 12, color: 'var(--muted)' }}>•••• {payment.cardNum.slice(-4)}</p>}
        </div>
      </div>

      {/* Totals */}
      <div style={{ border: '1px solid var(--border)', padding: '1.2rem', marginBottom: '1.5rem' }}>
        {[['Subtotal', fmt(total)], ['Shipping', shipping === 0 ? 'Free' : fmt(shipping)], ['Taxes (GST 18%)', fmt(Math.round(total * 0.18))]].map(([k, v]) => (
          <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border)' }}>
            <span style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)' }}>{k}</span>
            <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1rem', color: 'var(--sand)' }}>{v}</span>
          </div>
        ))}
        <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '1rem' }}>
          <span style={{ fontFamily: 'Cinzel, serif', fontSize: 12, letterSpacing: '0.15em', textTransform: 'uppercase', color: 'var(--cream)' }}>Total</span>
          <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.5rem', color: 'var(--gold)' }}>
            {fmt(total + shipping + Math.round(total * 0.18))}
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1rem' }}>
        <button onClick={onBack} style={{
          background: 'transparent', color: 'var(--muted)',
          border: '1px solid var(--border)', fontFamily: 'Cinzel, serif',
          fontSize: 11, letterSpacing: '0.15em', textTransform: 'uppercase', padding: '14px 24px',
        }}>← Back</button>
        <button onClick={onPlace} disabled={loading} style={{
          flex: 1, background: loading ? 'var(--bg4)' : 'var(--gold)',
          color: loading ? 'var(--muted)' : 'var(--bg)',
          fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase',
          padding: '14px 32px', border: 'none', transition: 'all 0.25s',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
        }}>
          {loading ? (
            <>
              <span style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid var(--muted)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
              Manifesting Order...
            </>
          ) : 'Place Order ✓'}
        </button>
      </div>
    </div>
  );
}

export default function CheckoutPage({ onComplete }) {
  const { cart, user, setPage } = useApp();
  const [step, setStep] = useState(0);
  const [address, setAddress] = useState({ name: user?.name || '', phone: '', line1: '', line2: '', city: '', state: '', pin: '' });
  const [payment, setPayment] = useState({ method: 'upi', upiId: '', cardNum: '', expiry: '', cvv: '', cardName: '' });
  const [loading, setLoading] = useState(false);

  const setAddr = (k, v) => setAddress(a => ({ ...a, [k]: v }));
  const setPay = (k, v) => setPayment(p => ({ ...p, [k]: v }));

  const placeOrder = async () => {
    setLoading(true);
    try {
      const order = await api.placeOrder(cart, address, payment);
      onComplete(order);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (cart.length === 0) {
    return (
      <div style={{ minHeight: '80vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1.5rem', padding: '4rem' }}>
        <div style={{ fontSize: 64 }}>🛒</div>
        <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.5rem', fontStyle: 'italic', color: 'var(--muted)', textAlign: 'center' }}>
          Your cart is empty.<br />The universe provides, but you must add items first.
        </p>
        <button onClick={() => setPage('store')} style={{
          background: 'var(--gold)', color: 'var(--bg)',
          fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase',
          padding: '13px 28px', border: 'none',
        }}>Back to Store</button>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', padding: '4rem 3rem' }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <p style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.3em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: 8 }}>Checkout</p>
        </div>
        <StepIndicator current={step} />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '2.5rem', alignItems: 'start' }}>
          {/* Form */}
          <div style={{ animation: 'fadeUp 0.4s ease both' }}>
            {step === 0 && <AddressStep data={address} onChange={setAddr} onNext={() => setStep(1)} />}
            {step === 1 && <PaymentStep data={payment} onChange={setPay} onNext={() => setStep(2)} onBack={() => setStep(0)} />}
            {step === 2 && <ReviewStep cart={cart} address={address} payment={payment} onBack={() => setStep(1)} onPlace={placeOrder} loading={loading} />}
          </div>

          {/* Order summary sidebar */}
          <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', padding: '1.5rem', position: 'sticky', top: '6rem' }}>
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--gold)', marginBottom: '1.2rem' }}>Order Summary</p>
            {cart.map(item => (
              <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 20 }}>{item.emoji}</span>
                  <div>
                    <p style={{ fontSize: 12, color: 'var(--cream)', lineHeight: 1.3 }}>{item.name.slice(0, 22)}…</p>
                    <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, color: 'var(--muted)' }}>×{item.qty}</p>
                  </div>
                </div>
                <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1rem', color: 'var(--sand)' }}>{fmt(item.price * item.qty)}</span>
              </div>
            ))}
            <div style={{ paddingTop: '1rem', display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontFamily: 'Cinzel, serif', fontSize: 11, color: 'var(--muted)' }}>Total</span>
              <span style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.3rem', color: 'var(--gold)' }}>
                {fmt(cart.reduce((s, i) => s + i.price * i.qty, 0))}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
