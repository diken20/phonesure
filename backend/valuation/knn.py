"""K-Nearest Neighbors (Cover and Hart, 1967) for market price check and similar phones.

Idea: a phone is worth about what the most similar phones are being sold for.
  1. Turn every phone into a vector of numbers (model price tier, age, condition, battery).
  2. Min-max normalise every column to 0..1 so big numbers (price) do not drown small ones (battery %).
  3. Measure the weighted Euclidean distance from the target phone to every listed phone.
  4. Take the K closest phones. Market price = average of their asking prices.

Pure Python (no Django, no ML library) so it is easy to test and explain.
"""
import math
from dataclasses import dataclass

K = 3
CONDITION_SCORE = {"poor": 1, "fair": 2, "good": 3, "excellent": 4}
# Order of the vector: base price (model tier), age bracket, condition, battery health.
# The model tier counts double so an iPhone 13 is compared with iPhone 13s first.
WEIGHTS = (2.0, 1.0, 1.0, 1.0)


def age_bucket(age_years):
    """Use the middle of the same age brackets as the price formula, so phones compare fairly."""
    if age_years < 1:
        return 0.5
    if age_years < 2:
        return 1.5
    if age_years < 3:
        return 2.5
    return 4.0


def to_vector(base_price, age_years, condition, battery_health):
    return [float(base_price), age_bucket(age_years), float(CONDITION_SCORE[condition]), float(battery_health)]


def normalize(vectors):
    """Min-max scale each column to 0..1. A column where every value is equal becomes 0."""
    columns = list(zip(*vectors))
    lows = [min(c) for c in columns]
    highs = [max(c) for c in columns]
    return [
        [(v - lo) / (hi - lo) if hi > lo else 0.0 for v, lo, hi in zip(vec, lows, highs)]
        for vec in vectors
    ]


def distance(a, b, weights=WEIGHTS):
    """Weighted Euclidean distance."""
    return math.sqrt(sum(w * (x - y) ** 2 for w, x, y in zip(weights, a, b)))


def nearest(target, candidates, k=K):
    """candidates = [(vector, payload), ...]. Returns [(distance, payload), ...], closest first."""
    if not candidates:
        return []
    scaled = normalize([target] + [vec for vec, _ in candidates])  # scale together, so one common scale
    scaled_target, scaled_candidates = scaled[0], scaled[1:]
    ranked = sorted(
        ((distance(scaled_target, vec), i) for i, vec in enumerate(scaled_candidates)),
        key=lambda pair: pair[0],
    )
    return [(d, candidates[i][1]) for d, i in ranked[:k]]


@dataclass(frozen=True)
class MarketCheck:
    price: int          # average asking price of the K nearest phones (rounded to Rs. 100)
    neighbors: tuple    # the K nearest payloads (phones), closest first


def market_check(target, candidates, price_of, k=K):
    """Average asking price of the k most similar phones.

    Returns None when there are fewer than k candidates: then there is not enough
    market data and the app falls back to the formula price only.
    """
    if len(candidates) < k:
        return None
    neighbors = [payload for _, payload in nearest(target, candidates, k)]
    average = sum(price_of(p) for p in neighbors) / len(neighbors)
    return MarketCheck(price=int(round(average / 100.0)) * 100, neighbors=tuple(neighbors))
