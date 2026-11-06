from rest_framework import serializers

from valuation.serializers import valuation_payload

from .models import Phone, PhoneModelReference


class ReferenceSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = PhoneModelReference
        fields = ["id", "label", "brand", "model_name", "storage_gb"]


class PhoneSerializer(serializers.ModelSerializer):
    # Sellers may enter a brand/model directly; a reference row is created automatically.
    reference = serializers.PrimaryKeyRelatedField(
        queryset=PhoneModelReference.objects.all(), required=False, allow_null=True
    )
    brand = serializers.CharField(write_only=True, required=False, max_length=50)
    model_name = serializers.CharField(write_only=True, required=False, max_length=80)
    storage_gb = serializers.IntegerField(write_only=True, required=False, min_value=1, max_value=2048)
    base_price = serializers.IntegerField(write_only=True, required=False, min_value=1)
    reference_label = serializers.CharField(source="reference.__str__", read_only=True)
    valuation = serializers.SerializerMethodField()
    price_verdict = serializers.CharField(read_only=True)
    trust_score = serializers.IntegerField(read_only=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    # A seller can only save a draft or submit for review. An ADMIN approves ("listed") and a verified
    # payment sets "sold", so a seller can never publish a phone to buyers by themselves.
    status = serializers.ChoiceField(choices=[("draft", "Draft"), ("pending", "Submit for review")], required=False)

    class Meta:
        model = Phone
        fields = [
            "id", "reference", "brand", "model_name", "storage_gb", "base_price", "reference_label", "purchase_year", "condition",
            "battery_health", "warranty_months", "repairs_done", "has_box",
            "has_charger", "has_bill", "asking_price", "photo", "status",
            "public_id", "valuation", "price_verdict", "trust_score", "review_note", "created_at",
        ]
        read_only_fields = ["id", "public_id", "review_note", "created_at"]

    def _attach_reference(self, validated_data):
        brand = validated_data.pop("brand", "").strip()
        model_name = validated_data.pop("model_name", "").strip()
        storage_gb = validated_data.pop("storage_gb", None)
        base_price = validated_data.pop("base_price", None)
        if brand and model_name and storage_gb:
            if not base_price and getattr(self, "instance", None):
                base_price = self.instance.reference.base_price
            if not base_price:
                raise serializers.ValidationError({"base_price": "Enter the estimated price when this phone was new."})
            ref, _ = PhoneModelReference.objects.get_or_create(brand=brand, model_name=model_name, storage_gb=storage_gb, defaults={"base_price": base_price})
            validated_data["reference"] = ref
        elif not validated_data.get("reference"):
            raise serializers.ValidationError({"brand": "Enter brand, model, storage and estimated new price."})
        return validated_data

    def create(self, validated_data):
        return super().create(self._attach_reference(validated_data))

    def update(self, instance, validated_data):
        validated_data = self._attach_reference(validated_data) if any(k in validated_data for k in ("brand", "model_name", "storage_gb", "base_price")) else validated_data
        new_status = validated_data.get("status")
        if instance.status == Phone.Status.LISTED and new_status != Phone.Status.DRAFT:
            # Changing a live listing sends it back for approval, so a phone cannot be swapped
            # for something different after the admin approved it.
            validated_data["status"] = new_status = Phone.Status.PENDING
        if new_status == Phone.Status.PENDING:
            validated_data["review_note"] = ""  # resubmitted: the old rejection reason is obsolete
        return super().update(instance, validated_data)

    def validate(self, attrs):
        if self.instance and self.instance.status == Phone.Status.SOLD:
            raise serializers.ValidationError("This phone is sold and can no longer be changed.")
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Relative URL (/media/...) so it works behind the React dev proxy and in production.
        data["photo"] = instance.photo.url if instance.photo else None
        return data

    def get_valuation(self, obj):
        return valuation_payload(obj.valuation)
