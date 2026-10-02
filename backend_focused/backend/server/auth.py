from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

REFRESH_COOKIE = "fleet_refresh"
REFRESH_COOKIE_PATH = "/api/auth/"


def _cookie_kwargs():
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    return {
        "httponly": True,
        "secure": not settings.DEBUG,
        "samesite": "Lax",
        "path": REFRESH_COOKIE_PATH,
        "max_age": int(lifetime.total_seconds()),
    }


def _set_refresh_cookie(response, refresh):
    response.set_cookie(REFRESH_COOKIE, refresh, **_cookie_kwargs())


def _clear_refresh_cookie(response):
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH, samesite="Lax")


class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get("refresh")
        if refresh:
            _set_refresh_cookie(response, refresh)
            del response.data["refresh"]
        return response


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get(REFRESH_COOKIE, "")
        serializer = self.get_serializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError):
            response = Response(
                {"detail": "Refresh token invalid."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
            _clear_refresh_cookie(response)
            return response
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        rotated = response.data.get("refresh")
        if rotated:
            _set_refresh_cookie(response, rotated)
            del response.data["refresh"]
        return response


class CookieLogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh = request.COOKIES.get(REFRESH_COOKIE)
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _clear_refresh_cookie(response)
        return response
