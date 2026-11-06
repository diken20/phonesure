from django.test import SimpleTestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from phones.models import Phone, PhoneModelReference

from .kmp import build_failure_table, kmp_contains, kmp_find, matches_all_terms


class KmpTests(SimpleTestCase):
    def test_failure_table(self):
        self.assertEqual(build_failure_table("ABABCABAB"), [0, 0, 1, 2, 0, 1, 2, 3, 4])

    def test_classic_example(self):
        self.assertEqual(kmp_find("ABABDABACDABABCABAB", "ABABCABAB"), 10)

    def test_not_found(self):
        self.assertEqual(kmp_find("iphone 13", "samsung"), -1)

    def test_case_insensitive(self):
        self.assertTrue(kmp_contains("Apple iPhone 13 128GB", "IPHONE"))

    def test_empty_pattern_and_short_text(self):
        self.assertEqual(kmp_find("abc", ""), 0)
        self.assertEqual(kmp_find("ab", "abc"), -1)

    def test_all_terms_must_match_in_any_order(self):
        self.assertTrue(matches_all_terms("Apple iPhone 13 128GB good", "128gb iphone"))
        self.assertFalse(matches_all_terms("Apple iPhone 13 128GB good", "iphone samsung"))


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get_or_create(user=user)[0].key}")
    return c


class MarketplaceApiTests(APITestCase):
    def setUp(self):
        self.iphone = PhoneModelReference.objects.create(brand="Apple", model_name="iPhone 13", storage_gb=128, base_price=85000)
        self.redmi = PhoneModelReference.objects.create(brand="Xiaomi", model_name="Redmi Note 12", storage_gb=128, base_price=32000)
        self.seller = User.objects.create_user("seller1", password="pw12345678", role="seller")
        self.buyer = User.objects.create_user("buyer1", password="pw12345678", role="buyer")
        self.make(self.iphone, 62000, "listed")
        self.make(self.redmi, 25000, "listed")
        self.make(self.iphone, 50000, "draft")  # drafts must stay hidden

    def make(self, ref, price, status):
        return Phone.objects.create(owner=self.seller, reference=ref, purchase_year=2025, condition="good",
                                    battery_health=86, asking_price=price, status=status, has_bill=True)

    def get(self, **params):
        return client_for(self.buyer).get("/api/marketplace/", params)

    def test_login_required(self):
        self.assertEqual(self.client.get("/api/marketplace/").status_code, 401)

    def test_buyer_sees_only_listed_phones(self):
        r = self.get()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data), 2)

    def test_no_seller_details_exposed(self):
        item = self.get().data[0]
        self.assertNotIn("owner", item)
        self.assertNotIn("seller1", str(item))

    def test_card_fields(self):
        item = [i for i in self.get().data if i["brand"] == "Apple"][0]
        self.assertEqual(item["title"], "iPhone 13, 128 GB")
        self.assertEqual(item["asking_price"], 62000)
        self.assertIn(item["price_verdict"], ("within", "above", "below"))
        self.assertGreaterEqual(item["trust_score"], 0)
        self.assertIsNone(item["photo"])

    def test_keyword_search(self):
        r = self.get(q="redmi")
        self.assertEqual([i["brand"] for i in r.data], ["Xiaomi"])

    def test_brand_filter(self):
        self.assertEqual(len(self.get(brand="apple").data), 1)

    def test_max_price_filter(self):
        r = self.get(max_price=30000)
        self.assertEqual([i["asking_price"] for i in r.data], [25000])

    def test_filters_combine(self):
        self.assertEqual(len(self.get(q="iphone", max_price=30000).data), 0)

    def test_bad_max_price_rejected(self):
        self.assertEqual(self.get(max_price="abc").status_code, 400)


class ListingDetailApiTests(APITestCase):
    def setUp(self):
        self.ref = PhoneModelReference.objects.create(brand="Apple", model_name="iPhone 13", storage_gb=128, base_price=85000)
        self.seller = User.objects.create_user("seller1", password="pw12345678", role="seller")
        self.buyer = User.objects.create_user("buyer1", password="pw12345678", role="buyer")
        self.phones = [
            Phone.objects.create(owner=self.seller, reference=self.ref, purchase_year=2025, condition="good",
                                 battery_health=80 + i, asking_price=60000 + i * 1000, status="listed", has_bill=True)
            for i in range(5)
        ]
        self.draft = Phone.objects.create(owner=self.seller, reference=self.ref, purchase_year=2025, condition="good",
                                          battery_health=86, asking_price=50000, status="draft")

    def get(self, pk):
        return client_for(self.buyer).get(f"/api/marketplace/{pk}/")

    def test_login_required(self):
        self.assertEqual(self.client.get(f"/api/marketplace/{self.phones[0].pk}/").status_code, 401)

    def test_draft_is_not_visible(self):
        self.assertEqual(self.get(self.draft.pk).status_code, 404)

    def test_detail_has_trust_breakdown_and_no_owner(self):
        r = self.get(self.phones[0].pk)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.data["trust_details"]), 7)
        self.assertNotIn("owner", r.data)
        self.assertNotIn("seller1", str(r.data))

    def test_similar_phones_use_knn_and_exclude_itself(self):
        r = self.get(self.phones[0].pk)
        similar_ids = [p["id"] for p in r.data["similar"]]
        self.assertEqual(len(similar_ids), 3)
        self.assertNotIn(self.phones[0].pk, similar_ids)
        self.assertNotIn(self.draft.pk, similar_ids)
        # battery 80 is closest to 81, then 82, then 83 (all else identical)
        self.assertEqual(similar_ids, [self.phones[1].pk, self.phones[2].pk, self.phones[3].pk])

    def test_market_price_is_average_of_three_nearest(self):
        r = self.get(self.phones[0].pk)
        self.assertEqual(r.data["market"], {"price": 62000, "count": 3})  # 61000, 62000, 63000
