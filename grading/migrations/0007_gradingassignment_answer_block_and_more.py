import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0006_examtemplate_scanpage_answerblock_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='gradingassignment',
            name='answer_block',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='assignments', to='grading.answerblock'),
        ),
        migrations.AddField(
            model_name='gradingassignment',
            name='draft_comment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='gradingassignment',
            name='draft_score',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
        migrations.AddField(
            model_name='gradingassignment',
            name='lease_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='QualityReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', '待质检'), ('passed', '通过'), ('failed', '不通过')], default='pending', max_length=20)),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quality_reviews', to='grading.gradingassignment')),
                ('reviewer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='quality_reviews', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ReleaseApproval',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', '待审批'), ('approved', '已批准'), ('rejected', '已驳回'), ('published', '已发布')], default='pending', max_length=20)),
                ('comment', models.TextField(blank=True)),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('exam', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='release_approval', to='grading.exam')),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='release_requests', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='release_reviews', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ScoreSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_score', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('objective_score', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('subjective_score', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('status', models.CharField(choices=[('draft', '草稿'), ('locked', '已锁定'), ('released', '已发布')], default='draft', max_length=20)),
                ('version', models.PositiveIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('locked_at', models.DateTimeField(blank=True, null=True)),
                ('released_at', models.DateTimeField(blank=True, null=True)),
                ('answer_sheet', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='score_snapshot', to='grading.answersheet')),
            ],
        ),
        migrations.CreateModel(
            name='TeacherProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subjects', models.JSONField(blank=True, default=list)),
                ('question_numbers', models.JSONField(blank=True, default=list)),
                ('max_active_assignments', models.PositiveIntegerField(default=50)),
                ('enabled', models.BooleanField(default=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
