from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from phones.models import PhoneModelReference

from . import engine


class EngineTests(SimpleTestCase):
    def test_worked_example_from_design(self):
        v = engine.estimate(85000, 1.5, "good", 86, has_box=True, has_charger=True)
        self.assertEqual(v.estimate, 62774)
        self.assertEqual([s.amount for s in v.steps], [-12750, -7225, -3251, 1000])
        self.assertEqual((v.low, v.high), (58400, 67200))

    def test_steps_add_up_to_estimate(self):
        v = engine.estimate(50000, 3.5, "fair", 65, has_bill=True)
        self.assertEqual(v.base_price + sum(s.amount for s in v.steps), v.estimate)

    def test_age_boundaries(self):
        self.assertEqual(engine.age_factor(0.99)[0], 1.0)
        self.assertEqual(engine.age_factor(1)[0], 0.85)
        self.assertEqual(engine.age_factor(2)[0], 0.72)
        self.assertEqual(engine.age_factor(3)[0], 0.60)

    def test_battery_boundaries(self):
        self.assertEqual(engine.battery_factor(90), 1.0)
        self.assertEqual(engine.battery_factor(89), 0.95)
        self.assertEqual(engine.battery_factor(70), 0.88)
        self.assertEqual(engine.battery_factor(69), 0.78)

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):
            engine.estimate(85000, 1, "broken", 80)
        with self.assertRaises(ValueError):
            engine.estimate(85000, 1, "good", 101)
        with self.assertRaises(ValueError):
            engine.estimate(0, 1, "good", 80)

    def test_verdict(self):
        v = engine.estimate(85000, 1.5, "good", 86)
        self.assertEqual(v.verdict(v.low - 1), "below")
        self.assertEqual(v.verdict(v.estimate), "within")
        self.assertEqual(v.verdict(v.high + 1), "above")


class ValuationApiTests(APITestCase):
    def setUp(self):
        self.ref = PhoneModelReference.objects.create(
            brand="Apple", model_name="iPhone 13", storage_gb=128, base_price=85000)
        self.url = "/api/valuation/"

    def payload(self, **extra):
        data = {"reference": self.ref.pk, "age_years": 1.5, "condition": "good",
                "battery_health": 86, "has_box": True, "has_charger": True}
        data.update(extra)
        return data

    def test_public_calculation(self):
        r = self.client.post(self.url, self.payload(asking_price=62000), format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["estimate"], 62774)
        self.assertEqual((r.data["low"], r.data["high"]), (58400, 67200))
        self.assertEqual(r.data["verdict"], "within")
        self.assertEqual(len(r.data["steps"]), 4)

    def test_verdict_is_none_without_price(self):
        r = self.client.post(self.url, self.payload(), format="json")
        self.assertIsNone(r.data["verdict"])

    def test_invalid_battery_rejected(self):
        r = self.client.post(self.url, self.payload(battery_health=150), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("battery_health", r.data)

    def test_unknown_phone_rejected(self):
        r = self.client.post(self.url, self.payload(reference=9999), format="json")
        self.assertEqual(r.status_code, 400)

    def test_reference_list_is_public(self):
        r = self.client.get("/api/references/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data[0]["label"], "Apple iPhone 13 128GB")


class MarketCheckApiTests(APITestCase):
    """KNN market check inside the calculator."""

    def setUp(self):
        from accounts.models import User
        from phones.models import Phone
        self.ref = PhoneModelReference.objects.create(brand="Apple", model_name="iPhone 13", storage_gb=128, base_price=85000)
        self.seller = User.objects.create_user("s", password="pw12345678", role="seller")
        self.Phone = Phone

    def listing(self, price, status="listed"):
        return self.Phone.objects.create(owner=self.seller, reference=self.ref, purchase_year=2025, condition="good",
                                         battery_health=86, asking_price=price, status=status)

    def post(self):
        return self.client.post("/api/valuation/", {"reference": self.ref.pk, "age_years": 1.5,
                                "condition": "good", "battery_health": 86}, format="json")

    def test_no_market_data_returns_none(self):
        self.listing(60000); self.listing(62000)  # only 2, K is 3
        self.assertIsNone(self.post().data["market"])

    def test_market_price_from_three_listings(self):
        for price in (60000, 62000, 64000):
            self.listing(price)
        market = self.post().data["market"]
        self.assertEqual(market, {"price": 62000, "count": 3})

    def test_drafts_are_ignored(self):
        for price in (60000, 62000):
            self.listing(price)
        self.listing(99000, status="draft")
        self.assertIsNone(self.post().data["market"])
