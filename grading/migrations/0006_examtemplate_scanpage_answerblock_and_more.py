import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('grading', '0005_gradingassignment_arbitration_threshold'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveIntegerField(default=1)),
                ('page_width', models.PositiveIntegerField(default=2480)),
                ('page_height', models.PositiveIntegerField(default=3508)),
                ('alignment_markers', models.JSONField(blank=True, default=list)),
                ('blocks', models.JSONField(blank=True, default=dict)),
                ('omr_regions', models.JSONField(blank=True, default=list)),
                ('active', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('exam', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='template', to='grading.exam')),
            ],
        ),
        migrations.CreateModel(
            name='ScanPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('page_no', models.PositiveIntegerField()),
                ('source_image', models.ImageField(upload_to='grading/pages/%Y/%m/%d/')),
                ('normalized_image', models.ImageField(blank=True, upload_to='grading/normalized/%Y/%m/%d/')),
                ('status', models.CharField(choices=[('received', '已接收'), ('normalized', '已标准化'), ('review', '待复核'), ('failed', '失败')], default='received', max_length=20)),
                ('width', models.PositiveIntegerField(default=0)),
                ('height', models.PositiveIntegerField(default=0)),
                ('rotation', models.SmallIntegerField(default=0)),
                ('quality', models.CharField(default='review', max_length=20)),
                ('quality_reasons', models.JSONField(blank=True, default=list)),
                ('ocr_result', models.JSONField(blank=True, default=dict)),
                ('omr_result', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='grading.scanbatch')),
            ],
            options={
                'ordering': ['batch_id', 'page_no'],
            },
        ),
        migrations.CreateModel(
            name='AnswerBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='grading/blocks/%Y/%m/%d/')),
                ('bbox', models.JSONField(default=list)),
                ('status', models.CharField(choices=[('ready', '待分发'), ('assigned', '已分发'), ('review', '待复核')], default='ready', max_length=20)),
                ('quality', models.CharField(default='pass', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('answer_sheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocks', to='grading.answersheet')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='answer_blocks', to='grading.question')),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='answer_blocks', to='grading.scanpage')),
            ],
        ),
        migrations.AddConstraint(
            model_name='scanpage',
            constraint=models.UniqueConstraint(fields=('batch', 'page_no'), name='unique_batch_page_no'),
        ),
        migrations.AddConstraint(
            model_name='answerblock',
            constraint=models.UniqueConstraint(fields=('answer_sheet', 'question'), name='unique_sheet_question_block'),
        ),
    ]
