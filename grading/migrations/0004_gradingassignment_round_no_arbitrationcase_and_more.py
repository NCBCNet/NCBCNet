import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0003_alter_gradingassignment_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='gradingassignment',
            name='round_no',
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.CreateModel(
            name='ArbitrationCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('threshold', models.DecimalField(decimal_places=2, default=2, max_digits=6)),
                ('status', models.CharField(choices=[('open', '待仲裁'), ('resolved', '已解决')], default='open', max_length=20)),
                ('final_score', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('resolution_comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('answer_sheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='arbitration_cases', to='grading.answersheet')),
                ('assignments', models.ManyToManyField(related_name='arbitration_cases', to='grading.gradingassignment')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='arbitration_cases', to='grading.question')),
                ('resolved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='resolved_arbitration_cases', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RecognitionJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('queued', '排队中'), ('processing', '处理中'), ('completed', '已完成'), ('failed', '失败')], default='queued', max_length=20)),
                ('engine', models.CharField(default='pillow-layout-v1', max_length=100)),
                ('processed_pages', models.PositiveIntegerField(default=0)),
                ('result', models.JSONField(blank=True, default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('batch', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='recognition_job', to='grading.scanbatch')),
            ],
        ),
    ]
