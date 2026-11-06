from django.db import transaction
from django.db.models import ProtectedError, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsAdminRole
from orders.models import Order, ProblemReport
from phones.models import Phone, PhoneModelReference

from .serializers import (AdminOrderSerializer, AdminPhoneSerializer, AdminProblemSerializer,
                          AdminReferenceSerializer, AdminUserSerializer)


class StatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        def count(model, field, choices):
            return {value: model.objects.filter(**{field: value}).count() for value, _ in choices}

        revenue = Order.objects.filter(status=Order.Status.PAID).aggregate(total=Sum("total"))["total"] or 0
        return Response({
            "users": count(User, "role", User.Role.choices),
            "phones": count(Phone, "status", Phone.Status.choices),
            "orders": count(Order, "status", Order.Status.choices),
            "revenue": revenue,
            "open_problems": ProblemReport.objects.filter(status=ProblemReport.Status.OPEN).count(),
        })


# ------------------------------------------------------- phone review
class PhoneReviewListView(generics.ListAPIView):
    """?status=pending (default) | listed | rejected | draft | sold | all"""
    permission_classes = [IsAdminRole]
    serializer_class = AdminPhoneSerializer

    def get_queryset(self):
        qs = Phone.objects.select_related("reference", "owner").order_by("created_at")
        wanted = self.request.query_params.get("status", "pending")
        return qs if wanted == "all" else qs.filter(status=wanted)


class PhoneApproveView(APIView):
    permission_classes = [IsAdminRole]

    @transaction.atomic
    def post(self, request, pk):
        phone = get_object_or_404(Phone.objects.select_for_update(), pk=pk)
        if phone.status != Phone.Status.PENDING:
            raise ValidationError({"detail": "Only phones that are waiting for review can be approved."})
        phone.status = Phone.Status.LISTED
        phone.review_note = ""
        phone.reviewed_at = timezone.now()
        phone.save()
        return Response(AdminPhoneSerializer(phone).data)


class PhoneRejectView(APIView):
    """Reject a pending phone, or take a live one down. A reason is required: the seller sees it."""
    permission_classes = [IsAdminRole]

    @transaction.atomic
    def post(self, request, pk):
        phone = get_object_or_404(Phone.objects.select_for_update(), pk=pk)
        note = str(request.data.get("note", "")).strip()
        if len(note) < 5:
            raise ValidationError({"note": ["Please give the seller a reason (at least 5 characters)."]})
        if phone.status not in (Phone.Status.PENDING, Phone.Status.LISTED):
            raise ValidationError({"detail": "Only pending or listed phones can be rejected."})
        phone.status = Phone.Status.REJECTED
        phone.review_note = note
        phone.reviewed_at = timezone.now()
        phone.save()
        return Response(AdminPhoneSerializer(phone).data)


# ------------------------------------------------------------- users
class UserAdminViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """List users and activate or deactivate them (PATCH is_active)."""
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        qs = User.objects.order_by("-date_joined")
        role = self.request.query_params.get("role")
        return qs.filter(role=role) if role else qs


# ------------------------------------------------- reference prices
class ReferenceAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = AdminReferenceSerializer
    queryset = PhoneModelReference.objects.all()

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError({"detail": "This model is used by phones, so it cannot be deleted. Change its price instead."})


# -------------------------------------------------------- orders
class OrderAdminListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminOrderSerializer

    def get_queryset(self):
        qs = Order.objects.select_related("buyer").prefetch_related("items")
        status = self.request.query_params.get("status")
        return qs.filter(status=status) if status else qs.exclude(status=Order.Status.CANCELLED)


class OrderRefundedView(APIView):
    """After refunding a 'Needs review' order in the eSewa merchant portal, close it here."""
    permission_classes = [IsAdminRole]

    @transaction.atomic
    def post(self, request, pk):
        order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
        if order.status != Order.Status.REVIEW:
            raise ValidationError({"detail": "Only orders that need review can be marked as refunded."})
        order.status = Order.Status.REFUNDED
        order.save()
        return Response(AdminOrderSerializer(order).data)


# ------------------------------------------------------ problems
class ProblemAdminViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdminRole]
    serializer_class = AdminProblemSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        qs = ProblemReport.objects.select_related("item__order", "item__phone__owner", "reporter")
        status = self.request.query_params.get("status")
        return qs.filter(status=status) if status else qs
