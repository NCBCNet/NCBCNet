from django.db import models


class TimestampedModel(models.Model):
    """共享内核：提供 created_at / updated_at 时间戳的抽象基类。

    供各业务模块新建模型继承，避免重复定义时间字段（阶段二 M2 约定）。
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
