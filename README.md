# 🛒 SmartBuy — AI-Based Product Price Comparison & Deal Recommendation System

Flow: **User → Search Product → Collect Prices → Compare → Analyze Deals → Recommend Best Option**

## Features Implemented

| Feature | Where |
|---|---|
| 🔍 Product search (live, as-you-type) | `/api/search`, `templates/index.html`, `static/script.js` |
| 💰 Price comparison across 5 stores | `/product/<id>`, `templates/results.html` |
| 📊 Price history + trend (30-day) | `get_price_history()`, `price_trend()` in `app.py`, Chart.js line chart |
| 🔔 Price drop alert | `/api/alert` (POST), stored in `price_alerts` table |
| 🏷️ Discount calculator | `/api/discount-calc` (GET) |
| ⭐ Ratings & reviews per store | seeded in `prices` table, shown in comparison table |
| 🏆 Best deal recommendation (not just cheapest) | `recommend.py` — weighted score of price + rating + delivery speed + discount |
| 🔐 User authentication | `/login`, `/signup`, `/logout` with hashed passwords and protected routes |
| ❤️ Personal wishlist | `/api/wishlist`, `/dashboard` |
| 📊 Product comparison | Select up to three products and open `/compare` |
| 👤 User dashboard | `/dashboard` with saved products and price alerts |
| 📋 Product specifications | Category-specific specifications on every product page |
| 🛍️ Store purchase links | Search links for Amazon, Flipkart, Croma, Reliance Digital, and Vijay Sales |
| 🖼️ Product-specific photos | Product-name image mapping with category fallback for future products |
| 🧭 Category browsing | Smartphones, laptops, audio, TVs, cameras, gaming, tablets, wearables, and home |
| 📦 Expanded catalog | 40 seeded products across 9 categories |

## Tech Stack

- **Backend:** Python + Flask
- **Database:** SQLite (`smartbuy.db`, auto-created)
- **Frontend:** HTML + CSS + vanilla JS
- **Charts:** Chart.js (loaded via CDN)
- **Data:** Realistic seeded sample data (see note below on going live)
- **Authentication:** Flask sessions + Werkzeug password hashing

## Quick Setup

```bash
cd smartbuy
pip install -r requirements.txt
python seed_data.py     # creates smartbuy.db and fills it with sample data
python app.py            # runs on http://localhost:5000
```

Then open **http://localhost:5000** in your browser.

Create an account from the sign-up page before browsing the protected product catalog. Run `seed_data.py` whenever you want to reset the demo catalog; existing user accounts are preserved.

## How the "Best Deal" Score Works

Instead of only picking the cheapest price, each store's offer is scored 0–100 using weighted factors:

```
score = 0.45 * price_score      (cheaper = higher, normalized across stores)
      + 0.25 * rating_score     (higher rating = higher)
      + 0.15 * delivery_score   (faster delivery = higher)
      + 0.15 * discount_score   (bigger discount = higher, capped at 20%+)
```

Out-of-stock offers get their score multiplied by 0.3 so they're still visible but rarely recommended. You can tune the `WEIGHTS` dict in `recommend.py` to change what matters most.

## Main Routes

| Route | Purpose |
|---|---|
| `/` | Searchable product catalog and category filters |
| `/product/<id>` | Product details, specifications, offers, purchase links, chart, and alerts |
| `/dashboard` | User wishlist and saved price alerts |
| `/compare?ids=1,2,3` | Side-by-side comparison for up to three products |
| `/login`, `/signup`, `/logout` | Authentication flow |

## Project Structure

```
smartbuy/
├── app.py              # Flask routes
├── database.py         # SQLite schema
├── seed_data.py        # Sample data generator
├── recommend.py        # Best-deal scoring engine
├── requirements.txt
├── README.md
├── templates/
│   ├── index.html      # Search, categories, wishlist, and compare controls
│   ├── results.html    # Product details, specs, offers, chart, and alerts
│   ├── dashboard.html  # Wishlist and alert dashboard
│   ├── compare.html    # Side-by-side product comparison
│   ├── login.html      # Sign-in page
│   └── signup.html     # Account creation page
└── static/
    ├── style.css
    └── script.js
```

## Demo Data and Images

The seed script creates **40 products across 9 categories**, five stores, current offers, ratings, discounts, and 31 days of price history. Product images are selected by exact product name, with category images used only for products added later without a mapping. Store buttons currently open store search pages using the product name.

## Going Live

Right now `seed_data.py` generates realistic sample prices/ratings/history so the whole app works offline. To connect real stores:

1. Write a `scraper.py` (or use store APIs where available) that fetches current price/rating/stock for a product from each store.
2. On a schedule (cron job or Flask background task), write results into the `prices` table (upsert) and append a row to `price_history` for that day.
3. Add a small worker that checks `price_alerts` against current prices and sends notifications when `current_price <= target_price`, then sets `triggered = 1`.

The database schema (`database.py`) supports users, wishlists, alerts, product specifications, store URLs, current offers, and price history. Replace seeded values with verified store API or scraper data before production use.

## Supported Stores

- Amazon
- Flipkart
- Croma
- Reliance Digital
- Vijay Sales

## License

This project is open source and available for educational and commercial use.
