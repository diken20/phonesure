"""Rule-based trust score out of 100 (pure Python, easy to test and explain)."""

RULES = [
    ("Original bill available", 20),
    ("Warranty remaining", 15),
    ("Battery health above 80%", 20),
    ("No repairs", 20),
    ("Original box", 5),
    ("Original charger", 5),
    ("Photo added", 15),
]  # points add up to 100


def trust_score(*, has_bill, warranty_months, battery_health, repairs_done,
                has_box, has_charger, has_photo):
    """Return (score, items). Each item says what was checked and whether points were earned."""
    passed = [
        bool(has_bill),
        warranty_months > 0,
        battery_health > 80,
        not repairs_done,
        bool(has_box),
        bool(has_charger),
        bool(has_photo),
    ]
    items = [
        {"label": label, "points": points, "earned": ok}
        for (label, points), ok in zip(RULES, passed)
    ]
    return sum(i["points"] for i in items if i["earned"]), items
