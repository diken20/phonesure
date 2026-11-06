"""PhoneSure valuation engine.

Estimated Price = Base Price x Age Factor x Condition Factor x Battery Factor
                  + Accessories Bonus

Pure Python (no Django imports) so it is easy to test and to explain in a viva.
Factor values are starting points: confirm them with local mobile shop owners.
"""
from dataclasses import dataclass

CONDITION_FACTORS = {"excellent": 1.0, "good": 0.9, "fair": 0.75, "poor": 0.55}
ACCESSORY_BONUS = {"box": 500, "charger": 500, "bill": 1000}
RANGE_PERCENT = 0.07  # fair range = estimate -7% .. +7%


@dataclass(frozen=True)
class Step:
    label: str
    amount: int  # negative = price reduced, positive = price increased


@dataclass(frozen=True)
class Valuation:
    base_price: int
    steps: tuple
    estimate: int
    low: int
    high: int

    def verdict(self, price):
        """Compare an asking price with the fair range."""
        if price < self.low:
            return "below"
        if price > self.high:
            return "above"
        return "within"


def age_factor(age_years):
    """Return (factor, label) for the phone's age in years."""
    if age_years < 1:
        return 1.0, "Under 1 year"
    if age_years < 2:
        return 0.85, "1 to 2 years"
    if age_years < 3:
        return 0.72, "2 to 3 years"
    return 0.60, "3 years or more"


def battery_factor(percent):
    if percent >= 90:
        return 1.0
    if percent >= 80:
        return 0.95
    if percent >= 70:
        return 0.88
    return 0.78


def condition_factor(condition):
    try:
        return CONDITION_FACTORS[condition]
    except KeyError:
        raise ValueError(f"Unknown condition: {condition!r}")


def _round_100(value):
    return int(round(value / 100.0)) * 100


def estimate(base_price, age_years, condition, battery_health,
             has_box=False, has_charger=False, has_bill=False):
    """Return a Valuation with a step-by-step price breakdown."""
    if base_price <= 0:
        raise ValueError("Base price must be positive")
    if age_years < 0:
        raise ValueError("Age cannot be negative")
    if not 0 <= battery_health <= 100:
        raise ValueError("Battery health must be between 0 and 100")

    a_factor, a_label = age_factor(age_years)
    c_factor = condition_factor(condition)
    b_factor = battery_factor(battery_health)

    after_age = round(base_price * a_factor)
    after_condition = round(base_price * a_factor * c_factor)
    after_battery = round(base_price * a_factor * c_factor * b_factor)

    bonus = (
        (ACCESSORY_BONUS["box"] if has_box else 0)
        + (ACCESSORY_BONUS["charger"] if has_charger else 0)
        + (ACCESSORY_BONUS["bill"] if has_bill else 0)
    )
    total = after_battery + bonus

    steps = (
        Step(f"Age ({a_label})", after_age - base_price),
        Step(f"Condition ({condition.title()})", after_condition - after_age),
        Step(f"Battery ({battery_health}%)", after_battery - after_condition),
        Step("Accessories and bill", bonus),
    )
    return Valuation(
        base_price=base_price,
        steps=steps,
        estimate=total,
        low=_round_100(total * (1 - RANGE_PERCENT)),
        high=_round_100(total * (1 + RANGE_PERCENT)),
    )
