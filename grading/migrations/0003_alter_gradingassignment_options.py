from django.db import migrations


def create_teacher_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    group, _ = Group.objects.get_or_create(name="教师")
    content_type = ContentType.objects.get(
        app_label="grading", model="gradingassignment"
    )
    permission = Permission.objects.get(
        content_type=content_type, codename="grade_answers"
    )
    group.permissions.add(permission)


def remove_teacher_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="教师").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0002_gradingassignment_claimed_at_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gradingassignment',
            options={'ordering': ['answer_sheet_id', 'question__number'], 'permissions': [('grade_answers', '可以评阅答题')]},
        ),
        migrations.RunPython(create_teacher_group, remove_teacher_group),
    ]
