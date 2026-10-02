from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from server.auth import CookieLogoutView, CookieTokenObtainPairView, CookieTokenRefreshView
from server.health import healthz

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/token/", CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/logout/", CookieLogoutView.as_view(), name="token_logout"),
    path("api/", include("fleet.urls")),
]
