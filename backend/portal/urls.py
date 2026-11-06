from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("users", views.UserAdminViewSet, basename="admin-user")
router.register("references", views.ReferenceAdminViewSet, basename="admin-reference")
router.register("problems", views.ProblemAdminViewSet, basename="admin-problem")

urlpatterns = [
    path("stats/", views.StatsView.as_view()),
    path("phones/", views.PhoneReviewListView.as_view()),
    path("phones/<int:pk>/approve/", views.PhoneApproveView.as_view()),
    path("phones/<int:pk>/reject/", views.PhoneRejectView.as_view()),
    path("orders/", views.OrderAdminListView.as_view()),
    path("orders/<int:pk>/refunded/", views.OrderRefundedView.as_view()),
    path("", include(router.urls)),
]
