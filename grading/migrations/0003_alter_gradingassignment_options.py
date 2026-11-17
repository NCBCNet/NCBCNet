from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0002_gradingassignment_claimed_at_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gradingassignment',
            options={'ordering': ['answer_sheet_id', 'question__number'], 'permissions': [('grade_answers', '可以评阅答题')]},
        ),
    ]
