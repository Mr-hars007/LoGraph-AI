// ─── Unified API Base URL ───────────────────────────────────────────────────
const API_BASE = "http://localhost:5005";

const req = async (url, options = {}) => {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
};

// ─── User Endpoints ──────────────────────────────────────────────────────────
export const userApi = {
  register: (data) =>
    req(`${API_BASE}/users`, { method: "POST", body: JSON.stringify(data) }),

  login: (email, password) =>
    req(`${API_BASE}/users/login`, { method: "POST", body: JSON.stringify({ email, password }) }),

  getProfile: (userId) =>
    req(`${API_BASE}/users/${userId}`),

  updateProfile: (userId, data) =>
    req(`${API_BASE}/users/${userId}`, { method: "PUT", body: JSON.stringify(data) }),
};

// ─── Order Endpoints ─────────────────────────────────────────────────────────
export const orderApi = {
  createOrder: (data) =>
    req(`${API_BASE}/orders`, { method: "POST", body: JSON.stringify(data) }),

  getOrders: (userId) =>
    req(`${API_BASE}/orders?userId=${userId}`),

  getOrder: (orderId) =>
    req(`${API_BASE}/orders/${orderId}`),

  cancelOrder: (orderId) =>
    req(`${API_BASE}/orders/${orderId}/cancel`, { method: "POST" }),
};

// ─── Payment Endpoints ───────────────────────────────────────────────────────
export const paymentApi = {
  processPayment: (data) =>
    req(`${API_BASE}/pay`, { method: "POST", body: JSON.stringify(data) }),

  getPaymentStatus: (txnId) =>
    req(`${API_BASE}/payments/${txnId}`),

  refund: (txnId) =>
    req(`${API_BASE}/payments/${txnId}/refund`, { method: "POST" }),
};

// ─── Graph and Prediction Endpoints ──────────────────────────────────────────
export const systemApi = {
  getGraph: () => req(`${API_BASE}/graph`),
  getPredictions: () => req(`${API_BASE}/predictions`),
  uploadData: (formData) => 
    fetch(`${API_BASE}/upload-data`, { method: "POST", body: formData }).then(res => res.json()),
};
