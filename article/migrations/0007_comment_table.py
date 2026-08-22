"""ADR-004 配套：按需创建 `comment_comment` 物理表。

`0006_comment` 已把 Comment 模型登记到 article 应用状态（db_table='comment_comment'），
本迁移在数据库层按需建表：

- 既有安装：`comment_comment` 表已存在 → 跳过（无 DDL）。
- 全新安装：表不存在 → 按当前模型建出 `comment_comment` 表。
"""
from django.db import migrations


def create_comment_table_if_missing(apps, schema_editor):
    Comment = apps.get_model('article', 'Comment')
    table_names = schema_editor.connection.introspection.table_names()
    if Comment._meta.db_table not in table_names:
        schema_editor.create_model(Comment)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('article', '0006_comment'),
    ]

    operations = [
        migrations.RunPython(create_comment_table_if_missing, noop),
    ]
