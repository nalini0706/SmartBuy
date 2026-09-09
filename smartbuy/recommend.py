"""
SmartBuy — Deal Recommendation Engine
Scores each store's offer using price + rating + delivery speed + discount,
instead of just picking the cheapest price.
"""

# Tunable weights (must sum to 1.0)
WEIGHTS = {
    "price": 0.45,
    "rating": 0.25,
    "delivery": 0.15,
    "discount": 0.15,
}


def _normalize(value, min_v, max_v, invert=False):
    """Scale value to 0-1. If invert=True, lower raw value -> higher score."""
    if max_v == min_v:
        return 1.0
    score = (value - min_v) / (max_v - min_v)
    return 1 - score if invert else score


def score_offers(offers):
    """
    offers: list of dicts with keys:
        store_name, current_price, original_price, rating,
        delivery_days, in_stock
    Returns the same list, each augmented with:
        discount_pct, deal_score (0-100), is_best_price, is_best_deal
    """
    if not offers:
        return []

    prices = [o["current_price"] for o in offers]
    ratings = [o["rating"] for o in offers]
    deliveries = [o["delivery_days"] for o in offers]

    min_price, max_price = min(prices), max(prices)
    min_rating, max_rating = min(ratings), max(ratings)
    min_delivery, max_delivery = min(deliveries), max(deliveries)

    for o in offers:
        o["discount_pct"] = round(
            (1 - o["current_price"] / o["original_price"]) * 100, 1
        ) if o["original_price"] > 0 else 0.0

        price_score = _normalize(o["current_price"], min_price, max_price, invert=True)
        rating_score = _normalize(o["rating"], min_rating, max_rating, invert=False)
        delivery_score = _normalize(o["delivery_days"], min_delivery, max_delivery, invert=True)
        discount_score = min(o["discount_pct"] / 20.0, 1.0)  # cap benefit at 20%+ discount

        raw_score = (
            WEIGHTS["price"] * price_score
            + WEIGHTS["rating"] * rating_score
            + WEIGHTS["delivery"] * delivery_score
            + WEIGHTS["discount"] * discount_score
        )

        # Out-of-stock offers are heavily penalized but still shown
        if not o.get("in_stock", True):
            raw_score *= 0.3

        o["deal_score"] = round(raw_score * 100, 1)

    best_price_val = min_price
    best_deal = max(offers, key=lambda o: o["deal_score"])

    for o in offers:
        o["is_best_price"] = (o["current_price"] == best_price_val)
        o["is_best_deal"] = (o is best_deal)
        o["price_diff_vs_best"] = round(o["current_price"] - best_price_val, 2)

    # Sort by price ascending for the comparison table
    offers.sort(key=lambda o: o["current_price"])
    return offers
