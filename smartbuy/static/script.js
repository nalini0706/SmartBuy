// ---------- Home page: live search ----------
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const productGrid = document.getElementById("productGrid");
const noResults = document.getElementById("noResults");

async function runSearch() {
  const q = searchInput.value.trim();
  const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
  const products = await res.json();

  productGrid.innerHTML = "";
  noResults.style.display = products.length ? "none" : "block";

  products.forEach(p => {
    const a = document.createElement("a");
    a.className = "product-card";
    a.href = `/product/${p.product_id}`;
    a.innerHTML = `
      <div class="emoji">${p.image_emoji}</div>
      <div class="name">${p.name}</div>
      <div class="category">${p.category}</div>
    `;
    productGrid.appendChild(a);
  });
}

if (searchBtn) {
  searchBtn.addEventListener("click", runSearch);
  searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") runSearch();
  });
  searchInput.addEventListener("input", () => {
    // debounce-lite: run search as user types
    clearTimeout(window._searchTimer);
    window._searchTimer = setTimeout(runSearch, 250);
  });
}

// ---------- Results page: price history chart ----------
if (window.PRICE_HISTORY) {
  const ctx = document.getElementById("priceChart");
  const history = window.PRICE_HISTORY;
  const colors = ["#2563eb", "#f59e0b", "#16a34a", "#dc2626", "#7c3aed"];

  const allDates = [...new Set(
    Object.values(history).flat().map(p => p.date)
  )].sort();

  const datasets = Object.keys(history).map((storeName, i) => {
    const byDate = Object.fromEntries(history[storeName].map(p => [p.date, p.price]));
    return {
      label: storeName,
      data: allDates.map(d => byDate[d] ?? null),
      borderColor: colors[i % colors.length],
      backgroundColor: colors[i % colors.length],
      tension: 0.3,
      spanGaps: true,
      pointRadius: 0,
      borderWidth: 2,
    };
  });

  new Chart(ctx, {
    type: "line",
    data: { labels: allDates, datasets },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "bottom" } },
      scales: {
        y: { ticks: { callback: (v) => "₹" + v.toLocaleString("en-IN") } },
        x: { ticks: { maxTicksLimit: 8 } },
      },
    },
  });
}

// ---------- Price drop alert form ----------
const alertForm = document.getElementById("alertForm");
if (alertForm) {
  alertForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const productId = document.getElementById("alertProductId").value;
    const targetPrice = document.getElementById("targetPrice").value;
    const email = document.getElementById("alertEmail").value;

    const res = await fetch("/api/alert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, target_price: targetPrice, email }),
    });
    const data = await res.json();
    const resultBox = document.getElementById("alertResult");
    resultBox.classList.add("show");

    if (data.already_triggered) {
      resultBox.className = "alert-result show result-ok";
      resultBox.textContent = `🎉 Good news — a store already has this at ₹${data.best_current_price.toLocaleString("en-IN")}, at or below your target!`;
    } else {
      resultBox.className = "alert-result show result-info";
      resultBox.textContent = `Alert set for ₹${Number(targetPrice).toLocaleString("en-IN")}. Current best price is ₹${data.best_current_price?.toLocaleString("en-IN") ?? "N/A"}. We'll notify you when it drops.`;
    }
  });
}

// ---------- Discount calculator form ----------
const discountForm = document.getElementById("discountForm");
if (discountForm) {
  discountForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const original = document.getElementById("origPrice").value;
    const final = document.getElementById("finalPrice").value;

    const res = await fetch(`/api/discount-calc?original=${original}&final=${final}`);
    const data = await res.json();
    const resultBox = document.getElementById("discountResult");
    resultBox.classList.add("show", "result-ok");

    if (data.error) {
      resultBox.textContent = "Error: " + data.error;
    } else {
      resultBox.innerHTML = `
        You save <strong>₹${data.discount_amount.toLocaleString("en-IN")}</strong>
        (<strong>${data.discount_percent}%</strong> off) —
        final price <strong>₹${data.final_price.toLocaleString("en-IN")}</strong>.
      `;
    }
  });
}
