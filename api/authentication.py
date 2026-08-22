"""Cookie 版 JWT 认证与 Cookie 写入/清除工具。

安全模型（ADR-003 中期方案落地）：
- access / refresh token 均放入 HttpOnly + SameSite + Secure Cookie，前端 JS 无法读取，
  消除 localStorage 存 token 带来的 XSS 窃取风险。
- access Cookie path="/"，随所有 API 请求携带。
- refresh Cookie path="/api/v1/auth/"，仅认证相关端点（login/refresh/logout/csrf）会收到。
- 写请求（POST/PUT/PATCH/DELETE）由 api.middleware.CookieAuthCsrfMiddleware 强制 CSRF 校验。
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.tokens import AccessToken


class CookieJWTAuthentication(BaseAuthentication):
    """从 HttpOnly Cookie 读取 access token 的 JWT 认证类。"""

    keyword = 'Bearer'

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        if not raw_token:
            return None
        try:
            validated = AccessToken(raw_token)
        except Exception:
            raise exceptions.AuthenticationFailed('访问令牌无效或已过期')
        user = self.get_user(validated)
        return (user, validated)

    def get_user(self, validated_token):
        User = get_user_model()
        try:
            user_id = validated_token['user_id']
        except KeyError:
            raise exceptions.AuthenticationFailed('令牌缺少用户标识')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('用户不存在')
        if not user.is_active:
            raise exceptions.AuthenticationFailed('用户已被禁用')
        return user

    def authenticate_header(self, request):
        return self.keyword


def set_auth_cookies(response, access_token, refresh_token):
    """把 access / refresh token 写入 HttpOnly Cookie。"""
    access_max_age = int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds())
    refresh_max_age = int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds())

    response.set_cookie(
        key=settings.AUTH_COOKIE_ACCESS,
        value=str(access_token),
        max_age=access_max_age,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_COOKIE_PATH,
    )
    response.set_cookie(
        key=settings.AUTH_COOKIE_REFRESH,
        value=str(refresh_token),
        max_age=refresh_max_age,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
    )
    return response


def clear_auth_cookies(response):
    """清除 access / refresh Cookie（登出）。"""
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS, path=settings.AUTH_COOKIE_PATH)
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH, path=settings.AUTH_REFRESH_COOKIE_PATH)
    return response
