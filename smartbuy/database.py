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
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS price_history;
    DROP TABLE IF EXISTS prices;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS stores;
    DROP TABLE IF EXISTS price_alerts;

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
        image_emoji TEXT DEFAULT '📦'
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
        product_id INTEGER NOT NULL REFERENCES products(product_id),
        target_price REAL NOT NULL,
        email TEXT,
        created_on TEXT DEFAULT CURRENT_TIMESTAMP,
        triggered INTEGER NOT NULL DEFAULT 0
    );
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
