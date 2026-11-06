from django.test import SimpleTestCase

from .trust import RULES, trust_score

FULL = dict(has_bill=True, warranty_months=6, battery_health=90, repairs_done=False,
            has_box=True, has_charger=True, has_photo=True)


class TrustScoreTests(SimpleTestCase):
    def test_rules_add_up_to_100(self):
        self.assertEqual(sum(points for _, points in RULES), 100)

    def test_perfect_listing(self):
        self.assertEqual(trust_score(**FULL)[0], 100)

    def test_empty_listing(self):
        score, _ = trust_score(has_bill=False, warranty_months=0, battery_health=50,
                               repairs_done=True, has_box=False, has_charger=False, has_photo=False)
        self.assertEqual(score, 0)

    def test_battery_must_be_above_80(self):
        self.assertEqual(trust_score(**{**FULL, "battery_health": 80})[0], 80)
        self.assertEqual(trust_score(**{**FULL, "battery_health": 81})[0], 100)

    def test_repairs_cost_points(self):
        self.assertEqual(trust_score(**{**FULL, "repairs_done": True})[0], 80)

    def test_items_explain_the_score(self):
        _, items = trust_score(**{**FULL, "has_bill": False})
        bill = [i for i in items if i["label"].startswith("Original bill")][0]
        self.assertFalse(bill["earned"])
