from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0007_gradingassignment_answer_block_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='scanpage',
            name='review_comment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='scanpage',
            name='review_required',
            field=models.BooleanField(default=True),
        ),
    ]
