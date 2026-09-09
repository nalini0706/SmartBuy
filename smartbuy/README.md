# 🛒 SmartBuy — AI-Based Product Price Comparison & Deal Recommendation System

Flow: **User → Search Product → Collect Prices → Compare → Analyze Deals → Recommend Best Option**

## Features implemented

| Feature | Where |
|---|---|
| 🔍 Product search (live, as-you-type) | `/api/search`, `templates/index.html`, `static/script.js` |
| 💰 Price comparison across 5 stores | `/product/<id>`, `templates/results.html` |
| 📊 Price history + trend (30-day) | `get_price_history()`, `price_trend()` in `app.py`, Chart.js line chart |
| 🔔 Price drop alert | `/api/alert` (POST), stored in `price_alerts` table |
| 🏷️ Discount calculator | `/api/discount-calc` (GET) |
| ⭐ Ratings & reviews per store | seeded in `prices` table, shown in comparison table |
| 🏆 Best deal recommendation (not just cheapest) | `recommend.py` — weighted score of price + rating + delivery speed + discount |

## Tech stack

- **Backend:** Python + Flask
- **Database:** SQLite (`smartbuy.db`, auto-created)
- **Frontend:** HTML + CSS + vanilla JS
- **Charts:** Chart.js (loaded via CDN)
- **Data:** Realistic seeded sample data (see note below on going live)

## Setup

```bash
cd smartbuy
pip install -r requirements.txt
python seed_data.py     # creates smartbuy.db and fills it with sample data
python app.py            # runs on http://localhost:5000
```

Then open **http://localhost:5000** in your browser.

## How the "Best Deal" score works (`recommend.py`)

Instead of only picking the cheapest price, each store's offer is scored 0–100 using weighted factors:

```
score = 0.45 * price_score      (cheaper = higher, normalized across stores)
      + 0.25 * rating_score     (higher rating = higher)
      + 0.15 * delivery_score   (faster delivery = higher)
      + 0.15 * discount_score   (bigger discount = higher, capped at 20%+)
```

Out-of-stock offers get their score multiplied by 0.3 so they're still visible but rarely recommended. You can tune the `WEIGHTS` dict in `recommend.py` to change what matters most.

Run this to see it in action — several products show a **different store for "best deal" vs "cheapest"**:

```bash
python3 -c "
from app import get_offers_for_product, get_all_products
from recommend import score_offers
for p in get_all_products():
    offers = score_offers(get_offers_for_product(p['product_id']))
    cheapest = [o for o in offers if o['is_best_price']][0]
    best = [o for o in offers if o['is_best_deal']][0]
    print(p['name'], '| cheapest:', cheapest['store_name'], '| best deal:', best['store_name'])
"
```

## Going from mock data to real data

Right now `seed_data.py` generates realistic sample prices/ratings/history so the whole app works offline. To connect real stores:

1. Write a `scraper.py` (or use store APIs where available) that fetches current price/rating/stock for a product from each store.
2. On a schedule (cron job or Flask background task), write results into the `prices` table (upsert) and append a row to `price_history` for that day.
3. Add a small worker that checks `price_alerts` against current prices and sends an email/notification when `current_price <= target_price`, then sets `triggered = 1`.

The database schema (`database.py`) already supports all of this — no changes needed to the web app itself.

## Project structure

```
smartbuy/
├── app.py              # Flask routes
├── database.py         # SQLite schema
├── seed_data.py         # Sample data generator
├── recommend.py         # Best-deal scoring engine
├── requirements.txt
├── templates/
│   ├── index.html       # Search / browse page
│   └── results.html     # Comparison table + chart + alert + discount calc
└── static/
    ├── style.css
    └── script.js
```
