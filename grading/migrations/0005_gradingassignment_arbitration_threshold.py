from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0004_gradingassignment_round_no_arbitrationcase_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='gradingassignment',
            name='arbitration_threshold',
            field=models.DecimalField(decimal_places=2, default=2, max_digits=6),
        ),
    ]
