from django.core.management.base import BaseCommand, CommandError

from grading.models import RecognitionJob
from grading.services import enqueue_scan_batch


class Command(BaseCommand):
    help = "重新排队失败的扫描识别任务"

    def add_arguments(self, parser):
        parser.add_argument("--batch-id", type=int)
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        batch_id = options.get("batch_id")
        if batch_id:
            jobs = RecognitionJob.objects.filter(
                batch_id=batch_id, status=RecognitionJob.Status.FAILED
            )
        else:
            jobs = RecognitionJob.objects.filter(
                status=RecognitionJob.Status.FAILED
            ).order_by("created_at")[: options["limit"]]
        count = 0
        for job in jobs:
            enqueue_scan_batch(batch_id=job.batch_id)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"已重新排队 {count} 个识别任务"))
