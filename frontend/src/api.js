// ─── Mock API ───────────────────────────────────────────────────────────────
// Simulates network delay, auth, cart, orders.
// Replace fetch() calls with real endpoints when backend is ready.

const delay = (ms = 400) => new Promise(r => setTimeout(r, ms));

// ── Product catalogue ────────────────────────────────────────────────────────
export const PRODUCTS = [
<<<<<<< HEAD
  { id: 1,  name: 'Samsang Galaxxy S67 Ultra',     category: 'Phones',    price: 89999,  oldPrice: 109999, rating: 4.2, reviews: 3201, badge: 'best',    emoji: '📱', desc: 'Flagship flex. Impresses everyone including your budget tracker. Has a 200MP camera for ultra-detailed photos.' },
  { id: 2,  name: 'iPhoney 15 Pro Maxx Plus',       category: 'Phones',    price: 134999, oldPrice: null,   rating: 4.8, reviews: 8102, badge: 'new',     emoji: '📱', desc: 'Titanium frame, USB-C after 15 years of stubbornness. Comes with one (1) courage.' },
  { id: 3,  name: 'Nothingburger Phone (2)',         category: 'Phones',    price: 29999,  oldPrice: 34999,  rating: 4.5, reviews: 1543, badge: 'sale',    emoji: '📱', desc: 'Transparent back so you can see the anxiety inside. LEDs go brrr.' },
  { id: 4,  name: 'Macbuk Air M67 Chip',             category: 'Laptops',   price: 119990, oldPrice: null,   rating: 4.9, reviews: 5421, badge: 'best',    emoji: '💻', desc: 'Battery lasts 18 hours. The chip is so fast it finishes your procrastination before you do.' },
  { id: 5,  name: 'Delll XPS 15 (dramatic fan mode)', category: 'Laptops', price: 159999, oldPrice: 179999, rating: 3.9, reviews: 2100, badge: 'sale',    emoji: '💻', desc: 'Premium build. Runs warm when pushed. Thermal design: ambitious.' },
  { id: 6,  name: 'Lenovo ThinkPad X1 Brrr',        category: 'Laptops',   price: 139999, oldPrice: null,   rating: 4.7, reviews: 1980, badge: null,      emoji: '💻', desc: 'The business classic. Legendary trackpoint included. No further questions.' },
  { id: 7,  name: 'Sono WH-1000XM6767',             category: 'Audio',     price: 29990,  oldPrice: 34999,  rating: 4.8, reviews: 9872, badge: 'best',    emoji: '🎧', desc: 'ANC so powerful it cancels your will to interact with humans. 30hr battery of pure silence.' },
  { id: 8,  name: 'AirPods Maxx (mortgage required)', category: 'Audio',   price: 59900,  oldPrice: null,   rating: 4.3, reviews: 4310, badge: null,      emoji: '🎧', desc: 'Spatial audio. Your music is everywhere except inside your skull where it belongs.' },
  { id: 9,  name: 'Bose QuietComfort Ultra Fancy',  category: 'Audio',     price: 34990,  oldPrice: 39990,  rating: 4.6, reviews: 3100, badge: 'sale',    emoji: '🎧', desc: 'Softer than clouds. Cozy fit. ANC so good the coffee shop turns into a calm bubble.' },
  { id: 10, name: 'Samsang 4K QLED Thicc TV',       category: 'TVs',       price: 79999,  oldPrice: 99999,  rating: 4.4, reviews: 2200, badge: 'sale',    emoji: '📺', desc: '65 inches of regret. HDR 4000. Has more ports than your router and more apps than your phone.' },
  { id: 11, name: 'LGee C3 OLED (send help)',        category: 'TVs',       price: 149999, oldPrice: null,   rating: 4.9, reviews: 6700, badge: 'best',    emoji: '📺', desc: 'Perfect blacks because the pixels literally turn off. Like your social life after buying this.' },
  { id: 12, name: 'Projector That Projects Vibes',  category: 'TVs',       price: 44999,  oldPrice: 52999,  rating: 4.1, reviews: 870,  badge: null,      emoji: '📽', desc: '4K laser. Mount it on the ceiling and contemplate existence while watching Netflix.' },
  { id: 13, name: 'Xiaohomi Watch S67',              category: 'Wearables', price: 19999,  oldPrice: 24999,  rating: 4.3, reviews: 1560, badge: 'new',     emoji: '⌚', desc: 'Tracks your steps, sleep, stress and slowly your will to live. 14 day battery.' },
  { id: 14, name: 'Apple iWatch Ultra 2 (budget trembles)', category: 'Wearables', price: 89900, oldPrice: null, rating: 4.7, reviews: 3200, badge: 'new',     emoji: '⌚', desc: 'Titanium. Sapphire. Depth gauge for diving. You might only dive into weekend plans, but it is still titanium.' },
  { id: 15, name: 'Fitbit Charge 6 (legacy edition)',   category: 'Wearables', price: 14999,  oldPrice: 18999,  rating: 4.0, reviews: 2100, badge: 'sale',    emoji: '⌚', desc: 'Now in the Google era. Tracks your steps, sleep, and your streak obsession.' },
  { id: 16, name: 'Raspberry Pi 5 (unavailable)',   category: 'Gadgets',   price: 7499,   oldPrice: null,   rating: 4.9, reviews: 11000, badge: 'best',   emoji: '🖥', desc: 'Sold out everywhere. You want one badly. You will never use it. It will collect dust gloriously.' },
  { id: 17, name: 'GoPuru Hero 12 Blakk',           category: 'Gadgets',   price: 39999,  oldPrice: 44999,  rating: 4.6, reviews: 4200, badge: 'sale',    emoji: '📷', desc: 'Waterproof. Shockproof. Proof that you are an adventurer (footage: grocery runs).' },
  { id: 18, name: 'Dyzon V15 Dust Wizard',          category: 'Gadgets',   price: 54990,  oldPrice: null,   rating: 4.8, reviews: 3800, badge: 'new',     emoji: '🌀', desc: 'Cleans with authority. 240 AW of pure vacuum power. Your carpet will look suspiciously new.' },
=======
  { id: 1,  name: 'Samsang Galaxxy S69 Ultra',     category: 'Phones',    price: 89999,  oldPrice: 109999, rating: 4.2, reviews: 3201, badge: 'best',    emoji: '📱', desc: 'Flagship killer. Kills everything including your savings. Has 200MP camera for photos you will never look at again.' },
  { id: 2,  name: 'iPhoney 15 Pro Maxx Plus',       category: 'Phones',    price: 134999, oldPrice: null,   rating: 4.8, reviews: 8102, badge: 'new',     emoji: '📱', desc: 'Titanium frame, USB-C after 15 years of stubbornness. Comes with one (1) courage.' },
  { id: 3,  name: 'Nothingburger Phone (2)',         category: 'Phones',    price: 29999,  oldPrice: 34999,  rating: 4.5, reviews: 1543, badge: 'sale',    emoji: '📱', desc: 'Transparent back so you can see the anxiety inside. LEDs go brrr.' },
  { id: 4,  name: 'Macbuk Air M69 Chip',             category: 'Laptops',   price: 119990, oldPrice: null,   rating: 4.9, reviews: 5421, badge: 'best',    emoji: '💻', desc: 'Battery lasts 18 hours. The chip is so fast it finishes your procrastination before you do.' },
  { id: 5,  name: 'Delll XPS 15 (explodes sometimes)', category: 'Laptops', price: 159999, oldPrice: 179999, rating: 3.9, reviews: 2100, badge: 'sale',    emoji: '💻', desc: 'Premium build. Runs hot enough to cook eggs. Thermal design: bold.' },
  { id: 6,  name: 'Lenovo ThinkPad X1 Brrr',        category: 'Laptops',   price: 139999, oldPrice: null,   rating: 4.7, reviews: 1980, badge: null,      emoji: '💻', desc: 'The business machine. Red nipple included. No further questions.' },
  { id: 7,  name: 'Sono WH-1000XM6969',             category: 'Audio',     price: 29990,  oldPrice: 34999,  rating: 4.8, reviews: 9872, badge: 'best',    emoji: '🎧', desc: 'ANC so powerful it cancels your will to interact with humans. 30hr battery of pure silence.' },
  { id: 8,  name: 'AirPods Maxx (mortgage required)', category: 'Audio',   price: 59900,  oldPrice: null,   rating: 4.3, reviews: 4310, badge: null,      emoji: '🎧', desc: 'Spatial audio. Your music is everywhere except inside your skull where it belongs.' },
  { id: 9,  name: 'Bose QuietComfort Ultra Fancy',  category: 'Audio',     price: 34990,  oldPrice: 39990,  rating: 4.6, reviews: 3100, badge: 'sale',    emoji: '🎧', desc: 'Softer than clouds. Warmer than your ex. ANC that deletes entire families in coffee shops.' },
  { id: 10, name: 'Samsang 4K QLED Thicc TV',       category: 'TVs',       price: 79999,  oldPrice: 99999,  rating: 4.4, reviews: 2200, badge: 'sale',    emoji: '📺', desc: '65 inches of regret. HDR 4000. Has more ports than your router and more apps than your phone.' },
  { id: 11, name: 'LGee C3 OLED (send help)',        category: 'TVs',       price: 149999, oldPrice: null,   rating: 4.9, reviews: 6700, badge: 'best',    emoji: '📺', desc: 'Perfect blacks because the pixels literally turn off. Like your social life after buying this.' },
  { id: 12, name: 'Projector That Projects Vibes',  category: 'TVs',       price: 44999,  oldPrice: 52999,  rating: 4.1, reviews: 870,  badge: null,      emoji: '📽', desc: '4K laser. Mount it on the ceiling and contemplate existence while watching Netflix.' },
  { id: 13, name: 'Xiaohomi Watch S69',              category: 'Wearables', price: 19999,  oldPrice: 24999,  rating: 4.3, reviews: 1560, badge: 'new',     emoji: '⌚', desc: 'Tracks your steps, sleep, stress and slowly your will to live. 14 day battery.' },
  { id: 14, name: 'Apple iWatch Ultra 2 (sold kidney)', category: 'Wearables', price: 89900, oldPrice: null, rating: 4.7, reviews: 3200, badge: 'new',     emoji: '⌚', desc: 'Titanium. Sapphire. Depth gauge for diving. You will never dive. It is still titanium.' },
  { id: 15, name: 'Fitbit Charge 6 (RIP Fitbit)',   category: 'Wearables', price: 14999,  oldPrice: 18999,  rating: 4.0, reviews: 2100, badge: 'sale',    emoji: '⌚', desc: 'Now a Google product. Tracks your data and probably sends it to a server farm in Iowa.' },
  { id: 16, name: 'Raspberry Pi 5 (unavailable)',   category: 'Gadgets',   price: 7499,   oldPrice: null,   rating: 4.9, reviews: 11000, badge: 'best',   emoji: '🖥', desc: 'Sold out everywhere. You want one badly. You will never use it. It will collect dust gloriously.' },
  { id: 17, name: 'GoPuru Hero 12 Blakk',           category: 'Gadgets',   price: 39999,  oldPrice: 44999,  rating: 4.6, reviews: 4200, badge: 'sale',    emoji: '📷', desc: 'Waterproof. Shockproof. Proof that you are an adventurer (footage: grocery runs).' },
  { id: 18, name: 'Dyzon V15 Suck Master',          category: 'Gadgets',   price: 54990,  oldPrice: null,   rating: 4.8, reviews: 3800, badge: 'new',     emoji: '🌀', desc: 'Sucks with authority. 240 AW of pure vacuum. Your carpet will develop separation anxiety.' },
>>>>>>> 6f15b6f (attented enlightment)
];

export const CATEGORIES = ['All', 'Phones', 'Laptops', 'Audio', 'TVs', 'Wearables', 'Gadgets'];

// ── Auth ─────────────────────────────────────────────────────────────────────
let _currentUser = null;

export const api = {
  // Auth
  login: async (email, password) => {
    await delay(600);
    if (!email.includes('@')) throw new Error('Invalid email address');
    if (password.length < 6) throw new Error('Password too short');
    _currentUser = { email, name: email.split('@')[0], id: 'usr_' + Date.now() };
    return { user: _currentUser, token: 'mock_tok_' + Date.now() };
  },

  signup: async (name, email, password) => {
    await delay(800);
    if (!email.includes('@')) throw new Error('Invalid email address');
    if (password.length < 6) throw new Error('Password must be at least 6 characters');
    _currentUser = { email, name, id: 'usr_' + Date.now() };
    return { user: _currentUser, token: 'mock_tok_' + Date.now() };
  },

  logout: async () => {
    await delay(200);
    _currentUser = null;
    return { success: true };
  },

  getUser: () => _currentUser,

  // Products
  getProducts: async (filters = {}) => {
    await delay(300);
    let list = [...PRODUCTS];
    if (filters.category && filters.category !== 'All') {
      list = list.filter(p => p.category === filters.category);
    }
    if (filters.search) {
      const q = filters.search.toLowerCase();
      list = list.filter(p => p.name.toLowerCase().includes(q) || p.category.toLowerCase().includes(q));
    }
    if (filters.sort === 'price-low') list.sort((a, b) => a.price - b.price);
    if (filters.sort === 'price-high') list.sort((a, b) => b.price - a.price);
    if (filters.sort === 'rating') list.sort((a, b) => b.rating - a.rating);
    return list;
  },

  getProduct: async (id) => {
    await delay(200);
    return PRODUCTS.find(p => p.id === id) || null;
  },

  // Orders
  placeOrder: async (cart, address, payment) => {
    await delay(1200);
    const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
    return {
      id: 'ORD-' + Math.random().toString(36).slice(2, 8).toUpperCase(),
      items: cart,
      total,
      address,
      payment,
      status: 'confirmed',
      placedAt: new Date().toISOString(),
    };
  },

  getOrders: async () => {
    await delay(400);
    return [
      {
        id: 'ORD-AX7K2M',
        items: [{ ...PRODUCTS[0], qty: 1 }, { ...PRODUCTS[6], qty: 2 }],
        total: PRODUCTS[0].price + PRODUCTS[6].price * 2,
        status: 'delivered',
        placedAt: '2025-03-12T10:30:00Z',
      },
      {
        id: 'ORD-BZ9P1Q',
        items: [{ ...PRODUCTS[3], qty: 1 }],
        total: PRODUCTS[3].price,
        status: 'shipped',
        placedAt: '2025-04-01T08:15:00Z',
      },
      {
        id: 'ORD-CW4R8N',
        items: [{ ...PRODUCTS[10], qty: 1 }],
        total: PRODUCTS[10].price,
        status: 'processing',
        placedAt: '2025-04-10T14:00:00Z',
      },
    ];
  },
};

export const fmt = (n) =>
  '₹' + Number(n).toLocaleString('en-IN');
