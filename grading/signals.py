from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate, dispatch_uid="grading.ensure_teacher_group")
def ensure_teacher_group(sender, **kwargs):
    if sender.name != "grading":
        return
    content_type = ContentType.objects.get(
        app_label="grading",
        model="gradingassignment",
    )
    permission = Permission.objects.get(
        content_type=content_type,
        codename="grade_answers",
    )
    group, _ = Group.objects.get_or_create(name="教师")
    group.permissions.add(permission)
