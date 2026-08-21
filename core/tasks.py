"""后台任务模块（阶段三：RQ worker）。

Web 请求内不做长任务；services 层把需要异步执行的工作入队：

    from core.tasks import get_queue
    get_queue().enqueue(ping_worker)

适用任务（ARCHITECTURE_ROADMAP 6.7）：AI 调用、缩略图生成、通知推送、文件后处理。
"""
import logging

logger = logging.getLogger(__name__)


def get_queue(name="default"):
    """返回 RQ 队列（惰性 import，避免 Web 进程强依赖 rq/redis 包）。"""
    import redis as redis_lib
    import rq
    from django.conf import settings

    conn = redis_lib.Redis.from_url(settings.REDIS_URL)
    return rq.Queue(name, connection=conn)


def ping_worker():
    """示例后台任务：验证 worker 队列可用。"""
    logger.info("worker ping ok")
    return "pong"


def process_uploaded_file(file_id):
    """上传后处理任务（预留脚手架，阶段三 worker）。

    当前上传流程无后处理环节，此任务为「上传后处理」预留入口：
    后续可在此实现缩略图生成、病毒扫描、转码、索引等耗时操作，
    由 FileUploadView 在上传完成后 `get_queue().enqueue(process_uploaded_file, file_id)` 入队。

    注意：文件「传输」无法后台化（必须由浏览器同步发出），只有「后处理」能入队。
    """
    from file_save.models import UploadedFile

    try:
        uploaded = UploadedFile.objects.get(pk=file_id)
    except UploadedFile.DoesNotExist:
        logger.warning("process_uploaded_file: file %s not found", file_id)
        return
    # TODO(阶段三): 在此实现真实后处理（缩略图/扫描/转码等）
    logger.info("process_uploaded_file: file %s (%s) queued for post-processing",
                file_id, uploaded.original_name)
    return file_id
