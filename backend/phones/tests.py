from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from accounts.models import User

from .models import Phone, PhoneModelReference


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get_or_create(user=user)[0].key}")
    return c


class PhoneApiTests(APITestCase):
    def setUp(self):
        self.ref = PhoneModelReference.objects.create(
            brand="Apple", model_name="iPhone 13", storage_gb=128, base_price=85000)
        self.seller = User.objects.create_user("seller1", password="pw12345678", role="seller")
        self.other = User.objects.create_user("seller2", password="pw12345678", role="seller")
        self.buyer = User.objects.create_user("buyer1", password="pw12345678", role="buyer")
        self.phone = Phone.objects.create(
            owner=self.seller, reference=self.ref, purchase_year=2025, condition="good",
            battery_health=86, asking_price=62000)

    def body(self, **extra):
        data = {"reference": self.ref.pk, "purchase_year": 2025, "condition": "good",
                "battery_health": 90, "warranty_months": 3, "asking_price": 60000, "status": "draft"}
        data.update(extra)
        return data

    def test_anonymous_gets_401(self):
        self.assertEqual(self.client.get("/api/phones/").status_code, 401)

    def test_buyer_gets_403(self):
        c = client_for(self.buyer)
        self.assertEqual(c.get("/api/phones/").status_code, 403)
        self.assertEqual(c.post("/api/phones/", self.body(), format="json").status_code, 403)

    def test_seller_sees_only_own_phones(self):
        self.assertEqual(len(client_for(self.seller).get("/api/phones/").data), 1)
        self.assertEqual(len(client_for(self.other).get("/api/phones/").data), 0)

    def test_list_includes_valuation(self):
        item = client_for(self.seller).get("/api/phones/").data[0]
        self.assertIn("low", item["valuation"])
        self.assertEqual(item["reference_label"], "Apple iPhone 13 128GB")

    def test_seller_can_create_and_owner_is_set(self):
        r = client_for(self.seller).post("/api/phones/", self.body(), format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Phone.objects.get(pk=r.data["id"]).owner, self.seller)


    def test_seller_can_create_phone_from_manual_brand_fields_without_reference_id(self):
        payload = {
            "brand": "Google", "model_name": "Pixel 8", "storage_gb": 128,
            "base_price": 90000, "purchase_year": 2025, "condition": "good",
            "battery_health": 90, "warranty_months": 0, "asking_price": 65000,
            "status": "draft",
        }
        response = client_for(self.seller).post("/api/phones/", payload, format="json")
        self.assertEqual(response.status_code, 201, response.data)
        created = Phone.objects.get(pk=response.data["id"])
        self.assertEqual(created.owner, self.seller)
        self.assertEqual(created.reference.brand, "Google")
        self.assertEqual(created.reference.model_name, "Pixel 8")

    def test_invalid_battery_rejected(self):
        r = client_for(self.seller).post("/api/phones/", self.body(battery_health=150), format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Phone.objects.count(), 1)

    def test_seller_can_update(self):
        r = client_for(self.seller).patch(f"/api/phones/{self.phone.pk}/", {"asking_price": 55000}, format="json")
        self.assertEqual(r.status_code, 200)
        self.phone.refresh_from_db()
        self.assertEqual(self.phone.asking_price, 55000)

    def test_cannot_touch_others_phone(self):
        c = client_for(self.other)
        url = f"/api/phones/{self.phone.pk}/"
        self.assertEqual(c.get(url).status_code, 404)
        self.assertEqual(c.patch(url, {"asking_price": 1}, format="json").status_code, 404)
        self.assertEqual(c.delete(url).status_code, 404)
        self.assertTrue(Phone.objects.filter(pk=self.phone.pk).exists())

    def test_owner_can_delete(self):
        r = client_for(self.seller).delete(f"/api/phones/{self.phone.pk}/")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Phone.objects.filter(pk=self.phone.pk).exists())

    def test_photo_is_null_when_missing(self):
        item = client_for(self.seller).get("/api/phones/").data[0]
        self.assertIsNone(item["photo"])
