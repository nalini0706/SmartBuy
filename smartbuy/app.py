"""
SmartBuy — AI-Based Product Price Comparison & Deal Recommendation System
Flow: User -> Search Product -> Collect Prices -> Compare -> Analyze Deals -> Recommend Best Option
"""
from flask import Flask, render_template, request, jsonify
from database import get_connection
from recommend import score_offers
import datetime

app = Flask(__name__)


# ---------- Data access helpers ----------

def search_products(query):
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT product_id, name, category, image_emoji FROM products "
        "WHERE name LIKE ? ORDER BY name",
        (f"%{query}%",),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_products():
    conn = get_connection()
    rows = conn.execute(
        "SELECT product_id, name, category, image_emoji FROM products ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_offers_for_product(product_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT p.current_price, p.original_price, p.rating, p.review_count,
                  p.in_stock, s.name AS store_name, s.delivery_days, s.trust_score
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
        "SELECT product_id, name, category, image_emoji FROM products WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


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

@app.route("/")
def index():
    products = get_all_products()
    return render_template("index.html", products=products)


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    results = search_products(query) if query else get_all_products()
    return jsonify(results)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        return "Product not found", 404

    offers = get_offers_for_product(product_id)
    offers = score_offers(offers)
    history = get_price_history(product_id)
    trend = price_trend(history)

    return render_template(
        "results.html",
        product=product,
        offers=offers,
        history=history,
        trend=trend,
    )


@app.route("/api/alert", methods=["POST"])
def create_alert():
    data = request.get_json(force=True)
    product_id = data.get("product_id")
    target_price = data.get("target_price")
    email = data.get("email", "")

    if not product_id or not target_price:
        return jsonify({"error": "product_id and target_price are required"}), 400

    conn = get_connection()
    conn.execute(
        "INSERT INTO price_alerts (product_id, target_price, email) VALUES (?, ?, ?)",
        (product_id, target_price, email),
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
