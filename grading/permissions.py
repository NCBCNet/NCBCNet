from rest_framework.permissions import BasePermission


TEACHER_GROUP = "教师"


def is_teacher(user):
    return bool(
        user
        and user.is_authenticated
        and user.groups.filter(name=TEACHER_GROUP).exists()
    )


class IsTeacher(BasePermission):
    message = "需要教师账号权限"

    def has_permission(self, request, view):
        return is_teacher(request.user)
