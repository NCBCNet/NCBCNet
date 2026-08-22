"""把本地媒体文件迁移到对象存储（S3 兼容：MinIO / 阿里云 OSS / 腾讯云 COS）。

执行纪律（ARCHITECTURE_ROADMAP 6.4）：
- 先只读双写验证，再切换；切换前全量备份本地卷。
- 分批次迁移，每批校验（存在性 + 大小一致）。
- 本命令保留原相对路径作为对象 key（不改动业务字段），安全可重入。
"""
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import BaseCommand

from file_save.models import UploadedFile


class Command(BaseCommand):
    help = '将本地媒体文件迁移到对象存储（需已配置 OSS_ENDPOINT_URL）'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='只打印迁移计划，不实际迁移')
        parser.add_argument('--delete-local', action='store_true', help='校验通过后删除本地副本')

    def handle(self, *args, **options):
        if settings.DEFAULT_FILE_STORAGE == 'django.core.files.storage.FileSystemStorage':
            self.stderr.write(self.style.WARNING(
                '未配置对象存储（OSS_ENDPOINT_URL），默认存储仍为本地磁盘，无需迁移。'
            ))
            return

        local = FileSystemStorage(location=settings.MEDIA_ROOT)
        migrated = skipped = failed = 0

        for uf in UploadedFile.objects.select_related('owner').iterator():
            name = uf.file.name
            if not local.exists(name):
                self.stdout.write(self.style.WARNING(f'本地文件缺失，跳过: {name}'))
                skipped += 1
                continue
            if default_storage.exists(name):
                self.stdout.write(f'远程已存在，跳过: {name}')
                skipped += 1
                continue
            if options['dry_run']:
                self.stdout.write(f'[dry-run] 将迁移: {name} ({local.size(name)} bytes)')
                migrated += 1
                continue

            try:
                with local.open(name, 'rb') as fh:
                    default_storage.save(name, fh)

                if default_storage.exists(name) and default_storage.size(name) == local.size(name):
                    uf.file.name = name
                    uf.save(update_fields=['file'])
                    if options['delete_local']:
                        local.delete(name)
                    migrated += 1
                    self.stdout.write(self.style.SUCCESS(f'已迁移: {name}'))
                else:
                    failed += 1
                    self.stderr.write(f'校验失败（大小不一致或不存在）: {name}')
            except Exception as exc:  # noqa: BLE001
                failed += 1
                self.stderr.write(f'迁移失败: {name} - {exc}')

        self.stdout.write(self.style.SUCCESS(
            f'完成：迁移 {migrated}，跳过 {skipped}，失败 {failed}'
        ))
