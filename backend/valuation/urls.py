from django.urls import path

from . import views

urlpatterns = [path("", views.ValuationView.as_view())]
