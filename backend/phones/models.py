import uuid
from datetime import date

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from valuation import engine

from .trust import trust_score as compute_trust

CONDITION_CHOICES = [
    ("excellent", "Excellent"),
    ("good", "Good"),
    ("fair", "Fair"),
    ("poor", "Poor"),
]


class PhoneModelReference(models.Model):
    """Admin-managed base price for a phone model + storage (see proposal)."""

    brand = models.CharField(max_length=50)
    model_name = models.CharField(max_length=80)
    storage_gb = models.PositiveSmallIntegerField()
    base_price = models.PositiveIntegerField(help_text="Price in NPR when bought new / almost new")

    class Meta:
        ordering = ["brand", "model_name", "storage_gb"]
        unique_together = ("brand", "model_name", "storage_gb")
        verbose_name = "phone model reference price"

    def __str__(self):
        return f"{self.brand} {self.model_name} {self.storage_gb}GB"


class PhoneQuerySet(models.QuerySet):
    def for_sale(self):
        """Phones a buyer may see and buy: approved by an admin, and the seller is still active."""
        return self.filter(status=Phone.Status.LISTED, owner__is_active=True)


class Phone(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending review"
        LISTED = "listed", "Listed"
        REJECTED = "rejected", "Rejected"
        SOLD = "sold", "Sold"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="phones")
    reference = models.ForeignKey(PhoneModelReference, on_delete=models.PROTECT, verbose_name="Phone model")
    purchase_year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2015), MaxValueValidator(date.today().year)]
    )
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    battery_health = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)], verbose_name="Battery health (%)"
    )
    warranty_months = models.PositiveSmallIntegerField(default=0, verbose_name="Warranty left (months)")
    repairs_done = models.BooleanField(default=False)
    has_box = models.BooleanField(default=False, verbose_name="Box")
    has_charger = models.BooleanField(default=False, verbose_name="Charger")
    has_bill = models.BooleanField(default=False, verbose_name="Original bill")
    asking_price = models.PositiveIntegerField(verbose_name="Asking price (Rs.)")
    photo = models.ImageField(upload_to="phones/", blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    review_note = models.TextField(blank=True, help_text="Why an admin rejected the phone")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # for the public report URL
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PhoneQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.reference)

    @property
    def age_years(self):
        # Year-based approximation: bought this year counts as "under 1 year".
        return max(0, date.today().year - self.purchase_year)

    @property
    def valuation(self):
        return engine.estimate(
            base_price=self.reference.base_price,
            age_years=self.age_years,
            condition=self.condition,
            battery_health=self.battery_health,
            has_box=self.has_box,
            has_charger=self.has_charger,
            has_bill=self.has_bill,
        )

    @property
    def price_verdict(self):
        return self.valuation.verdict(self.asking_price)

    def _trust(self):
        return compute_trust(
            has_bill=self.has_bill, warranty_months=self.warranty_months,
            battery_health=self.battery_health, repairs_done=self.repairs_done,
            has_box=self.has_box, has_charger=self.has_charger, has_photo=bool(self.photo),
        )

    @property
    def trust_score(self):
        return self._trust()[0]

    @property
    def trust_details(self):
        return self._trust()[1]
