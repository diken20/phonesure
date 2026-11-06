from rest_framework import serializers

from accounts.models import User
from orders.models import Order, ProblemReport
from phones.models import Phone, PhoneModelReference


class AdminPhoneSerializer(serializers.ModelSerializer):
    """Everything an admin needs to decide whether a phone may be shown to buyers."""
    seller = serializers.CharField(source="owner.username", read_only=True)
    reference_label = serializers.CharField(source="reference.__str__", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    fair_low = serializers.SerializerMethodField()
    fair_high = serializers.SerializerMethodField()
    price_verdict = serializers.CharField(read_only=True)
    trust_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = Phone
        fields = [
            "id", "seller", "reference_label", "purchase_year", "condition", "battery_health",
            "warranty_months", "repairs_done", "has_box", "has_charger", "has_bill", "asking_price",
            "photo", "status", "status_label", "review_note", "reviewed_at", "fair_low", "fair_high",
            "price_verdict", "trust_score", "created_at",
        ]

    def get_fair_low(self, obj):
        return obj.valuation.low

    def get_fair_high(self, obj):
        return obj.valuation.high

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["photo"] = instance.photo.url if instance.photo else None
        return data


class AdminUserSerializer(serializers.ModelSerializer):
    phone_count = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "is_active", "date_joined", "phone_count", "order_count"]
        read_only_fields = ["id", "username", "email", "role", "date_joined"]

    def get_phone_count(self, obj):
        return obj.phones.count()

    def get_order_count(self, obj):
        return obj.orders.count()

    def validate(self, attrs):
        if self.instance.pk == self.context["request"].user.pk:
            raise serializers.ValidationError("You cannot change your own account.")
        if self.instance.role == "admin" or self.instance.is_superuser:
            raise serializers.ValidationError("Admin accounts cannot be changed here.")
        return attrs


class AdminReferenceSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="__str__", read_only=True)
    phone_count = serializers.SerializerMethodField()
    base_price = serializers.IntegerField(min_value=1)

    class Meta:
        model = PhoneModelReference
        fields = ["id", "label", "brand", "model_name", "storage_gb", "base_price", "phone_count"]

    def get_phone_count(self, obj):
        return obj.phone_set.count()


class AdminOrderSerializer(serializers.ModelSerializer):
    buyer = serializers.CharField(source="buyer.username", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "buyer", "total", "status", "status_label", "esewa_code",
                  "transaction_uuid", "created_at", "paid_at", "items"]

    def get_items(self, obj):
        return [{"title": i.title, "price": i.price} for i in obj.items.all()]


class AdminProblemSerializer(serializers.ModelSerializer):
    item_title = serializers.CharField(source="item.title", read_only=True)
    order_id = serializers.IntegerField(source="item.order_id", read_only=True)
    reporter_name = serializers.CharField(source="reporter.username", read_only=True)
    seller = serializers.SerializerMethodField()
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ProblemReport
        fields = ["id", "item_title", "order_id", "reporter_name", "seller", "category",
                  "category_label", "description", "status", "status_label", "admin_note", "created_at"]
        read_only_fields = ["id", "category", "description", "created_at"]

    def get_seller(self, obj):
        phone = obj.item.phone
        return phone.owner.username if phone else None
