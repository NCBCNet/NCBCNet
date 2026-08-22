"""统一 DRF 错误响应格式（ARCHITECTURE_ROADMAP 4.6.2）。

所有错误统一返回：{ "code": <机器码>, "message": <可读文案>, "details": <结构化详情> }
"""
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    details = {}
    if isinstance(response.data, dict):
        details = response.data
    elif isinstance(response.data, list):
        details = {'errors': response.data}

    response.data = {
        'code': _map_code(exc, response.status_code),
        'message': _map_message(exc, response.status_code),
        'details': details,
    }
    return response


def _map_code(exc, status_code):
    if isinstance(exc, (drf_exceptions.AuthenticationFailed, drf_exceptions.NotAuthenticated)):
        return 'not_authenticated'
    if isinstance(exc, drf_exceptions.PermissionDenied):
        return 'permission_denied'
    if isinstance(exc, (drf_exceptions.NotFound, Http404)):
        return 'not_found'
    if isinstance(exc, drf_exceptions.Throttled):
        return 'throttled'
    if isinstance(exc, drf_exceptions.ValidationError):
        return 'validation_error'
    if isinstance(exc, drf_exceptions.MethodNotAllowed):
        return 'method_not_allowed'
    if status_code == 401:
        return 'not_authenticated'
    if status_code == 403:
        return 'permission_denied'
    if status_code == 404:
        return 'not_found'
    if status_code == 429:
        return 'throttled'
    return 'error'


def _map_message(exc, status_code):
    if status_code == 401:
        return '未登录或登录已过期'
    if status_code == 403:
        return '没有权限执行该操作'
    if status_code == 404:
        return '资源不存在'
    if status_code == 429:
        return '请求过于频繁，请稍后再试'
    if isinstance(exc, drf_exceptions.ValidationError):
        return '请求参数校验失败'
    detail = getattr(exc, 'detail', None)
    if isinstance(detail, str) and detail:
        return detail
    return '请求处理失败'
