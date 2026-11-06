"""Connects the pure KNN code to the database: which phones are the candidates."""
from valuation import knn

from .models import Phone


def vector_for(phone):
    return knn.to_vector(phone.reference.base_price, phone.age_years, phone.condition, phone.battery_health)


def listed_candidates(exclude_pk=None):
    qs = Phone.objects.for_sale().select_related("reference", "owner")
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return [(vector_for(p), p) for p in qs]


def market_check_for_phone(phone):
    """KNN market check for a listed phone, comparing it only with the OTHER listed phones."""
    return knn.market_check(vector_for(phone), listed_candidates(exclude_pk=phone.pk),
                            price_of=lambda p: p.asking_price)
