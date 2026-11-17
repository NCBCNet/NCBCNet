import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='考试名称')),
                ('code', models.CharField(max_length=64, unique=True, verbose_name='考试编码')),
                ('subject', models.CharField(max_length=100, verbose_name='科目')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('active', '评卷中'), ('closed', '已结束')], default='draft', max_length=20, verbose_name='状态')),
                ('starts_at', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('ends_at', models.DateTimeField(blank=True, null=True, verbose_name='结束时间')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_exams', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AnswerSheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('candidate_no', models.CharField(max_length=100, verbose_name='考号')),
                ('page_image', models.ImageField(blank=True, upload_to='grading/sheets/%Y/%m/%d/', verbose_name='答题卡图像')),
                ('status', models.CharField(choices=[('pending', '待分发'), ('grading', '评阅中'), ('completed', '已完成'), ('review', '待复核')], default='pending', max_length=20, verbose_name='状态')),
                ('objective_score', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('subjective_score', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answer_sheets', to='grading.exam')),
            ],
            options={
                'ordering': ['candidate_no'],
            },
        ),
        migrations.CreateModel(
            name='GradingAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=100)),
                ('object_type', models.CharField(max_length=100)),
                ('object_id', models.PositiveBigIntegerField()),
                ('payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='题号')),
                ('title', models.CharField(max_length=200, verbose_name='题目名称')),
                ('max_score', models.DecimalField(decimal_places=2, max_digits=6, validators=[django.core.validators.MinValueValidator(0)], verbose_name='满分')),
                ('rubric', models.JSONField(blank=True, default=dict, verbose_name='评分细则')),
                ('is_objective', models.BooleanField(default=False, verbose_name='客观题')),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='grading.exam')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='GradingAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('assigned', '待评阅'), ('in_progress', '评阅中'), ('submitted', '已提交'), ('expired', '已过期')], default='assigned', max_length=20)),
                ('score', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('comment', models.TextField(blank=True)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('answer_sheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='grading.answersheet')),
                ('grader', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='grading_assignments', to=settings.AUTH_USER_MODEL)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assignments', to='grading.question')),
            ],
            options={
                'ordering': ['answer_sheet_id', 'question__number'],
            },
        ),
        migrations.CreateModel(
            name='ScanBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_no', models.CharField(max_length=100, verbose_name='批次号')),
                ('source_file', models.FileField(upload_to='grading/scans/%Y/%m/%d/', verbose_name='扫描文件')),
                ('status', models.CharField(choices=[('received', '已接收'), ('processing', '处理中'), ('ready', '待分发'), ('failed', '失败')], default='received', max_length=20, verbose_name='状态')),
                ('page_count', models.PositiveIntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('exam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scan_batches', to='grading.exam')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddField(
            model_name='answersheet',
            name='batch',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='answer_sheets', to='grading.scanbatch'),
        ),
        migrations.AddConstraint(
            model_name='question',
            constraint=models.UniqueConstraint(fields=('exam', 'number'), name='unique_exam_question_number'),
        ),
        migrations.AddConstraint(
            model_name='gradingassignment',
            constraint=models.UniqueConstraint(fields=('answer_sheet', 'question', 'grader'), name='unique_grader_assignment'),
        ),
        migrations.AddConstraint(
            model_name='scanbatch',
            constraint=models.UniqueConstraint(fields=('exam', 'batch_no'), name='unique_exam_batch_no'),
        ),
        migrations.AddConstraint(
            model_name='answersheet',
            constraint=models.UniqueConstraint(fields=('exam', 'candidate_no'), name='unique_exam_candidate_no'),
        ),
    ]
