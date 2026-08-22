"""usermanage 业务服务层（阶段二 M2：模块化单体）。

约定：所有 ORM 操作与事务边界（transaction.atomic）都收敛在本层，
api 视图只做请求解析 / 序列化 / 响应组装，不再直接触碰模型。
"""
from django.contrib.auth import get_user_model
from django.db import transaction

from usermanage.models import Profile

User = get_user_model()

# 哨兵：区分“未传 email”与“显式置空 email”
_UNSET = object()


def register_user(username, password, email='', **extra):
    """创建用户并自动创建 Profile（事务内完成，保证一致性）。"""
    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **extra,
        )
        Profile.objects.get_or_create(user=user)
        return user


def get_or_create_profile(user):
    """获取用户资料，不存在则创建。"""
    profile, _created = Profile.objects.get_or_create(user=user)
    return profile


def update_profile(user, profile_data=None, email=_UNSET):
    """更新用户资料与邮箱。

    - profile_data：已校验的 Profile 字段字典（phone/avatar/bio），
      为空字典则跳过。
    - email：传 _UNSET 表示不修改邮箱；传 None/字符串则写入。
    """
    with transaction.atomic():
        if profile_data:
            profile, _created = Profile.objects.get_or_create(user=user)
            for field, value in profile_data.items():
                setattr(profile, field, value)
            profile.save()
        if email is not _UNSET:
            user.email = email
            user.save(update_fields=['email'])
        return user


def delete_user(user):
    """删除用户（Profile 通过 OneToOne CASCADE 一并删除）。"""
    with transaction.atomic():
        user.delete()
