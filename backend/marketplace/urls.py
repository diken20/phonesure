from django.urls import path

from . import views

urlpatterns = [
    path("", views.MarketplaceListView.as_view()),
    path("<int:pk>/", views.ListingDetailView.as_view()),
]
