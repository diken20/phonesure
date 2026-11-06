from rest_framework import serializers

from phones.models import Phone
from valuation.engine import age_factor
from orders.qr import qr_data_uri
from django.conf import settings


class ListingSerializer(serializers.ModelSerializer):
    """What a buyer may see. Deliberately has no owner or contact fields (privacy requirement)."""
    title = serializers.SerializerMethodField()
    brand = serializers.CharField(source="reference.brand")
    age_label = serializers.SerializerMethodField()
    fair_low = serializers.SerializerMethodField()
    fair_high = serializers.SerializerMethodField()
    trust_score = serializers.IntegerField(read_only=True)
    price_verdict = serializers.CharField(read_only=True)
    scam_report_qr = serializers.SerializerMethodField()

    class Meta:
        model = Phone
        fields = [
            "id", "public_id", "title", "brand", "condition", "battery_health", "age_label",
            "asking_price", "photo", "trust_score", "price_verdict", "fair_low", "fair_high", "scam_report_qr",
        ]

    def get_title(self, obj):
        return f"{obj.reference.model_name}, {obj.reference.storage_gb} GB"

    def get_age_label(self, obj):
        return age_factor(obj.age_years)[1]

    def get_fair_low(self, obj):
        return obj.valuation.low

    def get_fair_high(self, obj):
        return obj.valuation.high

    def get_scam_report_qr(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        report_url = f"{settings.FRONTEND_URL}/report-listing/{obj.pk}"
        return qr_data_uri(report_url)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["photo"] = self.context["request"].build_absolute_uri(instance.photo.url) if instance.photo and self.context.get("request") else (instance.photo.url if instance.photo else None)
        return data


class ListingDetailSerializer(ListingSerializer):
    """Full condition details for one listed phone (still no seller identity)."""
    trust_details = serializers.ListField(read_only=True)
    steps = serializers.SerializerMethodField()

    class Meta(ListingSerializer.Meta):
        fields = ListingSerializer.Meta.fields + [
            "purchase_year", "warranty_months", "repairs_done", "has_box", "has_charger",
            "has_bill", "trust_details", "steps",
        ]

    def get_steps(self, obj):
        return [{"label": s.label, "amount": s.amount} for s in obj.valuation.steps]
