from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsBuyer
from phones.models import Phone

from . import esewa
from .models import CartItem, Order, OrderItem, ProblemReport
from .serializers import CartItemSerializer, OrderSerializer, ProblemReportSerializer


# ----------------------------------------------------------------- cart
def cart_payload(user, request):
    items = CartItem.objects.filter(user=user).select_related("phone__reference")
    data = CartItemSerializer(items, many=True, context={"request": request}).data
    total = sum(i["phone"]["asking_price"] for i in data if i["available"])
    return {"items": data, "count": len(data), "total": total}


class CartView(APIView):
    permission_classes = [IsBuyer]

    def get(self, request):
        return Response(cart_payload(request.user, request))

    def post(self, request):
        phone_id = request.data.get("phone")
        phone = Phone.objects.for_sale().filter(pk=phone_id).first() if str(phone_id).isdigit() else None
        if phone is None:
            raise ValidationError({"phone": ["This phone is not available."]})
        CartItem.objects.get_or_create(user=request.user, phone=phone)
        return Response(cart_payload(request.user, request), status=status.HTTP_201_CREATED)


class CartItemView(APIView):
    permission_classes = [IsBuyer]

    def delete(self, request, pk):
        CartItem.objects.filter(user=request.user, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------- checkout
class CheckoutView(APIView):
    """Turn the cart into a pending order and return the signed eSewa form."""
    permission_classes = [IsBuyer]

    @transaction.atomic
    def post(self, request):
        user = request.user
        # An earlier unpaid attempt by the same buyer is replaced by this one.
        Order.objects.filter(buyer=user, status=Order.Status.PENDING).update(status=Order.Status.CANCELLED)

        # Buy Now can pass phone_id; normal cart checkout uses all cart items.
        buy_now_id = request.data.get("phone_id")
        if buy_now_id is not None:
            phone = Phone.objects.for_sale().select_related("reference", "owner").filter(pk=buy_now_id).first() if str(buy_now_id).isdigit() else None
            if phone is None:
                raise ValidationError({"detail": "This phone is not available."})
            cart = [type("CheckoutItem", (), {"phone": phone, "phone_id": phone.pk})()]
            from_cart = False
        else:
            cart = list(CartItem.objects.filter(user=user).select_related("phone__reference"))
            from_cart = True
        if not cart:
            raise ValidationError({"detail": "Your cart is empty."})

        cutoff = timezone.now() - timedelta(minutes=settings.RESERVATION_MINUTES)
        problems = []
        for ci in cart:
            phone = ci.phone
            if phone.status != Phone.Status.LISTED or not phone.owner.is_active:
                problems.append(f"{phone.reference} is no longer available.")
            elif (OrderItem.objects.filter(phone=phone, order__status=Order.Status.PENDING,
                                           order__created_at__gte=cutoff)
                  .exclude(order__buyer=user).exists()):
                problems.append(f"{phone.reference} is being bought by someone else right now.")
        if problems:
            return Response({"detail": "Some phones in your cart cannot be bought.", "problems": problems},
                            status=status.HTTP_409_CONFLICT)

        payment_method = request.data.get("payment_method", "esewa")
        if payment_method not in ("esewa", "cod"):
            raise ValidationError({"payment_method": "Choose eSewa or cash on delivery."})
        order = Order.objects.create(buyer=user, total=sum(ci.phone.asking_price for ci in cart), payment_method=payment_method)
        OrderItem.objects.bulk_create([
            OrderItem(order=order, phone=ci.phone, title=str(ci.phone.reference), price=ci.phone.asking_price)
            for ci in cart
        ])
        if payment_method == "cod":
            phone_ids = [ci.phone_id for ci in cart]
            Phone.objects.filter(pk__in=phone_ids).update(status=Phone.Status.SOLD)
            if from_cart:
                CartItem.objects.filter(user=user).delete()
            order.status = Order.Status.COD_PENDING
            order.save(update_fields=["status"])
            return Response(OrderSerializer(order, context={"with_qr": True}).data, status=status.HTTP_201_CREATED)
        return Response({"order_id": order.id, "esewa": esewa.build_payment_form(order)}, status=status.HTTP_201_CREATED)


class EsewaVerifyView(APIView):
    """The React 'payment success' page sends eSewa's ?data=... here."""
    permission_classes = [IsBuyer]

    def post(self, request):
        try:
            data = esewa.decode_reply(str(request.data.get("data", "")))
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)})

        if not esewa.verify_signature(data):
            raise ValidationError({"detail": "The payment signature is invalid."})

        with transaction.atomic():
            order = (Order.objects.select_for_update()
                     .filter(transaction_uuid=data.get("transaction_uuid"), buyer=request.user).first())
            if order is None:
                return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

            if order.status in (Order.Status.PAID, Order.Status.REVIEW):  # already handled: safe to repeat
                return Response(OrderSerializer(order, context={"with_qr": True}).data)

            if data.get("status") != "COMPLETE":
                raise ValidationError({"detail": "The payment was not completed."})
            if data.get("product_code") != settings.ESEWA_PRODUCT_CODE or not esewa.amount_matches(data, order):
                raise ValidationError({"detail": "The payment details do not match the order."})
            if settings.ESEWA_STATUS_CHECK:
                info = esewa.fetch_status(order)
                remote_status = info.get("status") if isinstance(info, dict) else None
                # No answer, or an error like "Service is currently unavailable" (no status field):
                # rely on the verified signature. A clear non-COMPLETE status blocks the payment.
                if remote_status is not None and remote_status != "COMPLETE":
                    raise ValidationError({"detail": "eSewa does not confirm this payment."})

            items = list(order.items.select_related("phone"))
            phone_ids = [i.phone_id for i in items if i.phone_id]
            phones = list(Phone.objects.select_for_update().filter(pk__in=phone_ids))
            all_available = len(phones) == len(items) and all(p.status == Phone.Status.LISTED for p in phones)

            order.esewa_code = str(data.get("transaction_code", ""))[:40]
            order.paid_at = timezone.now()
            if all_available:
                Phone.objects.filter(pk__in=phone_ids).update(status=Phone.Status.SOLD)
                CartItem.objects.filter(phone_id__in=phone_ids).delete()
                order.status = Order.Status.PAID
            else:
                # Money was taken but a phone was sold meanwhile. Staff must refund via eSewa.
                order.status = Order.Status.REVIEW
            order.save()
        return Response(OrderSerializer(order, context={"with_qr": True}).data)


# --------------------------------------------------------------- orders
class OrderListView(generics.ListAPIView):
    permission_classes = [IsBuyer]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (Order.objects.filter(buyer=self.request.user).exclude(status=Order.Status.CANCELLED)
                .prefetch_related("items"))


class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [IsBuyer]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).prefetch_related("items")

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "with_qr": True}


# ------------------------------------------------------------- problems
class ProblemLookupView(APIView):
    """What the QR code opens: tells the page which purchased phone this is."""
    permission_classes = [IsBuyer]

    def get(self, request, public_id):
        item = get_object_or_404(OrderItem, public_id=public_id, order__buyer=request.user,
                                 order__status=Order.Status.PAID)
        return Response({"public_id": item.public_id, "title": item.title, "price": item.price,
                         "order_id": item.order_id, "problem_count": item.problems.count()})


class ProblemListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProblemReportSerializer

    def get_queryset(self):
        user = self.request.user
        qs = ProblemReport.objects.select_related("item")
        if user.role == "buyer":
            return qs.filter(reporter=user)
        if user.role == "admin":
            return qs
        return qs.filter(item__phone__owner=user) | qs.filter(phone__owner=user)  # reports about seller listings

    def create(self, request, *args, **kwargs):
        if request.user.role != "buyer":
            raise PermissionDenied("Only buyers can report a problem.")
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        if serializer.validated_data.get("phone") and not serializer.validated_data.get("category") == ProblemReport.Category.SCAM:
            raise ValidationError({"category": "Marketplace reports must be marked as suspected scam."})
        if not serializer.validated_data.get("phone") and not serializer.validated_data.get("item"):
            raise ValidationError({"item": "Choose a purchased phone or a marketplace listing."})
        serializer.save(reporter=self.request.user)
