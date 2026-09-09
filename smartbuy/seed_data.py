"""
SmartBuy — Seed Data
Populates the database with realistic sample stores/products/prices so the
app works fully offline. In production, swap `refresh_prices_from_source()`
in scraper.py for real API/scraping calls that write into the same tables.
"""
import random
import datetime
import json
from urllib.parse import quote_plus
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
    ("Samsung Galaxy Z Flip 6", "Smartphones", "📱", 109999),
    ("Nothing Phone 3", "Smartphones", "📱", 44999),
    ("MacBook Air M3", "Laptops", "💻", 114900),
    ("Dell XPS 13", "Laptops", "💻", 99990),
    ("HP Spectre x360", "Laptops", "💻", 124990),
    ("Lenovo Yoga Slim 7", "Laptops", "💻", 84990),
    ("boAt Airdopes 141", "Audio", "🎧", 1299),
    ("Sony WH-1000XM5", "Audio", "🎧", 29990),
    ("Apple AirPods Pro 2", "Audio", "🎧", 24900),
    ("Bose QuietComfort Ultra", "Audio", "🎧", 34900),
    ("Sennheiser Momentum 4", "Audio", "🎧", 29990),
    ("JBL Live Beam 3", "Audio", "🎧", 8999),
    ("Samsung 55-inch QLED TV", "TVs", "📺", 64990),
    ("Sony Bravia 55-inch OLED TV", "TVs", "📺", 119990),
    ("LG 65-inch NanoCell TV", "TVs", "📺", 79990),
    ("TCL 55-inch 4K Google TV", "TVs", "📺", 42990),
    ("Canon EOS R50", "Cameras", "📷", 68990),
    ("GoPro HERO12 Black", "Cameras", "📷", 44990),
    ("Sony Alpha A6400", "Cameras", "📷", 74990),
    ("DJI Osmo Pocket 3", "Cameras", "📷", 51990),
    ("PlayStation 5 Slim", "Gaming", "🎮", 54990),
    ("ASUS ROG Gaming Laptop", "Gaming", "💻", 139990),
    ("Xbox Series X", "Gaming", "🎮", 52990),
    ("Nintendo Switch OLED", "Gaming", "🎮", 31990),
    ("Kindle Paperwhite", "Tablets & E-readers", "📖", 14999),
    ("Apple Watch Series 10", "Wearables", "⌚", 46900),
    ("Dyson V12 Detect Slim", "Home", "🏠", 52900),
    ("Google Pixel 9", "Smartphones", "📱", 79999),
    ("Xiaomi Pad 7", "Tablets & E-readers", "📱", 29999),
    ("Samsung Galaxy Tab S10", "Tablets & E-readers", "📱", 74999),
    ("OnePlus Pad 2", "Tablets & E-readers", "📱", 39999),
    ("Samsung Galaxy Watch 7", "Wearables", "⌚", 33999),
    ("Fitbit Charge 6", "Wearables", "⌚", 12999),
    ("Philips Air Fryer XL", "Home", "🏠", 12999),
    ("iRobot Roomba i5", "Home", "🏠", 39990),
]


def _price_variation(base_price, store_index):
    """Deterministic-ish but varied pricing per store around the base price."""
    random.seed(hash((base_price, store_index)) % (2**32))
    pct = random.uniform(-0.06, 0.05)  # -6% to +5% around base
    price = base_price * (1 + pct)
    return round(price / 10) * 10  # round to nearest 10


def _specifications(name, category):
    templates = {
        "Smartphones": {"Display": "6.1-inch OLED", "Storage": "128 GB", "Battery": "All-day battery", "Warranty": "1 year"},
        "Laptops": {"Display": "15.6-inch display", "Memory": "16 GB RAM", "Storage": "512 GB SSD", "Warranty": "1 year"},
        "Audio": {"Type": "Wireless", "Connectivity": "Bluetooth 5.3", "Battery": "Up to 30 hours", "Warranty": "1 year"},
        "TVs": {"Display": "4K Ultra HD", "Refresh rate": "120 Hz", "Smart platform": "Google TV", "Warranty": "2 years"},
        "Cameras": {"Resolution": "24.2 MP", "Video": "4K recording", "Connectivity": "Wi-Fi and Bluetooth", "Warranty": "1 year"},
        "Gaming": {"Resolution": "Up to 4K", "Storage": "1 TB", "Connectivity": "Wi-Fi 6", "Warranty": "1 year"},
        "Tablets & E-readers": {"Display": "11-inch display", "Storage": "128 GB", "Battery": "Up to 12 hours", "Warranty": "1 year"},
        "Wearables": {"Display": "AMOLED display", "Water resistance": "5 ATM", "Battery": "Up to 7 days", "Warranty": "1 year"},
        "Home": {"Power": "1400 W", "Capacity": "Large capacity", "Control": "Smart controls", "Warranty": "2 years"},
    }
    specs = dict(templates.get(category, {"Condition": "New", "Warranty": "1 year"}))
    specs["Model"] = name
    return json.dumps(specs)


def _description(name, category):
    descriptions = {
        "Smartphones": "A modern smartphone with a bright display, dependable battery life, and the everyday performance needed for work, photos, and entertainment.",
        "Laptops": "A capable laptop designed for productive work, smooth multitasking, and reliable everyday performance in a portable format.",
        "Audio": "A versatile audio pick for clear listening, comfortable use, and dependable wireless performance throughout the day.",
        "TVs": "A high-quality home entertainment display with sharp detail, vivid color, and smart features for streaming and everyday viewing.",
        "Cameras": "A compact imaging product for capturing detailed photos and steady video, with useful connectivity for sharing content.",
        "Gaming": "A performance-focused gaming product built for responsive play, immersive entertainment, and long sessions at home.",
        "Tablets & E-readers": "A lightweight screen for reading, streaming, browsing, and focused everyday tasks with an easy-to-carry design.",
        "Wearables": "A practical wearable for tracking activity, staying connected, and checking useful information at a glance.",
        "Home": "A convenient home product designed to make everyday routines easier with practical controls and dependable performance.",
    }
    return descriptions.get(category, f"A carefully selected {category.lower()} product with useful features and dependable everyday value.")


def _store_url(store_name, product_name):
    query = quote_plus(product_name)
    domains = {
        "Amazon": f"https://www.amazon.in/s?k={query}",
        "Flipkart": f"https://www.flipkart.com/search?q={query}",
        "Croma": f"https://www.croma.com/searchB?q={query}",
        "Reliance Digital": f"https://www.reliancedigital.in/search?q={query}",
        "Vijay Sales": f"https://www.vijaysales.com/search/{query}",
    }
    return domains[store_name]


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
            "INSERT INTO products (name, category, image_emoji, description, specs) VALUES (?, ?, ?, ?, ?)",
            (name, category, emoji, _description(name, category), _specifications(name, category)),
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
                          rating, review_count, in_stock, store_url)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (product_id, store_id, original_price, current_price,
                      rating, review_count, in_stock, _store_url(store_name, name)),
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
