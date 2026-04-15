import { useState } from 'react';
import { useApp } from './App';
import { api } from './api';

export default function AuthPage({ onSuccess }) {
  const { toast } = useApp();
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const e = {};
    if (mode === 'signup' && !form.name.trim()) e.name = 'Name is required';
    if (!form.email.includes('@')) e.email = 'Enter a valid email';
    if (form.password.length < 6) e.password = 'Min 6 characters';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      const res = mode === 'login'
        ? await api.login(form.email, form.password)
        : await api.signup(form.name, form.email, form.password);
<<<<<<< HEAD
      toast(`Welcome, ${res.user.name}. May your cart be full and your coupons stronger.`);
=======
      toast(`Welcome, ${res.user.name}. May your cart be full and your wallet empty.`);
>>>>>>> 6f15b6f (attented enlightment)
      onSuccess(res.user);
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const field = (key, label, type = 'text', placeholder = '') => (
    <div style={{ marginBottom: '1.4rem' }}>
      <label style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'var(--muted)', display: 'block', marginBottom: 8 }}>
        {label}
      </label>
      <input
        type={type}
        value={form[key]}
        onChange={e => { setForm(f => ({ ...f, [key]: e.target.value })); setErrors(er => ({ ...er, [key]: '' })); }}
        placeholder={placeholder}
        onKeyDown={e => e.key === 'Enter' && handleSubmit()}
        style={{
          width: '100%', background: 'var(--bg3)',
          border: `1px solid ${errors[key] ? 'rgba(200,60,30,0.6)' : 'var(--border)'}`,
          color: 'var(--cream)', padding: '13px 16px',
          fontSize: 14, fontFamily: 'DM Sans, sans-serif',
          outline: 'none', transition: 'border 0.2s',
        }}
      />
      {errors[key] && <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, color: 'rgba(220,80,50,0.9)', marginTop: 5, letterSpacing: '0.08em' }}>{errors[key]}</p>}
    </div>
  );

  const funnyQuotes = [
<<<<<<< HEAD
    '"Logging in is the first step toward adding five things and buying one."',
    '"An account is just a cart with memory."',
    '"Sign up. Your wishlist deserves better organization."',
=======
    '"Logging in is the first step toward spending money you don\'t have."',
    '"An account is just a cart with memory."',
    '"Sign up. Your data is our offering."',
>>>>>>> 6f15b6f (attented enlightment)
  ];
  const quote = funnyQuotes[mode === 'login' ? 0 : 1];

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg)',
      display: 'grid', gridTemplateColumns: '1fr 1fr',
    }}>
      {/* Left panel — decorative */}
      <div style={{
        background: 'var(--bg2)', borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        padding: '4rem', position: 'relative', overflow: 'hidden',
      }}>
        {/* Rings */}
        {[300, 220, 140, 60].map(r => (
          <div key={r} style={{
            position: 'absolute', width: r, height: r,
            border: `1px solid rgba(200,168,75,${0.03 + (300 - r) / 300 * 0.07})`,
            borderRadius: '50%', top: '50%', left: '50%',
            transform: 'translate(-50%, -50%)',
          }} />
        ))}
        <div style={{ position: 'relative', zIndex: 2, textAlign: 'center' }}>
          <div style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '3.5rem', fontStyle: 'italic', color: 'var(--gold)', marginBottom: '0.5rem' }}>Ishara</div>
          <div style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.35em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '3rem' }}>Sacred Tech Emporium</div>
          <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.15rem', fontStyle: 'italic', color: 'var(--sand)', lineHeight: 1.8, maxWidth: 320 }}>
            {quote}
          </p>
          <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'center', gap: 6 }}>
            {['📱', '💻', '🎧', '⌚'].map(e => (
              <span key={e} style={{ fontSize: 24, opacity: 0.6 }}>{e}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4rem 3rem' }}>
        <div style={{ width: '100%', maxWidth: 400, animation: 'fadeUp 0.5s ease both' }}>
          {/* Mode toggle */}
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', marginBottom: '2.5rem' }}>
            {['login', 'signup'].map(m => (
              <button key={m} onClick={() => { setMode(m); setErrors({}); }} style={{
                flex: 1, background: 'none',
                fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase',
                color: mode === m ? 'var(--gold)' : 'var(--muted)',
                borderBottom: `2px solid ${mode === m ? 'var(--gold)' : 'transparent'}`,
                padding: '0 0 1rem', marginBottom: -1, transition: 'all 0.25s',
              }}>
                {m === 'login' ? 'Login' : 'Create Account'}
              </button>
            ))}
          </div>

          <h1 style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '2rem', fontWeight: 300, color: 'var(--cream)', marginBottom: '0.4rem' }}>
            {mode === 'login' ? 'Welcome back,' : 'Begin your'}
          </h1>
          <p style={{ fontFamily: 'Cormorant Garamond, serif', fontSize: '1.8rem', fontStyle: 'italic', color: 'var(--gold)', marginBottom: '2rem' }}>
            {mode === 'login' ? 'seeker.' : 'journey.'}
          </p>

          {mode === 'signup' && field('name', 'Full Name', 'text', 'Enlightened Kumar')}
          {field('email', 'Email Address', 'email', 'seeker@universe.com')}
          {field('password', 'Password', 'password', '••••••••')}

          <button
            onClick={handleSubmit}
            disabled={loading}
            style={{
              width: '100%', background: loading ? 'var(--bg4)' : 'var(--gold)',
              color: loading ? 'var(--muted)' : 'var(--bg)',
              fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', textTransform: 'uppercase',
              padding: '15px', marginBottom: '1rem', transition: 'all 0.25s',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
          >
            {loading ? (
              <>
                <span style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid var(--muted)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                Processing...
              </>
            ) : mode === 'login' ? 'Enter the Temple' : 'Join the Order'}
          </button>

          <p style={{ fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.08em', color: 'var(--muted)', textAlign: 'center' }}>
            {mode === 'login' ? "Don't have an account? " : 'Already initiated? '}
            <button onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setErrors({}); }} style={{
              background: 'none', color: 'var(--gold)', fontFamily: 'Cinzel, serif', fontSize: 10, letterSpacing: '0.08em',
              textDecoration: 'underline', textUnderlineOffset: 3,
            }}>
              {mode === 'login' ? 'Sign up' : 'Login'}
            </button>
          </p>

          <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid var(--border)', background: 'var(--bg2)' }}>
            <p style={{ fontFamily: 'Cinzel, serif', fontSize: 9, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: 6 }}>Demo credentials</p>
            <p style={{ fontFamily: 'DM Sans, sans-serif', fontSize: 12, color: 'var(--sand)' }}>any@email.com · anypassword</p>
          </div>
        </div>
      </div>
    </div>
  );
}
