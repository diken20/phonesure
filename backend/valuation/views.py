from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from phones.similar import listed_candidates

from . import engine, knn
from .serializers import ValuationInputSerializer, valuation_payload


class ValuationView(APIView):
    """Public price calculator for sellers and buyers."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ValuationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        result = engine.estimate(
            base_price=d["reference"].base_price,
            age_years=d["age_years"],
            condition=d["condition"],
            battery_health=d["battery_health"],
            has_box=d["has_box"],
            has_charger=d["has_charger"],
            has_bill=d["has_bill"],
        )
        payload = valuation_payload(result)
        asking = d.get("asking_price")
        payload["verdict"] = result.verdict(asking) if asking else None

        # KNN market check: what are the most similar LISTED phones asking?
        target = knn.to_vector(d["reference"].base_price, d["age_years"], d["condition"], d["battery_health"])
        check = knn.market_check(target, listed_candidates(), price_of=lambda p: p.asking_price)
        payload["market"] = {"price": check.price, "count": len(check.neighbors)} if check else None
        return Response(payload)
