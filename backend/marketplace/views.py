from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView

from phones.models import Phone
from phones.similar import listed_candidates, vector_for
from valuation import knn

from .kmp import matches_all_terms
from .serializers import ListingDetailSerializer, ListingSerializer


def searchable_text(phone):
    ref = phone.reference
    return f"{ref.brand} {ref.model_name} {ref.storage_gb}GB {phone.condition}"


class MarketplaceListView(generics.ListAPIView):
    """Listed phones for any signed-in user (buyers, sellers, admins).

    ?q=iphone 13   keyword search (KMP)
    ?brand=Apple   brand filter
    ?max_price=70000
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ListingSerializer

    def get_queryset(self):
        params = self.request.query_params
        qs = Phone.objects.for_sale().select_related("reference").order_by("-created_at")

        brand = params.get("brand", "").strip()
        if brand:
            qs = qs.filter(reference__brand__iexact=brand)

        max_price = params.get("max_price", "").strip()
        if max_price:
            if not max_price.isdigit():
                raise ValidationError({"max_price": "Enter a whole number."})
            qs = qs.filter(asking_price__lte=int(max_price))

        query = params.get("q", "").strip()
        if query:
            return [p for p in qs if matches_all_terms(searchable_text(p), query)]
        return qs


class ListingDetailView(RetrieveAPIView):
    """One listed phone + KNN market check + the 3 most similar phones."""
    permission_classes = [IsAuthenticated]
    serializer_class = ListingDetailSerializer
    queryset = Phone.objects.for_sale().select_related("reference")

    def retrieve(self, request, *args, **kwargs):
        phone = self.get_object()
        data = self.get_serializer(phone).data

        others = listed_candidates(exclude_pk=phone.pk)
        neighbors = [p for _, p in knn.nearest(vector_for(phone), others, knn.K)]
        check = knn.market_check(vector_for(phone), others, price_of=lambda p: p.asking_price)

        data["market"] = {"price": check.price, "count": len(check.neighbors)} if check else None
        data["similar"] = ListingSerializer(neighbors, many=True, context={"request": request}).data
        return Response(data)
