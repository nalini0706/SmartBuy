// ---------- Home page: live search ----------
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const productGrid = document.getElementById("productGrid");
const noResults = document.getElementById("noResults");
const resultCount = document.getElementById("resultCount");
let selectedCategory = "";
const compareIds = new Set();

function updateCompareTray() {
  const tray = document.getElementById("compareTray");
  const count = document.getElementById("compareCount");
  const link = document.getElementById("compareLink");
  if (!tray || !count || !link) return;
  count.textContent = compareIds.size;
  link.href = `/compare?ids=${[...compareIds].join(",")}`;
  tray.hidden = compareIds.size === 0;
  document.querySelectorAll(".compare-toggle").forEach(button => {
    const selected = compareIds.has(Number(button.dataset.productId));
    button.classList.toggle("selected", selected);
    button.textContent = selected ? "Selected" : "Compare";
  });
}

async function toggleWishlist(button) {
  const productId = Number(button.dataset.productId);
  const removing = button.classList.contains("saved");
  const response = await fetch("/api/wishlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, action: removing ? "remove" : "add" }),
  });
  if (!response.ok) return;
  button.classList.toggle("saved", !removing);
  button.textContent = removing ? "♡" : "♥";
  button.setAttribute("aria-label", removing ? "Add to wishlist" : "Remove from wishlist");
}

async function runSearch() {
  const q = searchInput.value.trim();
  const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&category=${encodeURIComponent(selectedCategory)}`);
  const products = await res.json();

  productGrid.innerHTML = "";
  noResults.style.display = products.length ? "none" : "block";
  if (resultCount) resultCount.textContent = `${products.length} product${products.length === 1 ? "" : "s"}`;

  products.forEach(p => {
    const a = document.createElement("a");
    a.className = "product-card";
    a.href = `/product/${p.product_id}`;
    const badge = p.discount_pct >= 10 ? `<span class="deal-badge">-${p.discount_pct}%</span>` : "";
    a.innerHTML = `
      ${badge}
      <button class="wishlist-toggle" data-product-id="${p.product_id}" aria-label="Add to wishlist">♡</button>
      <div class="product-image"><img src="${p.image_url}" data-fallback="${p.image_fallback}" data-final-fallback="/static/product-placeholder.svg" onerror="if(this.dataset.fallback!==this.dataset.finalFallback){this.src=this.dataset.fallback;this.dataset.fallback=this.dataset.finalFallback}else{this.onerror=null;this.src=this.dataset.finalFallback}" alt="${p.name}" loading="lazy"><span class="image-category">${p.category}</span></div>
      <div class="product-card-body">
        <div class="name">${p.name}</div>
        <div class="card-rating">★ ${p.rating} <span>· Compare across stores</span></div>
        <div class="card-price-label">Best price from</div>
        <div class="card-price">₹${Number(p.best_price).toLocaleString("en-IN")} <span>→</span></div>
        <button class="compare-toggle" data-product-id="${p.product_id}">Compare</button>
      </div>
    `;
    productGrid.appendChild(a);
  });
}

if (productGrid) {
  productGrid.addEventListener("click", (event) => {
    const wishlistButton = event.target.closest(".wishlist-toggle");
    const compareButton = event.target.closest(".compare-toggle");
    if (!wishlistButton && !compareButton) return;
    event.preventDefault();
    event.stopPropagation();
    if (wishlistButton) toggleWishlist(wishlistButton);
    if (compareButton) {
      const productId = Number(compareButton.dataset.productId);
      if (compareIds.has(productId)) compareIds.delete(productId);
      else if (compareIds.size < 3) compareIds.add(productId);
      updateCompareTray();
    }
  });
}

document.getElementById("clearCompare")?.addEventListener("click", () => {
  compareIds.clear();
  updateCompareTray();
});
updateCompareTray();

document.querySelectorAll(".category-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".category-chip").forEach(item => item.classList.remove("active"));
    chip.classList.add("active");
    selectedCategory = chip.dataset.category;
    runSearch();
  });
});

document.querySelectorAll(".category-link").forEach(link => {
  link.addEventListener("click", () => {
    const matchingChip = document.querySelector(`.category-chip[data-category="${link.dataset.category}"]`);
    if (matchingChip) matchingChip.click();
    document.getElementById("productGrid")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

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
if (window.PRICE_HISTORY && typeof Chart !== "undefined") {
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
    const resultBox = document.getElementById("alertResult");
    try {
      const productId = document.getElementById("alertProductId").value;
      const targetPrice = document.getElementById("targetPrice").value;
      const email = document.getElementById("alertEmail").value;
      const res = await fetch("/api/alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: productId, target_price: targetPrice, email }),
      });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || "Could not set the alert");

      if (data.already_triggered) {
        resultBox.className = "alert-result show result-ok";
        resultBox.textContent = `Good news - a store already has this at ₹${data.best_current_price.toLocaleString("en-IN")}, at or below your target!`;
      } else {
        resultBox.className = "alert-result show result-info";
        resultBox.textContent = `Alert set for ₹${Number(targetPrice).toLocaleString("en-IN")}. Current best price is ₹${data.best_current_price?.toLocaleString("en-IN") ?? "N/A"}. We'll notify you when it drops.`;
      }
    } catch (error) {
      resultBox.className = "alert-result show result-error";
      resultBox.textContent = error.message;
    }
  });
}

// ---------- Discount calculator form ----------
const discountForm = document.getElementById("discountForm");
if (discountForm) {
  discountForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const resultBox = document.getElementById("discountResult");
    try {
      const original = document.getElementById("origPrice").value;
      const final = document.getElementById("finalPrice").value;
      const res = await fetch(`/api/discount-calc?original=${encodeURIComponent(original)}&final=${encodeURIComponent(final)}`);
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || "Could not calculate the discount");

      resultBox.className = "discount-result show result-ok";
      resultBox.innerHTML = `
        You save <strong>₹${data.discount_amount.toLocaleString("en-IN")}</strong>
        (<strong>${data.discount_percent}%</strong> off) -
        final price <strong>₹${data.final_price.toLocaleString("en-IN")}</strong>.
      `;
    } catch (error) {
      resultBox.className = "discount-result show result-error";
      resultBox.textContent = error.message;
    }
  });
}
