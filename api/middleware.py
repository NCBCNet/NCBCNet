"""对 /api/ 写请求强制 CSRF 校验。

DRF 默认对其视图做 csrf_exempt。改用 HttpOnly Cookie 认证后必须恢复 CSRF 防护，
否则攻击者可通过跨站表单/请求携带受害者的 Cookie 执行写操作。

本中间件复用 Django 内建 CsrfViewMiddleware 的完整校验（Origin/Referer + token），
仅作用于 /api/ 前缀下的不安全方法。
"""
from django.middleware.csrf import CsrfViewMiddleware

UNSAFE_METHODS = ('POST', 'PUT', 'PATCH', 'DELETE')


class CookieAuthCsrfMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._csrf = CsrfViewMiddleware(get_response)

    def __call__(self, request):
        if self._requires_csrf(request):
            # 确保 request.META["CSRF_COOKIE"] 就绪
            self._csrf.process_request(request)
            # 以“非 csrf_exempt”方式执行完整 CSRF 校验；返回 403 响应时直接短路
            rejected = self._csrf.process_view(request, None, None, None)
            if rejected is not None:
                return rejected
        return self.get_response(request)

    def _requires_csrf(self, request):
        path = getattr(request, 'path_info', '') or getattr(request, 'path', '')
        # 对所有 /api/ 写请求强制 CSRF（含 login/register，抵御 login CSRF）
        return request.method in UNSAFE_METHODS and path.startswith('/api/')
