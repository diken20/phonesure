from django.urls import path

from . import views

urlpatterns = [
    path("cart/", views.CartView.as_view()),
    path("cart/items/<int:pk>/", views.CartItemView.as_view()),
    path("orders/checkout/", views.CheckoutView.as_view()),
    path("orders/esewa/verify/", views.EsewaVerifyView.as_view()),
    path("orders/", views.OrderListView.as_view()),
    path("orders/<int:pk>/", views.OrderDetailView.as_view()),
    path("problems/lookup/<uuid:public_id>/", views.ProblemLookupView.as_view()),
    path("problems/", views.ProblemListCreateView.as_view()),
]
