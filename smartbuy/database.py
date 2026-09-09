"""
SmartBuy — Database layer
Handles SQLite schema creation and connections.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smartbuy.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            created_on TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            wishlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
            created_on TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, product_id)
        )
    """)
    alert_columns = {row[1] for row in conn.execute("PRAGMA table_info(price_alerts)").fetchall()}
    if "user_id" not in alert_columns and alert_columns:
        conn.execute("ALTER TABLE price_alerts ADD COLUMN user_id INTEGER REFERENCES users(user_id)")
    product_columns = {row[1] for row in conn.execute("PRAGMA table_info(products)").fetchall()}
    if "specs" not in product_columns and product_columns:
        conn.execute("ALTER TABLE products ADD COLUMN specs TEXT")
    price_columns = {row[1] for row in conn.execute("PRAGMA table_info(prices)").fetchall()}
    if "store_url" not in price_columns and price_columns:
        conn.execute("ALTER TABLE prices ADD COLUMN store_url TEXT")
    conn.commit()
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS price_history;
    DROP TABLE IF EXISTS prices;
    DROP TABLE IF EXISTS wishlist;
    DROP TABLE IF EXISTS price_alerts;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS stores;

    CREATE TABLE stores (
        store_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        delivery_days INTEGER NOT NULL DEFAULT 3,
        trust_score REAL NOT NULL DEFAULT 4.0  -- store reliability, 0-5
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        image_emoji TEXT DEFAULT '📦',
        description TEXT,
        specs TEXT
    );

    -- current live price + rating + discount info per store
    CREATE TABLE prices (
        price_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        store_id INTEGER NOT NULL REFERENCES stores(store_id),
        original_price REAL NOT NULL,
        current_price REAL NOT NULL,
        rating REAL NOT NULL DEFAULT 4.0,        -- 0-5
        review_count INTEGER NOT NULL DEFAULT 0,
        in_stock INTEGER NOT NULL DEFAULT 1,
        store_url TEXT,
        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(product_id, store_id)
    );

    -- historical price points for charting (per product/store)
    CREATE TABLE price_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        store_id INTEGER NOT NULL REFERENCES stores(store_id),
        price REAL NOT NULL,
        recorded_on TEXT NOT NULL  -- ISO date
    );

    -- user price-drop alerts
    CREATE TABLE price_alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        target_price REAL NOT NULL,
        email TEXT,
        created_on TEXT DEFAULT CURRENT_TIMESTAMP,
        triggered INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE wishlist (
        wishlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
        created_on TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, product_id)
    );

    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        created_on TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
