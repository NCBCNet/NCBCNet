from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0008_scanpage_review_comment_scanpage_review_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='recognitionjob',
            name='max_retries',
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.AddField(
            model_name='recognitionjob',
            name='retry_count',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
