"""DRF 限流（ARCHITECTURE_ROADMAP 4.6.4）。

覆盖登录、注册、上传三个高风险端点，避免与 django-ratelimit 两套限流并存：
统一使用 DRF 内建 throttle。
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


# rate 统一在 settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] 配置，
# 类只声明 scope，便于测试环境覆盖、生产环境按需调整。
class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'


class RegisterRateThrottle(AnonRateThrottle):
    scope = 'register'


class UploadRateThrottle(UserRateThrottle):
    scope = 'upload'
