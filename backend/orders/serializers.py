from rest_framework import serializers

from marketplace.serializers import ListingSerializer

from .models import CartItem, Order, OrderItem, ProblemReport
from .qr import problem_report_url, qr_data_uri


class CartItemSerializer(serializers.ModelSerializer):
    phone = ListingSerializer(read_only=True)
    available = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "phone", "available"]

    def get_available(self, obj):
        return obj.phone.status == "listed" and obj.phone.owner.is_active


class OrderItemSerializer(serializers.ModelSerializer):
    qr = serializers.SerializerMethodField()
    problem_count = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["public_id", "title", "price", "qr", "problem_count"]

    def get_qr(self, obj):
        # The QR code opens the "Report a problem" page for this exact purchased phone.
        if self.context.get("with_qr") and obj.order.status == Order.Status.PAID:
            return qr_data_uri(problem_report_url(obj))
        return None

    def get_problem_count(self, obj):
        return obj.problems.count()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "status", "status_label", "payment_method", "total", "transaction_uuid", "esewa_code",
                  "created_at", "paid_at", "items"]


class ProblemReportSerializer(serializers.ModelSerializer):
    item = serializers.SlugRelatedField(slug_field="public_id", queryset=OrderItem.objects.none(), required=False, allow_null=True)
    phone = serializers.PrimaryKeyRelatedField(queryset=__import__("phones.models", fromlist=["Phone"]).Phone.objects.all(), required=False, allow_null=True)
    item_title = serializers.SerializerMethodField()
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    description = serializers.CharField(min_length=10, max_length=2000)

    def get_item_title(self, obj):
        if obj.item_id:
            return obj.item.title
        if obj.phone_id:
            return str(obj.phone.reference)
        return "Marketplace listing"

    class Meta:
        model = ProblemReport
        fields = ["id", "item", "phone", "item_title", "category", "category_label", "description",
                  "status", "status_label", "admin_note", "created_at"]
        read_only_fields = ["id", "status", "admin_note", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            # A buyer can only report phones from THEIR OWN paid orders.
            self.fields["item"].queryset = OrderItem.objects.filter(
                order__buyer=request.user, order__status__in=[Order.Status.PAID, Order.Status.COD_PENDING])
            self.fields["phone"].queryset = __import__("phones.models", fromlist=["Phone"]).Phone.objects.filter(status="listed").exclude(owner=request.user)
