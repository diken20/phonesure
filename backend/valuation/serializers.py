from rest_framework import serializers

from phones.models import CONDITION_CHOICES, PhoneModelReference


class ValuationInputSerializer(serializers.Serializer):
    reference = serializers.PrimaryKeyRelatedField(queryset=PhoneModelReference.objects.all())
    age_years = serializers.FloatField(min_value=0, max_value=50)
    condition = serializers.ChoiceField(choices=CONDITION_CHOICES)
    battery_health = serializers.IntegerField(min_value=1, max_value=100)
    has_box = serializers.BooleanField(required=False, default=False)
    has_charger = serializers.BooleanField(required=False, default=False)
    has_bill = serializers.BooleanField(required=False, default=False)
    asking_price = serializers.IntegerField(required=False, allow_null=True, min_value=1)


def valuation_payload(v):
    """Turn an engine.Valuation into plain JSON."""
    return {
        "base_price": v.base_price,
        "steps": [{"label": s.label, "amount": s.amount} for s in v.steps],
        "estimate": v.estimate,
        "low": v.low,
        "high": v.high,
    }
