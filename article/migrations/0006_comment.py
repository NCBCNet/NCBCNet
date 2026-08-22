"""ADR-004：评论模型并入文章域（comment → article）——状态登记。

背景
----
原 comment 应用与 article 应用互相导入形成循环依赖；M2 将 Comment 整体并入
article 域并删除 comment 应用，同时保留其物理表 `comment_comment`。

本迁移仅登记模型状态（SeparateDatabaseAndState(database_operations=[])），
不执行 DDL；既有安装的 `comment_comment` 表保持不变。
全新安装的建表由紧随其后的 `0007_comment_table` 完成（届时模型已登记到状态，
可安全地按需建表）。
"""
import django.db.models.deletion
import django_ckeditor_5.fields
import mptt.fields
import mptt.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0005_articletest_article_avatar_article_likes_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Comment',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('level', models.PositiveIntegerField(editable=False)),
                        ('lft', models.PositiveIntegerField(editable=False)),
                        ('rght', models.PositiveIntegerField(editable=False)),
                        ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                        ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='article.comment')),
                        ('reply_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replyers', to=settings.AUTH_USER_MODEL)),
                        ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='article.article')),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL)),
                        ('content', django_ckeditor_5.fields.CKEditor5Field(config_name='extends')),
                        ('created', models.DateTimeField(auto_now_add=True)),
                    ],
                    options={
                        'db_table': 'comment_comment',
                    },
                    bases=(mptt.models.MPTTModel,),
                ),
            ],
        ),
    ]
