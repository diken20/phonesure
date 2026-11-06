import uuid

from django.conf import settings
from django.db import models

from phones.models import Phone


def new_transaction_uuid():
    # eSewa accepts letters, digits and hyphens only; must be unique per payment attempt.
    return "PS-" + uuid.uuid4().hex[:20]


class CartItem(models.Model):
    """A used phone is one-of-a-kind, so the cart has no quantity."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    phone = models.ForeignKey(Phone, on_delete=models.CASCADE, related_name="in_carts")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "phone")
        ordering = ["-added_at"]


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Waiting for payment"
        PAID = "paid", "Paid"
        REVIEW = "review", "Needs review (paid, phone no longer available)"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"
        COD_PENDING = "cod_pending", "Cash on delivery - awaiting delivery"

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    payment_method = models.CharField(max_length=12, choices=[("esewa", "eSewa"), ("cod", "Cash on delivery")], default="esewa")
    total = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_uuid = models.CharField(max_length=40, unique=True, default=new_transaction_uuid)
    esewa_code = models.CharField(max_length=40, blank=True, help_text="eSewa transaction_code")
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} ({self.get_status_display()})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    phone = models.ForeignKey(Phone, on_delete=models.SET_NULL, null=True, related_name="order_items")
    title = models.CharField(max_length=150)   # snapshot, in case the phone record changes
    price = models.PositiveIntegerField()      # snapshot of the asking price at checkout
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # goes into the QR code

    def __str__(self):
        return self.title


class ProblemReport(models.Model):
    class Category(models.TextChoices):
        NOT_AS_DESCRIBED = "not_as_described", "Not as described"
        SCAM = "scam", "Suspected scam or fake listing"
        BATTERY = "battery", "Battery problem"
        SCREEN_OR_BODY = "screen_or_body", "Screen or body damage"
        NOT_WORKING = "not_working", "Not working properly"
        MISSING_ITEMS = "missing_items", "Missing box, charger or bill"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"

    item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="problems", null=True, blank=True)
    phone = models.ForeignKey(Phone, on_delete=models.SET_NULL, related_name="scam_reports", null=True, blank=True)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="problem_reports")
    category = models.CharField(max_length=20, choices=Category.choices)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
