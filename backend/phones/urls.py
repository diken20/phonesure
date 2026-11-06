from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("phones", views.PhoneViewSet, basename="phone")

urlpatterns = [
    path("references/", views.ReferenceListView.as_view()),
    path("", include(router.urls)),
]
