import base64
import json
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from phones.models import Phone, PhoneModelReference

from . import esewa
from .models import CartItem, Order, OrderItem, ProblemReport

SECRET = "8gBm/:&EnhH.1/q"


def client_for(user):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.get_or_create(user=user)[0].key}")
    return c


def eSewa_reply(order, **override):
    """Build the base64 `data` that eSewa sends back, correctly signed."""
    data = {"transaction_code": "000AWEO", "status": "COMPLETE", "total_amount": f"{order.total}.0",
            "transaction_uuid": order.transaction_uuid, "product_code": "EPAYTEST",
            "signed_field_names": "transaction_code,status,total_amount,transaction_uuid,product_code,signed_field_names"}
    data.update(override)
    names = data["signed_field_names"].split(",")
    data["signature"] = esewa.sign(esewa.signature_message(data, names), SECRET)
    return base64.b64encode(json.dumps(data).encode()).decode()


class EsewaHelperTests(SimpleTestCase):
    def test_sign_is_standard_hmac_sha256_base64(self):
        # Well-known HMAC-SHA256 test vector (key "key", the "quick brown fox" sentence).
        signature = esewa.sign("The quick brown fox jumps over the lazy dog", "key")
        self.assertEqual(base64.b64decode(signature).hex(),
                         "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8")

    def test_message_uses_the_field_order_given(self):
        fields = {"b": "2", "a": "1"}
        self.assertEqual(esewa.signature_message(fields, ["a", "b"]), "a=1,b=2")

    def test_decode_keeps_number_text_exactly(self):
        raw = base64.b64encode(b'{"total_amount": 1000.0, "n": 230}').decode()
        self.assertEqual(esewa.decode_reply(raw), {"total_amount": "1000.0", "n": "230"})

    def test_garbage_reply_rejected(self):
        with self.assertRaises(ValueError):
            esewa.decode_reply("not-base64-json!!")


class ShopTestCase(APITestCase):
    def setUp(self):
        self.ref = PhoneModelReference.objects.create(brand="Apple", model_name="iPhone 13", storage_gb=128, base_price=85000)
        self.seller = User.objects.create_user("seller1", password="pw12345678", role="seller")
        self.buyer = User.objects.create_user("buyer1", password="pw12345678", role="buyer")
        self.buyer2 = User.objects.create_user("buyer2", password="pw12345678", role="buyer")
        self.p1 = self.phone(62000)
        self.p2 = self.phone(40000)
        self.draft = self.phone(30000, status="draft")
        self.bc, self.bc2 = client_for(self.buyer), client_for(self.buyer2)

    def phone(self, price, status="listed"):
        return Phone.objects.create(owner=self.seller, reference=self.ref, purchase_year=2025, condition="good",
                                    battery_health=86, asking_price=price, status=status)

    def checkout(self, client, *phones):
        for p in phones:
            client.post("/api/cart/", {"phone": p.pk}, format="json")
        return client.post("/api/orders/checkout/")

    def pay(self, client, order, **override):
        return client.post("/api/orders/esewa/verify/", {"data": eSewa_reply(order, **override)}, format="json")


class CartTests(ShopTestCase):
    def test_roles(self):
        self.assertEqual(self.client.get("/api/cart/").status_code, 401)
        self.assertEqual(client_for(self.seller).get("/api/cart/").status_code, 403)

    def test_add_list_total_remove(self):
        self.bc.post("/api/cart/", {"phone": self.p1.pk}, format="json")
        r = self.bc.post("/api/cart/", {"phone": self.p2.pk}, format="json")
        self.assertEqual((r.status_code, r.data["count"], r.data["total"]), (201, 2, 102000))
        item_id = r.data["items"][0]["id"]
        self.assertEqual(self.bc.delete(f"/api/cart/items/{item_id}/").status_code, 204)
        self.assertEqual(self.bc.get("/api/cart/").data["count"], 1)

    def test_adding_twice_does_not_duplicate(self):
        self.bc.post("/api/cart/", {"phone": self.p1.pk}, format="json")
        self.bc.post("/api/cart/", {"phone": self.p1.pk}, format="json")
        self.assertEqual(CartItem.objects.filter(user=self.buyer).count(), 1)

    def test_draft_or_unknown_phone_rejected(self):
        self.assertEqual(self.bc.post("/api/cart/", {"phone": self.draft.pk}, format="json").status_code, 400)
        self.assertEqual(self.bc.post("/api/cart/", {"phone": 9999}, format="json").status_code, 400)

    def test_cannot_remove_someone_elses_item(self):
        r = self.bc.post("/api/cart/", {"phone": self.p1.pk}, format="json")
        self.bc2.delete(f"/api/cart/items/{r.data['items'][0]['id']}/")
        self.assertEqual(CartItem.objects.count(), 1)


class CheckoutTests(ShopTestCase):
    def test_empty_cart(self):
        self.assertEqual(self.bc.post("/api/orders/checkout/").status_code, 400)

    def test_creates_order_with_signed_form(self):
        r = self.checkout(self.bc, self.p1, self.p2)
        self.assertEqual(r.status_code, 201)
        order = Order.objects.get(pk=r.data["order_id"])
        self.assertEqual((order.total, order.status), (102000, "pending"))
        f = r.data["esewa"]["fields"]
        self.assertEqual((f["total_amount"], f["transaction_uuid"], f["product_code"]),
                         ("102000", order.transaction_uuid, "EPAYTEST"))
        expected = esewa.sign(f"total_amount=102000,transaction_uuid={order.transaction_uuid},product_code=EPAYTEST", SECRET)
        self.assertEqual(f["signature"], expected)
        self.assertEqual(f["success_url"], settings.FRONTEND_URL + "/payment/success")
        self.assertEqual(order.items.count(), 2)

    def test_new_checkout_cancels_old_pending_order(self):
        first = self.checkout(self.bc, self.p1).data["order_id"]
        self.bc.post("/api/orders/checkout/")
        self.assertEqual(Order.objects.get(pk=first).status, "cancelled")

    def test_phone_held_by_another_buyers_checkout(self):
        self.checkout(self.bc, self.p1)
        r = self.checkout(self.bc2, self.p1)
        self.assertEqual(r.status_code, 409)
        self.assertIn("someone else", r.data["problems"][0])

    def test_hold_expires_after_reservation_time(self):
        order_id = self.checkout(self.bc, self.p1).data["order_id"]
        Order.objects.filter(pk=order_id).update(created_at=timezone.now() - timedelta(minutes=settings.RESERVATION_MINUTES + 1))
        self.assertEqual(self.checkout(self.bc2, self.p1).status_code, 201)

    def test_phone_unlisted_after_adding(self):
        self.bc.post("/api/cart/", {"phone": self.p1.pk}, format="json")
        Phone.objects.filter(pk=self.p1.pk).update(status="draft")
        self.assertEqual(self.bc.post("/api/orders/checkout/").status_code, 409)


@override_settings(ESEWA_STATUS_CHECK=False)
class PaymentVerifyTests(ShopTestCase):
    def setUp(self):
        super().setUp()
        self.order = Order.objects.get(pk=self.checkout(self.bc, self.p1, self.p2).data["order_id"])

    def test_valid_payment_marks_paid_and_phones_sold(self):
        r = self.pay(self.bc, self.order)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["status"], "paid")
        self.assertEqual(r.data["esewa_code"], "000AWEO")
        self.assertEqual(Phone.objects.filter(status="sold").count(), 2)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertTrue(r.data["items"][0]["qr"].startswith("data:image/png;base64,"))

    def test_sold_phones_leave_marketplace(self):
        self.pay(self.bc, self.order)
        self.assertEqual(len(self.bc.get("/api/marketplace/").data), 0)

    def test_repeating_verification_is_safe(self):
        self.pay(self.bc, self.order)
        self.assertEqual(self.pay(self.bc, self.order).data["status"], "paid")
        self.assertEqual(Order.objects.filter(status="paid").count(), 1)

    def test_tampered_amount_rejected(self):
        r = self.pay(self.bc, self.order, total_amount="100.0")  # signed correctly, but wrong amount
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Order.objects.get(pk=self.order.pk).status, "pending")

    def test_bad_signature_rejected(self):
        data = json.loads(base64.b64decode(eSewa_reply(self.order)))
        data["signature"] = "AAAA"
        enc = base64.b64encode(json.dumps(data).encode()).decode()
        self.assertEqual(self.bc.post("/api/orders/esewa/verify/", {"data": enc}, format="json").status_code, 400)

    def test_forged_reply_reusing_the_request_signature_is_rejected(self):
        # The buyer can SEE the form signature (it signs only amount, id and code). They must not
        # be able to present it as a "COMPLETE" reply.
        form = esewa.build_payment_form(self.order)["fields"]
        forged = {"status": "COMPLETE", "total_amount": form["total_amount"],
                  "transaction_uuid": form["transaction_uuid"], "product_code": "EPAYTEST",
                  "signed_field_names": "total_amount,transaction_uuid,product_code",
                  "signature": form["signature"], "transaction_code": "FAKE"}
        enc = base64.b64encode(json.dumps(forged).encode()).decode()
        r = self.bc.post("/api/orders/esewa/verify/", {"data": enc}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Phone.objects.filter(status="sold").count(), 0)

    def test_status_not_complete_rejected(self):
        r = self.pay(self.bc, self.order, status="PENDING")
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Phone.objects.filter(status="sold").count(), 0)

    def test_other_buyer_cannot_confirm_my_order(self):
        self.assertEqual(self.pay(self.bc2, self.order).status_code, 404)

    def test_phone_sold_meanwhile_sends_order_to_review(self):
        Phone.objects.filter(pk=self.p1.pk).update(status="sold")
        self.assertEqual(self.pay(self.bc, self.order).data["status"], "review")
        self.assertEqual(Phone.objects.filter(status="sold").count(), 1)  # p2 is NOT marked sold

    @override_settings(ESEWA_STATUS_CHECK=True)
    def test_esewa_status_api_must_agree(self):
        with mock.patch("orders.esewa.fetch_status", return_value={"status": "PENDING"}):
            self.assertEqual(self.pay(self.bc, self.order).status_code, 400)
        with mock.patch("orders.esewa.fetch_status", return_value={"status": "COMPLETE"}):
            self.assertEqual(self.pay(self.bc, self.order).status_code, 200)

    @override_settings(ESEWA_STATUS_CHECK=True)
    def test_status_api_unreachable_or_erroring_falls_back_to_signature(self):
        for answer in (None, {"code": 0, "error_message": "Service is currently unavailable"}):
            Order.objects.filter(pk=self.order.pk).update(status="pending")
            with mock.patch("orders.esewa.fetch_status", return_value=answer):
                self.assertEqual(self.pay(self.bc, self.order).status_code, 200)
            Phone.objects.filter(pk__in=[self.p1.pk, self.p2.pk]).update(status="listed")


@override_settings(ESEWA_STATUS_CHECK=False)
class OrderAndProblemTests(ShopTestCase):
    def setUp(self):
        super().setUp()
        self.order = Order.objects.get(pk=self.checkout(self.bc, self.p1).data["order_id"])
        self.item = self.order.items.get()

    def paid(self):
        self.pay(self.bc, self.order)

    def report(self, client=None, **extra):
        body = {"item": str(self.item.public_id), "category": "battery", "description": "Battery drains in two hours."}
        body.update(extra)
        return (client or self.bc).post("/api/problems/", body, format="json")

    def test_orders_list_hides_cancelled_and_detail_has_qr_only_when_paid(self):
        self.assertIsNone(self.bc.get(f"/api/orders/{self.order.pk}/").data["items"][0]["qr"])
        self.paid()
        detail = self.bc.get(f"/api/orders/{self.order.pk}/").data
        self.assertTrue(detail["items"][0]["qr"])
        self.assertEqual(len(self.bc.get("/api/orders/").data), 1)
        self.assertEqual(len(self.bc2.get("/api/orders/").data), 0)
        self.assertEqual(self.bc2.get(f"/api/orders/{self.order.pk}/").status_code, 404)

    def test_qr_encodes_the_report_url(self):
        from .qr import problem_report_url
        self.assertEqual(problem_report_url(self.item), f"{settings.FRONTEND_URL}/report-problem/{self.item.public_id}")

    def test_cannot_report_before_paying(self):
        self.assertEqual(self.report().status_code, 400)
        self.assertEqual(self.bc.get(f"/api/problems/lookup/{self.item.public_id}/").status_code, 404)

    def test_buyer_reports_after_paying(self):
        self.paid()
        look = self.bc.get(f"/api/problems/lookup/{self.item.public_id}/")
        self.assertEqual(look.data["title"], "Apple iPhone 13 128GB")
        r = self.report()
        self.assertEqual((r.status_code, r.data["status"]), (201, "open"))
        self.assertEqual(ProblemReport.objects.get().reporter, self.buyer)
        self.assertEqual(len(self.bc.get("/api/problems/").data), 1)

    def test_other_buyer_cannot_scan_my_qr(self):
        self.paid()
        self.assertEqual(self.bc2.get(f"/api/problems/lookup/{self.item.public_id}/").status_code, 404)
        self.assertEqual(self.report(self.bc2).status_code, 400)

    def test_short_description_rejected(self):
        self.paid()
        self.assertEqual(self.report(description="bad").status_code, 400)

    def test_seller_sees_reports_about_sold_phone_but_cannot_file(self):
        self.paid(); self.report()
        sc = client_for(self.seller)
        self.assertEqual(len(sc.get("/api/problems/").data), 1)
        self.assertEqual(sc.post("/api/problems/", {"item": str(self.item.public_id), "category": "other",
                                                    "description": "I am the seller here"}, format="json").status_code, 403)
        other = client_for(User.objects.create_user("seller2", password="pw12345678", role="seller"))
        self.assertEqual(len(other.get("/api/problems/").data), 0)

    def test_sold_phone_cannot_be_edited_or_deleted_by_seller(self):
        self.paid()
        sc = client_for(self.seller)
        url = f"/api/phones/{self.p1.pk}/"
        self.assertEqual(sc.patch(url, {"asking_price": 1}, format="json").status_code, 400)
        self.assertEqual(sc.delete(url).status_code, 400)
        self.assertTrue(Phone.objects.filter(pk=self.p1.pk).exists())

    def test_seller_cannot_set_status_to_sold(self):
        r = client_for(self.seller).patch(f"/api/phones/{self.p2.pk}/", {"status": "sold"}, format="json")
        self.assertEqual(r.status_code, 400)
