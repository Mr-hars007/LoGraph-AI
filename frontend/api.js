// ─── API Base URLs ────────────────────────────────────────────────────────────
const USER_API    = "http://localhost:3001";
const ORDER_API   = "http://localhost:3002";
const PAYMENT_API = "http://localhost:3003";

const req = async (url, options = {}) => {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
};

// ─── User Service (port 3001) ─────────────────────────────────────────────────
export const userApi = {
  register: (data) =>
    req(`${USER_API}/api/users`, { method: "POST", body: JSON.stringify(data) }),

  login: (email, password) =>
    req(`${USER_API}/api/auth/login`, { method: "POST", body: JSON.stringify({ email, password }) }),

  getProfile: (userId, token) =>
    req(`${USER_API}/api/users/${userId}`, { headers: { Authorization: `Bearer ${token}` } }),

  updateProfile: (userId, data, token) =>
    req(`${USER_API}/api/users/${userId}`, { method: "PUT", body: JSON.stringify(data), headers: { Authorization: `Bearer ${token}` } }),
};

// ─── Order Service (port 3002) ────────────────────────────────────────────────
export const orderApi = {
  createOrder: (data, token) =>
    req(`${ORDER_API}/api/orders`, { method: "POST", body: JSON.stringify(data), headers: { Authorization: `Bearer ${token}` } }),

  getOrders: (userId, token) =>
    req(`${ORDER_API}/api/orders?userId=${userId}`, { headers: { Authorization: `Bearer ${token}` } }),

  getOrder: (orderId, token) =>
    req(`${ORDER_API}/api/orders/${orderId}`, { headers: { Authorization: `Bearer ${token}` } }),

  cancelOrder: (orderId, token) =>
    req(`${ORDER_API}/api/orders/${orderId}/cancel`, { method: "POST", headers: { Authorization: `Bearer ${token}` } }),
};

// ─── Payment Service (port 3003) ──────────────────────────────────────────────
export const paymentApi = {
  processPayment: (data, token) =>
    req(`${PAYMENT_API}/api/payments/process`, { method: "POST", body: JSON.stringify(data), headers: { Authorization: `Bearer ${token}` } }),

  getPaymentStatus: (txnId, token) =>
    req(`${PAYMENT_API}/api/payments/${txnId}`, { headers: { Authorization: `Bearer ${token}` } }),

  refund: (txnId, token) =>
    req(`${PAYMENT_API}/api/payments/${txnId}/refund`, { method: "POST", headers: { Authorization: `Bearer ${token}` } }),
};
