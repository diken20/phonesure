from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("phones.urls")),
    path("api/marketplace/", include("marketplace.urls")),
    path("api/admin/", include("portal.urls")),
    path("api/", include("orders.urls")),
    path("api/valuation/", include("valuation.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
