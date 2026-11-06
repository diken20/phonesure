from rest_framework import generics, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny

from accounts.permissions import IsSeller

from .models import Phone, PhoneModelReference
from .serializers import PhoneSerializer, ReferenceSerializer


class ReferenceListView(generics.ListAPIView):
    """Public list of phone models for the dropdowns."""
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = PhoneModelReference.objects.all()
    serializer_class = ReferenceSerializer


class PhoneViewSet(viewsets.ModelViewSet):
    """Seller CRUD. A seller can only ever see and change their own phones."""
    serializer_class = PhoneSerializer
    permission_classes = [IsSeller]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Phone.objects.filter(owner=self.request.user).select_related("reference")

    def perform_destroy(self, instance):
        if instance.status == Phone.Status.SOLD:
            raise ValidationError("A sold phone cannot be deleted. It is part of a buyer's order.")
        instance.delete()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
