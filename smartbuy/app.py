"""
SmartBuy — AI-Based Product Price Comparison & Deal Recommendation System
Flow: User -> Search Product -> Collect Prices -> Compare -> Analyze Deals -> Recommend Best Option
"""
from functools import wraps
import json
import os

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from database import get_connection
from recommend import score_offers
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "smartbuy-development-key-change-me")


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


# ---------- Data access helpers ----------

def search_products(query, category=""):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.product_id, p.name, p.category, p.image_emoji, p.description,
                  MIN(pr.current_price) AS best_price,
                  MAX(pr.rating) AS rating,
                  MAX(CASE WHEN pr.original_price > 0
                      THEN ROUND((pr.original_price - pr.current_price) * 100.0 / pr.original_price, 0)
                      ELSE 0 END) AS discount_pct
           FROM products p LEFT JOIN prices pr ON pr.product_id = p.product_id
           WHERE p.name LIKE ? AND (? = '' OR p.category = ?)
           GROUP BY p.product_id ORDER BY p.name""",
        (f"%{query}%", category, category),
    ).fetchall()
    conn.close()
    return decorate_products(rows)


def get_all_products():
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.product_id, p.name, p.category, p.image_emoji, p.description,
                  MIN(pr.current_price) AS best_price,
                  MAX(pr.rating) AS rating,
                  MAX(CASE WHEN pr.original_price > 0
                      THEN ROUND((pr.original_price - pr.current_price) * 100.0 / pr.original_price, 0)
                      ELSE 0 END) AS discount_pct
           FROM products p LEFT JOIN prices pr ON pr.product_id = p.product_id
           GROUP BY p.product_id ORDER BY p.name"""
    ).fetchall()
    conn.close()
    return decorate_products(rows)


def decorate_products(rows):
    """Add stable visual assets while keeping product data in SQLite."""
    products = []
    for row in rows:
        product = dict(row)
        product["image_url"] = product_image_url(product["category"], product["name"])
        product["best_price"] = product["best_price"] or 0
        product["rating"] = round(product["rating"] or 0, 1)
        product["discount_pct"] = int(product["discount_pct"] or 0)
        products.append(product)
    return products


def product_image_url(category, product_name=None):
    product_images = {
        "iPhone 16": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
        "iPhone 16 Pro": "https://images.unsplash.com/photo-1592286927505-2fd9f07f7b5b",
        "Samsung Galaxy S24": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf",
        "Redmi Note 14": "https://images.unsplash.com/photo-1598327105666-5b89351aff97",
        "OnePlus 13": "https://images.unsplash.com/photo-1603899122634-f086ca5f5ddd",
        "Samsung Galaxy Z Flip 6": "https://images.unsplash.com/photo-1616348436168-de43ad0db179",
        "Nothing Phone 3": "https://images.unsplash.com/photo-1556656793-08538906a9f8",
        "Google Pixel 9": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5",
        "MacBook Air M3": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853",
        "Dell XPS 13": "https://images.unsplash.com/photo-1517336714739-489689fd1ca8",
        "HP Spectre x360": "https://images.unsplash.com/photo-1541807084-5c52b6b3adef",
        "Lenovo Yoga Slim 7": "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2",
        "ASUS ROG Gaming Laptop": "https://images.unsplash.com/photo-1593642702821-c8da6771f0c6",
        "boAt Airdopes 141": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1",
        "Sony WH-1000XM5": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
        "Apple AirPods Pro 2": "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434",
        "Bose QuietComfort Ultra": "https://images.unsplash.com/photo-1546435770-a3e426bf472b",
        "Sennheiser Momentum 4": "https://images.unsplash.com/photo-1487215078519-e21cc028cb29",
        "JBL Live Beam 3": "https://images.unsplash.com/photo-1583394838336-acd977736f90",
        "Samsung 55-inch QLED TV": "https://images.unsplash.com/photo-1593784991095-a205069470b6",
        "Sony Bravia 55-inch OLED TV": "https://images.unsplash.com/photo-1461151304267-38535e780c79",
        "LG 65-inch NanoCell TV": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1",
        "TCL 55-inch 4K Google TV": "https://images.unsplash.com/photo-1601944177325-f8867652837f",
        "Canon EOS R50": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32",
        "GoPro HERO12 Black": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f",
        "Sony Alpha A6400": "https://images.unsplash.com/photo-1502920917128-1aa500764cbd",
        "DJI Osmo Pocket 3": "https://images.unsplash.com/photo-1495701002650-27a7f8b9f9b5",
        "PlayStation 5 Slim": "https://images.unsplash.com/photo-1606813907291-d86efa9b94db",
        "ASUS ROG Gaming Laptop": "https://images.unsplash.com/photo-1593642702909-dec73df255d7",
        "Xbox Series X": "https://images.unsplash.com/photo-1621259182978-fbf93132d53d",
        "Nintendo Switch OLED": "https://images.unsplash.com/photo-1578303512597-81e6cc155b3e",
        "Kindle Paperwhite": "https://images.unsplash.com/photo-1544947950-fa07a98d237f",
        "Xiaomi Pad 7": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0",
        "Samsung Galaxy Tab S10": "https://images.unsplash.com/photo-1561154464-82e9adf32764",
        "OnePlus Pad 2": "https://images.unsplash.com/photo-1585790050230-5dd28404ccb9",
        "Apple Watch Series 10": "https://images.unsplash.com/photo-1523275335684-37898b6baf30",
        "Samsung Galaxy Watch 7": "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1",
        "Fitbit Charge 6": "https://images.unsplash.com/photo-1576243345690-4e4b79b63288",
        "Dyson V12 Detect Slim": "https://images.unsplash.com/photo-1558317374-067fb5f30001",
        "Philips Air Fryer XL": "https://images.unsplash.com/photo-1585325701956-60dd9c8553bc",
        "iRobot Roomba i5": "https://images.unsplash.com/photo-1581578731548-c64695cc6952",
    }
    category_images = {
        "Smartphones": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=90",
        "Laptops": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=90",
        "Audio": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=90",
        "TVs": "https://images.unsplash.com/photo-1593784991095-a205069470b6?auto=format&fit=crop&w=900&q=90",
        "Cameras": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=90",
        "Gaming": "https://images.unsplash.com/photo-1605901309584-818e25960a8f?auto=format&fit=crop&w=900&q=90",
        "Home": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=900&q=90",
        "Tablets & E-readers": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=90",
        "Wearables": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=900&q=90",
    }
    category_text = (category or "").strip().lower()
    image_url = "https://images.unsplash.com/photo-1505740420928-5e560c06d30e"
    for mapped_name, candidate_url in product_images.items():
        if mapped_name == product_name:
            return f"{candidate_url}?auto=format&fit=crop&w=900&q=90&v=4"
    for category_name, candidate_url in category_images.items():
        if category_text == category_name.lower() or category_name.lower() in category_text:
            image_url = candidate_url
            break
    return f"{image_url}&v=3"


def get_offers_for_product(product_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.current_price, p.original_price, p.rating, p.review_count,
                  p.in_stock, s.name AS store_name, s.delivery_days, s.trust_score
              , p.store_url
           FROM prices p JOIN stores s ON p.store_id = s.store_id
           WHERE p.product_id = ?""",
        (product_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_price_history(product_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT ph.recorded_on, ph.price, s.name AS store_name
           FROM price_history ph JOIN stores s ON ph.store_id = s.store_id
           WHERE ph.product_id = ? ORDER BY ph.recorded_on""",
        (product_id,),
    ).fetchall()
    conn.close()

    history = {}
    for r in rows:
        history.setdefault(r["store_name"], []).append(
            {"date": r["recorded_on"], "price": r["price"]}
        )
    return history


def get_product(product_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT product_id, name, category, image_emoji, description, specs FROM products WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    product = dict(row)
    product["image_url"] = product_image_url(product["category"], product["name"])
    try:
        product["specs"] = json.loads(product["specs"] or "{}")
    except (TypeError, ValueError):
        product["specs"] = {}
    return product


def get_wishlist_ids(user_id):
    conn = get_connection()
    rows = conn.execute("SELECT product_id FROM wishlist WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    return {row["product_id"] for row in rows}


def get_products_by_ids(product_ids):
    if not product_ids:
        return []
    placeholders = ",".join("?" for _ in product_ids)
    conn = get_connection()
    rows = conn.execute(
        f"""SELECT p.product_id, p.name, p.category, p.image_emoji, p.description,
                   MIN(pr.current_price) AS best_price,
                   MAX(pr.rating) AS rating,
                   MAX(CASE WHEN pr.original_price > 0
                       THEN ROUND((pr.original_price - pr.current_price) * 100.0 / pr.original_price, 0)
                       ELSE 0 END) AS discount_pct
            FROM products p LEFT JOIN prices pr ON pr.product_id = p.product_id
            WHERE p.product_id IN ({placeholders})
            GROUP BY p.product_id""",
        product_ids,
    ).fetchall()
    conn.close()
    products = decorate_products(rows)
    order = {product_id: index for index, product_id in enumerate(product_ids)}
    return sorted(products, key=lambda product: order[product["product_id"]])


def price_trend(history):
    """Overall trend across stores: compare avg of last 7 days vs prior 7 days."""
    all_points = [p for series in history.values() for p in series]
    if len(all_points) < 2:
        return {"direction": "flat", "change_pct": 0.0}

    by_date = {}
    for p in all_points:
        by_date.setdefault(p["date"], []).append(p["price"])
    dates = sorted(by_date.keys())
    daily_avg = [sum(by_date[d]) / len(by_date[d]) for d in dates]

    recent = daily_avg[-7:]
    prior = daily_avg[-14:-7] if len(daily_avg) >= 14 else daily_avg[:-7]
    if not prior:
        prior = [daily_avg[0]]

    recent_avg = sum(recent) / len(recent)
    prior_avg = sum(prior) / len(prior)
    change_pct = round(((recent_avg - prior_avg) / prior_avg) * 100, 1) if prior_avg else 0.0

    direction = "flat"
    if change_pct > 1:
        direction = "up"
    elif change_pct < -1:
        direction = "down"
    return {"direction": direction, "change_pct": change_pct}


# ---------- Routes ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_connection()
        user = conn.execute(
            "SELECT user_id, name, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["user_name"] = user["name"]
            next_page = request.args.get("next") or url_for("index")
            return redirect(next_page if next_page.startswith("/") else url_for("index"))

        flash("That email or password is incorrect.", "error")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 6:
            flash("Enter your name and email, and use a password with at least 6 characters.", "error")
            return render_template("signup.html")

        conn = get_connection()
        try:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            conn.commit()
        except Exception:
            conn.close()
            flash("An account with that email already exists.", "error")
            return render_template("signup.html")
        conn.close()

        session.clear()
        session["user_id"] = cursor.lastrowid
        session["user_name"] = name
        return redirect(url_for("index"))

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    products = get_all_products()
    categories = sorted({product["category"] for product in products})
    wishlist_ids = get_wishlist_ids(session["user_id"])
    return render_template("index.html", products=products, categories=categories, wishlist_ids=wishlist_ids)


@app.route("/api/search")
@login_required
def api_search():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    results = search_products(query, category) if query or category else get_all_products()
    return jsonify(results)


@app.route("/product/<int:product_id>")
@login_required
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        return "Product not found", 404

    offers = get_offers_for_product(product_id)
    offers = score_offers(offers)
    history = get_price_history(product_id)
    trend = price_trend(history)
    product["is_wishlisted"] = product_id in get_wishlist_ids(session["user_id"])

    return render_template(
        "results.html",
        product=product,
        offers=offers,
        history=history,
        trend=trend,
    )


@app.route("/api/wishlist", methods=["POST"])
@login_required
def toggle_wishlist():
    data = request.get_json(force=True)
    try:
        product_id = int(data.get("product_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "A valid product_id is required"}), 400

    action = data.get("action", "add")
    conn = get_connection()
    product = conn.execute("SELECT product_id FROM products WHERE product_id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({"error": "Product not found"}), 404
    if action == "remove":
        conn.execute("DELETE FROM wishlist WHERE user_id = ? AND product_id = ?", (session["user_id"], product_id))
        saved = False
    else:
        conn.execute("INSERT OR IGNORE INTO wishlist (user_id, product_id) VALUES (?, ?)", (session["user_id"], product_id))
        saved = True
    conn.commit()
    conn.close()
    return jsonify({"saved": saved})


@app.route("/dashboard")
@login_required
def dashboard():
    wishlist = get_products_by_ids(list(get_wishlist_ids(session["user_id"])))
    conn = get_connection()
    alerts = conn.execute(
        """SELECT a.alert_id, a.target_price, a.email, a.created_on, a.triggered,
                  p.name, p.product_id
           FROM price_alerts a JOIN products p ON p.product_id = a.product_id
           WHERE a.user_id = ? ORDER BY a.created_on DESC""",
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", wishlist=wishlist, alerts=[dict(alert) for alert in alerts])


@app.route("/compare")
@login_required
def compare():
    raw_ids = request.args.get("ids", "")
    product_ids = []
    for value in raw_ids.split(","):
        try:
            product_id = int(value)
        except ValueError:
            continue
        if product_id not in product_ids:
            product_ids.append(product_id)
    product_ids = product_ids[:3]
    products = get_products_by_ids(product_ids)
    comparisons = []
    for product in products:
        offers = score_offers(get_offers_for_product(product["product_id"]))
        best = min(offers, key=lambda offer: offer["current_price"]) if offers else None
        comparisons.append({"product": product, "best": best, "offers": offers})
    return render_template("compare.html", comparisons=comparisons)


@app.route("/api/alert", methods=["POST"])
@login_required
def create_alert():
    data = request.get_json(force=True)
    product_id = data.get("product_id")
    target_price = data.get("target_price")
    email = data.get("email", "")

    if not product_id or not target_price:
        return jsonify({"error": "product_id and target_price are required"}), 400

    conn = get_connection()
    conn.execute(
        "INSERT INTO price_alerts (user_id, product_id, target_price, email) VALUES (?, ?, ?, ?)",
        (session["user_id"], product_id, target_price, email),
    )
    conn.commit()

    # Check immediately whether any current offer already qualifies
    offers = get_offers_for_product(product_id)
    best_price = min(o["current_price"] for o in offers) if offers else None
    already_triggered = best_price is not None and best_price <= float(target_price)
    conn.close()

    return jsonify({
        "status": "created",
        "already_triggered": already_triggered,
        "best_current_price": best_price,
    })


@app.route("/api/discount-calc")
@login_required
def discount_calc():
    """?original=1000&final=850  ->  discount amount + percent"""
    try:
        original = float(request.args.get("original"))
        final = float(request.args.get("final"))
    except (TypeError, ValueError):
        return jsonify({"error": "original and final must be numbers"}), 400

    if original <= 0:
        return jsonify({"error": "original must be > 0"}), 400

    discount_amount = round(original - final, 2)
    discount_pct = round((discount_amount / original) * 100, 2)
    return jsonify({
        "original_price": original,
        "final_price": final,
        "discount_amount": discount_amount,
        "discount_percent": discount_pct,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
