"""DRF 限流（ARCHITECTURE_ROADMAP 4.6.4）。

覆盖登录、注册、上传三个高风险端点，避免与 django-ratelimit 两套限流并存：
统一使用 DRF 内建 throttle。
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'
    rate = '5/min'


class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'
    rate = '3/min'


class UploadRateThrottle(UserRateThrottle):
    scope = 'upload'
    rate = '30/min'
