let token = localStorage.getItem("token");

// DOM Elements
const authSection = document.getElementById("auth-section");
const dashboardSection = document.getElementById("dashboard-section");
const navUserInfo = document.getElementById("nav-user-info");
const navUsername = document.getElementById("nav-username");
const logoutBtn = document.getElementById("logout-btn");

const tabLogin = document.getElementById("tab-login");
const tabSignup = document.getElementById("tab-signup");
const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");
const authError = document.getElementById("auth-error");

const stockSearchInput = document.getElementById("stock-search-input");
const searchResults = document.getElementById("search-results");
const orderForm = document.getElementById("order-form");
const orderSymbol = document.getElementById("order-symbol");
const orderQty = document.getElementById("order-qty");
const orderFeedback = document.getElementById("order-feedback");

// ---------------- Helpers & API ---------------- //

async function api(url, options = {}) {
  const headers = options.headers || {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    logout();
    throw new Error("Session expired. Please log in again.");
  }
  return response;
}

const fmt = (num) => Number(num).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// ---------------- Auth Logic ---------------- //

tabLogin.onclick = () => {
  tabLogin.classList.add("active");
  tabSignup.classList.remove("active");
  loginForm.classList.remove("hidden");
  signupForm.classList.add("hidden");
  authError.textContent = "";
};

tabSignup.onclick = () => {
  tabSignup.classList.add("active");
  tabLogin.classList.remove("active");
  signupForm.classList.remove("hidden");
  loginForm.classList.add("hidden");
  authError.textContent = "";
};

loginForm.onsubmit = async (e) => {
  e.preventDefault();
  authError.textContent = "";

  // OAuth2 expects x-www-form-urlencoded
  const formData = new URLSearchParams();
  formData.append("username", document.getElementById("login-username").value);
  formData.append("password", document.getElementById("login-password").value);

  const res = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    authError.textContent = data.detail || "Login failed.";
    return;
  }

  token = data.access_token;
  localStorage.setItem("token", token);
  initApp();
};

signupForm.onsubmit = async (e) => {
  e.preventDefault();
  authError.textContent = "";

  const payload = {
    username: document.getElementById("signup-username").value,
    email: document.getElementById("signup-email").value,
    password: document.getElementById("signup-password").value,
  };

  const res = await fetch("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    authError.textContent = data.detail || "Sign up failed.";
    return;
  }

  // Auto switch to login
  alert("Account created! Please log in.");
  tabLogin.click();
};

function logout() {
  token = null;
  localStorage.removeItem("token");
  navUserInfo.classList.add("hidden");
  dashboardSection.classList.add("hidden");
  authSection.classList.remove("hidden");
}
logoutBtn.onclick = logout;

// ---------------- Stock Search ---------------- //

let debounceTimer = null;
stockSearchInput.oninput = (e) => {
  clearTimeout(debounceTimer);
  const q = e.target.value.trim();
  if (q.length === 0) {
    searchResults.classList.add("hidden");
    return;
  }

  debounceTimer = setTimeout(async () => {
    try {
      const res = await api(`/stocks/search?q=${encodeURIComponent(q)}`);
      const items = await res.json();

      searchResults.innerHTML = "";
      if (items.length === 0) {
        searchResults.innerHTML = `<div class="search-item">No results found</div>`;
      } else {
        items.forEach((item) => {
          const div = document.createElement("div");
          div.className = "search-item";
          div.innerHTML = `<strong>${item.symbol}</strong> - ${item.name} (${item.exchange || ""})`;
          div.onclick = () => {
            orderSymbol.value = item.symbol;
            searchResults.classList.add("hidden");
            stockSearchInput.value = "";
            loadChartData(item.symbol, currentPeriod, currentInterval);
          };
          searchResults.appendChild(div);
        });
      }
      searchResults.classList.remove("hidden");
    } catch (err) {
      console.error(err);
    }
  }, 300);
};

// ---------------- Order Placement ---------------- //

orderForm.onsubmit = async (e) => {
  e.preventDefault();
  orderFeedback.textContent = "";
  orderFeedback.className = "feedback-msg";

  const side = document.querySelector('input[name="side"]:checked').value;
  const payload = {
    symbol: orderSymbol.value.trim().toUpperCase(),
    side: side,
    order_type: "MARKET",
    quantity: parseFloat(orderQty.value),
  };

  try {
    const res = await api("/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      orderFeedback.textContent = data.detail || "Order failed";
      orderFeedback.classList.add("neg");
      return;
    }

    orderFeedback.textContent = `Order Filled: ${side} ${data.quantity} shares of ${data.symbol} @ $${fmt(data.execution_price)}`;
    orderFeedback.classList.add("pos");
    orderQty.value = "";

    // Refresh dashboard state
    loadPortfolio();
    loadOrders();
  } catch (err) {
    orderFeedback.textContent = err.message;
    orderFeedback.classList.add("neg");
  }
};

// ---------------- Data Fetching & Rendering ---------------- //

async function loadPortfolio() {
  const res = await api("/portfolio");
  if (!res.ok) return;
  const data = await res.json();

  document.getElementById("val-cash").textContent = `$${fmt(data.available_funds)}`;
  document.getElementById("val-market").textContent = `$${fmt(data.total_market_value)}`;
  document.getElementById("val-net-worth").textContent = `$${fmt(data.total_portfolio_value)}`;

  const pnlEl = document.getElementById("val-pnl");
  pnlEl.textContent = `$${fmt(data.total_unrealized_pnl)}`;
  pnlEl.className = `metric-value ${data.total_unrealized_pnl >= 0 ? "pos" : "neg"}`;

  const tbody = document.getElementById("holdings-tbody");
  tbody.innerHTML = "";

  if (data.holdings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No open positions.</td></tr>`;
    return;
  }

  data.holdings.forEach((h) => {
    const isPos = h.unrealized_pnl >= 0;
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><strong>${h.symbol}</strong></td>
      <td>${parseFloat(h.quantity)}</td>
      <td>$${fmt(h.average_buy_price)}</td>
      <td>$${fmt(h.current_price)}</td>
      <td>$${fmt(h.market_value)}</td>
      <td class="${isPos ? "pos" : "neg"}">${isPos ? "+" : ""}$${fmt(h.unrealized_pnl)}</td>
      <td class="${isPos ? "pos" : "neg"}">${isPos ? "+" : ""}${fmt(h.unrealized_pnl_percent)}%</td>
    `;
    tbody.appendChild(row);
  });
}

async function loadOrders() {
  const res = await api("/orders?limit=20");
  if (!res.ok) return;
  const orders = await res.json();

  const tbody = document.getElementById("orders-tbody");
  tbody.innerHTML = "";

  if (orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No trade history.</td></tr>`;
    return;
  }

  orders.forEach((o) => {
    const dateStr = new Date(o.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${dateStr}</td>
      <td><strong>${o.symbol}</strong></td>
      <td class="${o.side === "BUY" ? "badge-buy" : "badge-sell"}">${o.side}</td>
      <td>${parseFloat(o.quantity)}</td>
      <td>$${fmt(o.execution_price)}</td>
      <td>$${fmt(o.total_amount)}</td>
      <td>${o.status}</td>
    `;
    tbody.appendChild(row);
  });
}

// ---------------- App Bootstrap ---------------- //

async function initApp() {
  if (!token) {
    authSection.classList.remove("hidden");
    dashboardSection.classList.add("hidden");
    navUserInfo.classList.add("hidden");
    return;
  }

  try {
    const res = await api("/auth/me");
    if (!res.ok) throw new Error();
    const user = await res.json();

    navUsername.textContent = `${user.username}`;
    navUserInfo.classList.remove("hidden");
    authSection.classList.add("hidden");

    // 1. Unhide dashboard FIRST so DOM has actual pixel dimensions
    dashboardSection.classList.remove("hidden");

    // 2. Initialize chart and load data
    initTradingViewChart();
    loadChartData("AAPL", "1mo", "1d");

    // 3. Load other dashboard tables
    loadPortfolio();
    loadOrders();
  } catch {
    logout();
  }
}

let chartInstance = null;
let candleSeries = null;
let currentChartSymbol = "AAPL";
let currentPeriod = "1mo";
let currentInterval = "1d";

function initTradingViewChart() {
  const container = document.getElementById("chart-container");
  if (!container || chartInstance) return;

  chartInstance = LightweightCharts.createChart(container, {
    width: container.clientWidth || 600,
    height: 380,
    layout: {
      background: { color: "#1e293b" },
      textColor: "#94a3b8",
    },
    grid: {
      vertLines: { color: "#334155" },
      horzLines: { color: "#334155" },
    },
    timeScale: {
      borderColor: "#334155",
      timeVisible: true,
      secondsVisible: false,
    },
    rightPriceScale: {
      borderColor: "#334155",
    },
  });

  const seriesOptions = {
    upColor: "#22c55e",
    downColor: "#ef4444",
    borderDownColor: "#ef4444",
    borderUpColor: "#22c55e",
    wickDownColor: "#ef4444",
    wickUpColor: "#22c55e",
  };

  // Compatible with both v3 and v4/v5
  if (typeof chartInstance.addCandlestickSeries === "function") {
    candleSeries = chartInstance.addCandlestickSeries(seriesOptions);
  } else {
    candleSeries = chartInstance.addSeries(LightweightCharts.CandlestickSeries, seriesOptions);
  }

  new ResizeObserver((entries) => {
    if (entries.length && chartInstance) {
      chartInstance.applyOptions({
        width: entries[0].contentRect.width,
      });
    }
  }).observe(container);
}

async function loadChartData(symbol, period = "1mo", interval = "1d") {
  currentChartSymbol = symbol.toUpperCase();
  currentPeriod = period;
  currentInterval = interval;

  const titleEl = document.getElementById("chart-symbol-title");
  if (titleEl) titleEl.textContent = currentChartSymbol;

  try {
    const res = await api(`/stocks/${currentChartSymbol}/history?period=${period}&interval=${interval}`);
    if (!res.ok) return;

    const bars = await res.json();
    if (!bars || bars.length === 0) {
      console.warn("No bar data received for", symbol);
      return;
    }

    // Deduplicate by time key
    const timeMap = new Map();
    bars.forEach((b) => {
      timeMap.set(b.time, {
        time: b.time,
        open: parseFloat(b.open_price),
        high: parseFloat(b.high_price),
        low: parseFloat(b.low_price),
        close: parseFloat(b.close_price),
      });
    });

    const formattedData = Array.from(timeMap.values()).sort((a, b) => {
      if (typeof a.time === "number") return a.time - b.time;
      return a.time.localeCompare(b.time);
    });

    if (candleSeries && chartInstance) {
      candleSeries.setData(formattedData);

      // Auto-fit both axes so candles are brought into view
      chartInstance.timeScale().fitContent();
      chartInstance.priceScale("right").applyOptions({
        autoScale: true,
      });

      const lastBar = formattedData[formattedData.length - 1];
      const priceTag = document.getElementById("chart-price-tag");
      if (priceTag && lastBar) {
        priceTag.textContent = `$${fmt(lastBar.close)}`;
      }
    }
  } catch (err) {
    console.error("Failed to load chart data:", err);
  }
}
// Bind timeframe buttons
document.querySelectorAll(".tf-btn").forEach((btn) => {
  btn.onclick = (e) => {
    document.querySelectorAll(".tf-btn").forEach((b) => b.classList.remove("active"));
    e.target.classList.add("active");
    loadChartData(currentChartSymbol, e.target.dataset.period, e.target.dataset.interval);
  };
});

initApp();