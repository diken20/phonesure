from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from orders.models import Order, OrderItem, ProblemReport
from phones.models import Phone, PhoneModelReference


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get_or_create(user=user)[0].key}")
    return c


class PortalTestCase(APITestCase):
    def setUp(self):
        self.ref = PhoneModelReference.objects.create(brand="Apple", model_name="iPhone 13", storage_gb=128, base_price=85000)
        self.admin = User.objects.create_superuser("boss", "boss@example.com", "pw12345678")
        self.seller = User.objects.create_user("seller1", password="pw12345678", role="seller")
        self.buyer = User.objects.create_user("buyer1", password="pw12345678", role="buyer")
        self.ac, self.sc, self.bc = client_for(self.admin), client_for(self.seller), client_for(self.buyer)

    def body(self, **extra):
        data = {"reference": self.ref.pk, "purchase_year": 2025, "condition": "good", "battery_health": 86,
                "warranty_months": 3, "asking_price": 62000}
        data.update(extra)
        return data

    def submit(self, **extra):
        return self.sc.post("/api/phones/", self.body(status="pending", **extra), format="json").data["id"]

    def marketplace_ids(self):
        return [p["id"] for p in self.bc.get("/api/marketplace/").data]


class ApprovalWorkflowTests(PortalTestCase):
    def test_seller_submission_is_hidden_until_admin_approves(self):
        phone_id = self.submit()
        self.assertEqual(Phone.objects.get(pk=phone_id).status, "pending")
        self.assertNotIn(phone_id, self.marketplace_ids())
        r = self.ac.post(f"/api/admin/phones/{phone_id}/approve/")
        self.assertEqual((r.status_code, r.data["status"]), (200, "listed"))
        self.assertIn(phone_id, self.marketplace_ids())

    def test_draft_is_not_reviewable_or_visible(self):
        phone_id = self.sc.post("/api/phones/", self.body(), format="json").data["id"]
        self.assertEqual(Phone.objects.get(pk=phone_id).status, "draft")
        self.assertEqual(self.ac.post(f"/api/admin/phones/{phone_id}/approve/").status_code, 400)

    def test_seller_cannot_publish_directly(self):
        self.assertEqual(self.sc.post("/api/phones/", self.body(status="listed"), format="json").status_code, 400)
        phone_id = self.submit()
        self.assertEqual(self.sc.patch(f"/api/phones/{phone_id}/", {"status": "listed"}, format="json").status_code, 400)

    def test_rejection_needs_a_reason_and_seller_sees_it(self):
        phone_id = self.submit()
        self.assertEqual(self.ac.post(f"/api/admin/phones/{phone_id}/reject/", {"note": ""}, format="json").status_code, 400)
        r = self.ac.post(f"/api/admin/phones/{phone_id}/reject/", {"note": "Photo is missing"}, format="json")
        self.assertEqual(r.data["status"], "rejected")
        mine = self.sc.get(f"/api/phones/{phone_id}/").data
        self.assertEqual((mine["status"], mine["review_note"]), ("rejected", "Photo is missing"))
        self.assertNotIn(phone_id, self.marketplace_ids())

    def test_resubmitting_after_rejection_clears_the_note(self):
        phone_id = self.submit()
        self.ac.post(f"/api/admin/phones/{phone_id}/reject/", {"note": "Photo is missing"}, format="json")
        r = self.sc.patch(f"/api/phones/{phone_id}/", {"status": "pending"}, format="json")
        self.assertEqual((r.data["status"], r.data["review_note"]), ("pending", ""))

    def test_editing_a_live_listing_needs_approval_again(self):
        phone_id = self.submit()
        self.ac.post(f"/api/admin/phones/{phone_id}/approve/")
        r = self.sc.patch(f"/api/phones/{phone_id}/", {"asking_price": 50000}, format="json")
        self.assertEqual(r.data["status"], "pending")
        self.assertNotIn(phone_id, self.marketplace_ids())

    def test_seller_can_take_a_live_listing_back_to_draft(self):
        phone_id = self.submit()
        self.ac.post(f"/api/admin/phones/{phone_id}/approve/")
        self.sc.patch(f"/api/phones/{phone_id}/", {"status": "draft"}, format="json")
        self.assertNotIn(phone_id, self.marketplace_ids())

    def test_admin_can_take_down_a_live_phone(self):
        phone_id = self.submit()
        self.ac.post(f"/api/admin/phones/{phone_id}/approve/")
        r = self.ac.post(f"/api/admin/phones/{phone_id}/reject/", {"note": "Suspicious price"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn(phone_id, self.marketplace_ids())

    def test_cannot_approve_twice_or_reject_sold(self):
        phone_id = self.submit()
        self.ac.post(f"/api/admin/phones/{phone_id}/approve/")
        self.assertEqual(self.ac.post(f"/api/admin/phones/{phone_id}/approve/").status_code, 400)
        Phone.objects.filter(pk=phone_id).update(status="sold")
        self.assertEqual(self.ac.post(f"/api/admin/phones/{phone_id}/reject/", {"note": "too late now"}, format="json").status_code, 400)

    def test_review_queue_defaults_to_pending_oldest_first(self):
        first, second = self.submit(), self.submit()
        self.sc.post("/api/phones/", self.body(), format="json")  # a draft, must not appear
        rows = self.ac.get("/api/admin/phones/").data
        self.assertEqual([r["id"] for r in rows], [first, second])
        self.assertEqual(rows[0]["seller"], "seller1")
        self.assertIn("fair_low", rows[0])
        self.assertEqual(len(self.ac.get("/api/admin/phones/?status=all").data), 3)

    def test_deactivated_seller_phones_disappear_and_cannot_be_bought(self):
        phone_id = self.submit()
        self.ac.post(f"/api/admin/phones/{phone_id}/approve/")
        self.bc.post("/api/cart/", {"phone": phone_id}, format="json")
        self.ac.patch(f"/api/admin/users/{self.seller.pk}/", {"is_active": False}, format="json")
        self.assertNotIn(phone_id, self.marketplace_ids())
        self.assertEqual(self.bc.get(f"/api/marketplace/{phone_id}/").status_code, 404)
        self.assertFalse(self.bc.get("/api/cart/").data["items"][0]["available"])
        self.assertEqual(self.bc.post("/api/orders/checkout/").status_code, 409)
        self.ac.patch(f"/api/admin/users/{self.seller.pk}/", {"is_active": True}, format="json")
        self.assertIn(phone_id, self.marketplace_ids())


class PortalAccessTests(PortalTestCase):
    URLS = ["/api/admin/stats/", "/api/admin/phones/", "/api/admin/users/", "/api/admin/references/",
            "/api/admin/orders/", "/api/admin/problems/"]

    def test_anonymous_gets_401(self):
        for url in self.URLS:
            self.assertEqual(self.client.get(url).status_code, 401, url)

    def test_seller_and_buyer_get_403(self):
        for url in self.URLS:
            self.assertEqual(self.sc.get(url).status_code, 403, url)
            self.assertEqual(self.bc.get(url).status_code, 403, url)

    def test_admin_gets_200(self):
        for url in self.URLS:
            self.assertEqual(self.ac.get(url).status_code, 200, url)

    def test_seller_cannot_approve_own_phone(self):
        phone_id = self.submit()
        self.assertEqual(self.sc.post(f"/api/admin/phones/{phone_id}/approve/").status_code, 403)
        self.assertEqual(Phone.objects.get(pk=phone_id).status, "pending")


class StatsTests(PortalTestCase):
    def test_counts_and_revenue(self):
        self.submit()
        approved = self.submit()
        self.ac.post(f"/api/admin/phones/{approved}/approve/")
        order = Order.objects.create(buyer=self.buyer, total=62000, status="paid")
        Order.objects.create(buyer=self.buyer, total=10000, status="review")
        data = self.ac.get("/api/admin/stats/").data
        self.assertEqual(data["users"], {"buyer": 1, "seller": 1, "admin": 1})
        self.assertEqual((data["phones"]["pending"], data["phones"]["listed"]), (1, 1))
        self.assertEqual((data["orders"]["paid"], data["orders"]["review"]), (1, 1))
        self.assertEqual(data["revenue"], 62000)  # only PAID orders count
        self.assertEqual(data["open_problems"], 0)
        self.assertEqual(order.status, "paid")


class UserManagementTests(PortalTestCase):
    def test_deactivated_user_loses_access(self):
        r = self.ac.patch(f"/api/admin/users/{self.buyer.pk}/", {"is_active": False}, format="json")
        self.assertFalse(r.data["is_active"])
        self.assertEqual(self.bc.get("/api/auth/me/").status_code, 401)  # existing token stops working
        login = APIClient().post("/api/auth/login/", {"username": "buyer1", "password": "pw12345678"}, format="json")
        self.assertEqual(login.status_code, 400)

    def test_cannot_change_self_or_other_admins(self):
        self.assertEqual(self.ac.patch(f"/api/admin/users/{self.admin.pk}/", {"is_active": False}, format="json").status_code, 400)
        other = User.objects.create_superuser("boss2", "b2@example.com", "pw12345678")
        self.assertEqual(self.ac.patch(f"/api/admin/users/{other.pk}/", {"is_active": False}, format="json").status_code, 400)

    def test_only_is_active_can_be_changed(self):
        self.ac.patch(f"/api/admin/users/{self.buyer.pk}/", {"role": "admin", "username": "hacked"}, format="json")
        self.buyer.refresh_from_db()
        self.assertEqual((self.buyer.role, self.buyer.username), ("buyer", "buyer1"))

    def test_role_filter_and_counts(self):
        rows = self.ac.get("/api/admin/users/?role=seller").data
        self.assertEqual([r["username"] for r in rows], ["seller1"])
        self.assertEqual(rows[0]["phone_count"], 0)

    def test_users_cannot_be_deleted_or_created_here(self):
        self.assertEqual(self.ac.delete(f"/api/admin/users/{self.buyer.pk}/").status_code, 405)
        self.assertEqual(self.ac.post("/api/admin/users/", {"username": "x"}, format="json").status_code, 405)


class ReferencePriceTests(PortalTestCase):
    def test_crud(self):
        r = self.ac.post("/api/admin/references/", {"brand": "Xiaomi", "model_name": "Redmi 12", "storage_gb": 128, "base_price": 21000}, format="json")
        self.assertEqual((r.status_code, r.data["label"]), (201, "Xiaomi Redmi 12 128GB"))
        rid = r.data["id"]
        self.assertEqual(self.ac.patch(f"/api/admin/references/{rid}/", {"base_price": 19500}, format="json").data["base_price"], 19500)
        self.assertEqual(self.ac.delete(f"/api/admin/references/{rid}/").status_code, 204)

    def test_price_change_moves_the_valuation(self):
        before = self.client.post("/api/valuation/", {"reference": self.ref.pk, "age_years": 1.5, "condition": "good", "battery_health": 86}, format="json").data["estimate"]
        self.ac.patch(f"/api/admin/references/{self.ref.pk}/", {"base_price": 60000}, format="json")
        after = self.client.post("/api/valuation/", {"reference": self.ref.pk, "age_years": 1.5, "condition": "good", "battery_health": 86}, format="json").data["estimate"]
        self.assertLess(after, before)

    def test_duplicate_rejected(self):
        r = self.ac.post("/api/admin/references/", {"brand": "Apple", "model_name": "iPhone 13", "storage_gb": 128, "base_price": 1000}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_zero_price_rejected(self):
        r = self.ac.post("/api/admin/references/", {"brand": "A", "model_name": "B", "storage_gb": 64, "base_price": 0}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_cannot_delete_model_in_use(self):
        self.submit()
        r = self.ac.delete(f"/api/admin/references/{self.ref.pk}/")
        self.assertEqual(r.status_code, 400)
        self.assertTrue(PhoneModelReference.objects.filter(pk=self.ref.pk).exists())
        self.assertEqual(self.ac.get("/api/admin/references/").data[0]["phone_count"], 1)


class OrdersAndProblemsTests(PortalTestCase):
    def setUp(self):
        super().setUp()
        phone = Phone.objects.create(owner=self.seller, reference=self.ref, purchase_year=2025, condition="good",
                                     battery_health=86, asking_price=62000, status="sold")
        self.order = Order.objects.create(buyer=self.buyer, total=62000, status="paid")
        self.item = OrderItem.objects.create(order=self.order, phone=phone, title="Apple iPhone 13 128GB", price=62000)

    def test_orders_list_hides_cancelled_by_default(self):
        Order.objects.create(buyer=self.buyer, total=1, status="cancelled")
        rows = self.ac.get("/api/admin/orders/").data
        self.assertEqual([r["id"] for r in rows], [self.order.id])
        self.assertEqual(rows[0]["buyer"], "buyer1")
        self.assertEqual(rows[0]["items"][0]["title"], "Apple iPhone 13 128GB")

    def test_mark_review_order_as_refunded(self):
        review = Order.objects.create(buyer=self.buyer, total=5000, status="review")
        self.assertEqual(self.ac.post(f"/api/admin/orders/{self.order.pk}/refunded/").status_code, 400)  # paid, not review
        r = self.ac.post(f"/api/admin/orders/{review.pk}/refunded/")
        self.assertEqual(r.data["status"], "refunded")
        self.assertEqual(self.bc.get(f"/api/orders/{review.pk}/").data["status_label"], "Refunded")

    def test_problem_report_handling(self):
        report = ProblemReport.objects.create(item=self.item, reporter=self.buyer, category="battery", description="Battery drains fast")
        row = self.ac.get("/api/admin/problems/").data[0]
        self.assertEqual((row["seller"], row["reporter_name"], row["order_id"]), ("seller1", "buyer1", self.order.pk))
        r = self.ac.patch(f"/api/admin/problems/{report.pk}/", {"status": "resolved", "admin_note": "Seller refunded Rs. 3,000"}, format="json")
        self.assertEqual(r.data["status"], "resolved")
        self.assertEqual(self.bc.get("/api/problems/").data[0]["admin_note"], "Seller refunded Rs. 3,000")
        self.assertEqual(self.ac.get("/api/admin/problems/?status=open").data, [])
        self.ac.patch(f"/api/admin/problems/{report.pk}/", {"description": "rewritten"}, format="json")
        report.refresh_from_db()
        self.assertEqual(report.description, "Battery drains fast")  # reporter's text is not editable
