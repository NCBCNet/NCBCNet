from django.core.management.base import BaseCommand, CommandError

from grading.services import reclaim_expired_assignments


class Command(BaseCommand):
    help = "回收超过租约时间的评卷任务"

    def add_arguments(self, parser):
        parser.add_argument("--timeout-minutes", type=int, default=30)

    def handle(self, *args, **options):
        timeout = options["timeout_minutes"]
        if timeout < 0:
            raise CommandError("--timeout-minutes 不能为负数")
        count = reclaim_expired_assignments(timeout_minutes=timeout)
        self.stdout.write(self.style.SUCCESS(f"已回收 {count} 个评卷任务"))
