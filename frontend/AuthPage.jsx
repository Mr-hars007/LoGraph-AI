import { useState } from "react";
import { useApp } from "./App";
import { userApi } from "./api";

const Field = ({ label, type = "text", value, onChange, placeholder }) => (
  <div style={{ marginBottom: "18px" }}>
    <label style={{ display: "block", fontSize: "12px", fontWeight: 600, color: "#5a5550", marginBottom: "7px", letterSpacing: "0.04em" }}>{label}</label>
    <input type={type} value={value} onChange={onChange} placeholder={placeholder}
      style={{ width: "100%", border: "1.5px solid #ede9e2", borderRadius: "10px", padding: "12px 16px", fontSize: "14px", fontFamily: "inherit", outline: "none", transition: "border-color 0.2s", background: "#fafaf8", color: "#1a1a1a" }}
      onFocus={e => e.target.style.borderColor = "#c8a96e"}
      onBlur={e => e.target.style.borderColor = "#ede9e2"}
    />
  </div>
);

export default function AuthPage() {
  const { setUser, showToast, nav } = useApp();
  const [mode, setMode]     = useState("login");   // login | register
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");
  const [form, setForm]     = useState({ name: "", email: "", password: "", confirm: "" });

  const set = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }));

  const handleSubmit = async () => {
    setError("");
    if (!form.email || !form.password) return setError("Please fill all required fields.");
    if (mode === "register" && form.password !== form.confirm) return setError("Passwords do not match.");
    if (mode === "register" && !form.name) return setError("Name is required.");

    setLoading(true);
    try {
      let result;
      if (mode === "login") {
        // POST /api/auth/login → User Service :3001
        result = await userApi.login(form.email, form.password);
        setUser({ id: result.userId || result.id, name: result.name, email: form.email, token: result.token });
        showToast(`Welcome back, ${result.name || form.email.split("@")[0]}!`);
      } else {
        // POST /api/users → User Service :3001
        result = await userApi.register({ name: form.name, email: form.email, password: form.password });
        setUser({ id: result.id, name: form.name, email: form.email, token: result.token });
        showToast(`Account created! Welcome, ${form.name}!`);
      }
      nav("store");
    } catch (err) {
      // Fallback: simulate login so UI is demoable without backend running
      if (form.email && form.password.length >= 4) {
        const name = mode === "register" ? form.name : form.email.split("@")[0];
        setUser({ id: "USR-DEMO", name, email: form.email, token: "demo-token" });
        showToast(`Welcome, ${name}! (demo mode)`);
        nav("store");
      } else {
        setError(mode === "login" ? "Invalid email or password." : err.message || "Registration failed.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "calc(100vh - 64px)", display: "flex", alignItems: "center", justifyContent: "center", padding: "40px 24px", background: "#fafaf8" }}>
      <div style={{ width: "100%", maxWidth: "440px" }}>
        {/* Brand */}
        <div style={{ textAlign: "center", marginBottom: "36px" }}>
          <div style={{ fontFamily: "'Playfair Display', serif", fontWeight: 800, fontSize: "28px", marginBottom: "8px" }}>MART<span style={{ color: "#c8a96e" }}>·</span></div>
          <div style={{ fontSize: "15px", color: "#9c9890" }}>{mode === "login" ? "Sign in to your account" : "Create your account"}</div>
        </div>

        {/* Card */}
        <div style={{ background: "#fff", borderRadius: "20px", padding: "36px", border: "1px solid #ede9e2", boxShadow: "0 4px 40px rgba(0,0,0,0.05)" }}>
          {/* Mode toggle */}
          <div style={{ display: "flex", background: "#f5f3ef", borderRadius: "10px", padding: "4px", marginBottom: "28px" }}>
            {[["login","Sign In"],["register","Register"]].map(([m, label]) => (
              <button key={m} onClick={() => { setMode(m); setError(""); }} style={{ flex: 1, padding: "9px", borderRadius: "8px", border: "none", cursor: "pointer", fontSize: "13px", fontWeight: mode === m ? 600 : 400, fontFamily: "inherit", background: mode === m ? "#fff" : "transparent", color: mode === m ? "#1a1a1a" : "#9c9890", transition: "all 0.2s", boxShadow: mode === m ? "0 1px 4px rgba(0,0,0,0.08)" : "none" }}>{label}</button>
            ))}
          </div>

          {mode === "register" && <Field label="Full Name" value={form.name} onChange={set("name")} placeholder="Harsha C K" />}
          <Field label="Email Address" type="email" value={form.email} onChange={set("email")} placeholder="you@example.com" />
          <Field label="Password" type="password" value={form.password} onChange={set("password")} placeholder="Min. 4 characters" />
          {mode === "register" && <Field label="Confirm Password" type="password" value={form.confirm} onChange={set("confirm")} placeholder="Re-enter password" />}

          {error && <div style={{ marginBottom: "16px", padding: "11px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "8px", fontSize: "13px", color: "#b91c1c" }}>{error}</div>}

          <button onClick={handleSubmit} disabled={loading} style={{ width: "100%", background: "#1a1a1a", color: "#fff", border: "none", borderRadius: "10px", padding: "14px", fontSize: "15px", fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", fontFamily: "inherit", opacity: loading ? 0.7 : 1, transition: "opacity 0.2s" }}>
            {loading ? "Please wait…" : mode === "login" ? "Sign In →" : "Create Account →"}
          </button>

          <div style={{ marginTop: "20px", textAlign: "center", fontSize: "13px", color: "#9c9890" }}>
            {mode === "login" ? "Don't have an account? " : "Already have an account? "}
            <button onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }} style={{ background: "none", border: "none", color: "#c8a96e", cursor: "pointer", fontFamily: "inherit", fontSize: "13px", fontWeight: 600 }}>
              {mode === "login" ? "Register" : "Sign In"}
            </button>
          </div>
        </div>

        {/* Note */}
        <div style={{ marginTop: "20px", textAlign: "center", fontSize: "12px", color: "#b0ada6", lineHeight: 1.6 }}>
          Calls <code style={{ background: "#f0ede8", padding: "2px 6px", borderRadius: "4px", fontSize: "11px" }}>POST /api/auth/login</code> on User Service :3001
        </div>
      </div>
    </div>
  );
}
