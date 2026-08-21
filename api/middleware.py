"""对 /api/ 写请求强制 CSRF 校验（轻量版）。

DRF 默认对其视图做 csrf_exempt。改用 HttpOnly Cookie 认证后必须恢复 CSRF 防护，
否则攻击者可通过跨站表单/请求携带受害者的 Cookie 执行写操作。

本实现只读取 X-CSRFToken 请求头 + csrftoken Cookie 做比对，并做 Origin 校验，
**绝不访问 request.POST**——避免对 multipart 文件上传触发提前的全量 body 解析
（这正是大文件上传「延迟很大才反应」的根因）。API 走 JSON/头，本就不需要表单字段。
"""
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.middleware.csrf import (
    CsrfViewMiddleware,
    InvalidTokenFormat,
    _check_token_format,
    _does_token_match,
)

UNSAFE_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')


class CookieAuthCsrfMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._csrf = CsrfViewMiddleware(get_response)

    def __call__(self, request):
        if self._requires_csrf(request):
            reason = self._check(request)
            if reason is not None:
                raise PermissionDenied(reason)
        return self.get_response(request)

    def _requires_csrf(self, request):
        path = getattr(request, 'path_info', '') or getattr(request, 'path', '')
        return request.method in UNSAFE_METHODS and path.startswith('/api/')

    def _check(self, request):
        # 测试客户端可用 _dont_enforce_csrf_checks 关闭校验（与 Django 行为一致）
        if getattr(request, '_dont_enforce_csrf_checks', False):
            return None

        # 从 cookie 读取 CSRF secret 并写入 request.META["CSRF_COOKIE"]
        self._csrf.process_request(request)

        # Origin 校验（保留跨站防护；不访问 request.POST）
        if 'HTTP_ORIGIN' in request.META and not self._csrf._origin_verified(request):
            return 'Origin checking failed.'

        csrf_secret = request.META.get('CSRF_COOKIE')
        if csrf_secret is None:
            return 'CSRF cookie not set.'

        token = request.META.get(settings.CSRF_HEADER_NAME)
        if not token:
            return 'CSRF token missing.'

        try:
            _check_token_format(token)
        except InvalidTokenFormat as exc:
            return f'CSRF token {exc.reason}.'

        if not _does_token_match(token, csrf_secret):
            return 'CSRF token incorrect.'

        return None
