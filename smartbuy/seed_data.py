"""
SmartBuy — Seed Data
Populates the database with realistic sample stores/products/prices so the
app works fully offline. In production, swap `refresh_prices_from_source()`
in scraper.py for real API/scraping calls that write into the same tables.
"""
import random
import datetime
from database import get_connection, init_db

STORES = [
    # name, delivery_days, trust_score
    ("Amazon", 2, 4.5),
    ("Flipkart", 2, 4.4),
    ("Croma", 3, 4.2),
    ("Reliance Digital", 3, 4.1),
    ("Vijay Sales", 4, 4.0),
]

PRODUCTS = [
    # name, category, emoji, base_price
    ("iPhone 16", "Smartphones", "📱", 69999),
    ("iPhone 16 Pro", "Smartphones", "📱", 129900),
    ("Samsung Galaxy S24", "Smartphones", "📱", 74999),
    ("Redmi Note 14", "Smartphones", "📱", 18999),
    ("OnePlus 13", "Smartphones", "📱", 64999),
    ("MacBook Air M3", "Laptops", "💻", 114900),
    ("Dell XPS 13", "Laptops", "💻", 99990),
    ("boAt Airdopes 141", "Audio", "🎧", 1299),
    ("Sony WH-1000XM5", "Audio", "🎧", 29990),
    ("Samsung 55-inch QLED TV", "TVs", "📺", 64990),
]


def _price_variation(base_price, store_index):
    """Deterministic-ish but varied pricing per store around the base price."""
    random.seed(hash((base_price, store_index)) % (2**32))
    pct = random.uniform(-0.06, 0.05)  # -6% to +5% around base
    price = base_price * (1 + pct)
    return round(price / 10) * 10  # round to nearest 10


def seed():
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    store_ids = {}
    for name, delivery_days, trust in STORES:
        cur.execute(
            "INSERT INTO stores (name, delivery_days, trust_score) VALUES (?, ?, ?)",
            (name, delivery_days, trust),
        )
        store_ids[name] = cur.lastrowid

    today = datetime.date.today()

    for name, category, emoji, base_price in PRODUCTS:
        cur.execute(
            "INSERT INTO products (name, category, image_emoji) VALUES (?, ?, ?)",
            (name, category, emoji),
        )
        product_id = cur.lastrowid

        for idx, (store_name, delivery_days, trust) in enumerate(STORES):
            store_id = store_ids[store_name]
            current_price = _price_variation(base_price, idx)

            # ~40% chance a store is currently running a discount
            random.seed(hash((product_id, store_id, "discount")) % (2**32))
            has_discount = random.random() < 0.4
            if has_discount:
                discount_pct = random.uniform(0.05, 0.20)
                original_price = round(current_price / (1 - discount_pct) / 10) * 10
            else:
                original_price = current_price

            rating = round(random.uniform(3.6, 4.8), 1)
            review_count = random.randint(120, 15000)
            in_stock = 0 if random.random() < 0.05 else 1

            cur.execute(
                """INSERT INTO prices
                   (product_id, store_id, original_price, current_price,
                    rating, review_count, in_stock)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (product_id, store_id, original_price, current_price,
                 rating, review_count, in_stock),
            )

            # Generate 30 days of price history with gentle random walk
            price_walk = current_price
            for days_ago in range(30, -1, -1):
                random.seed(hash((product_id, store_id, days_ago)) % (2**32))
                drift = random.uniform(-0.015, 0.015)
                price_walk = max(base_price * 0.7, price_walk * (1 + drift))
                recorded_on = (today - datetime.timedelta(days=days_ago)).isoformat()
                cur.execute(
                    """INSERT INTO price_history
                       (product_id, store_id, price, recorded_on)
                       VALUES (?, ?, ?, ?)""",
                    (product_id, store_id, round(price_walk / 10) * 10, recorded_on),
                )
            # make sure history ends exactly at the current live price
            cur.execute(
                """UPDATE price_history SET price = ?
                   WHERE product_id = ? AND store_id = ? AND recorded_on = ?""",
                (current_price, product_id, store_id, today.isoformat()),
            )

    conn.commit()
    conn.close()
    print(f"Seeded {len(STORES)} stores and {len(PRODUCTS)} products with 31-day price history.")


if __name__ == "__main__":
    seed()
