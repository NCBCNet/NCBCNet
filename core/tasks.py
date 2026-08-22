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
    """上传后处理任务（阶段三 worker）：图片生成缩略图 + 计算 SHA256。

    由 file_save.services.upload_file 在上传保存后入队；RQ/Redis 不可用时同步兜底执行。
    文件「传输」无法后台化（必须由浏览器同步发出），只有「后处理」能入队。
    """
    import hashlib

    from file_save.models import UploadedFile

    try:
        uploaded = UploadedFile.objects.get(pk=file_id)
    except UploadedFile.DoesNotExist:
        logger.warning("process_uploaded_file: file %s not found", file_id)
        return

    try:
        # 1) SHA256（分块读取，避免整文件入内存）
        sha = hashlib.sha256()
        with uploaded.file.open('rb') as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b''):
                sha.update(chunk)
        uploaded.sha256 = sha.hexdigest()

        # 2) 图片缩略图（仅图片）
        if _is_image(uploaded.original_name):
            _generate_thumbnail(uploaded)

        uploaded.status = 'done'
        uploaded.save(update_fields=['status', 'sha256', 'thumbnail'])
        logger.info("process_uploaded_file: %s done", file_id)
    except Exception:
        logger.exception("process_uploaded_file: %s failed", file_id)
        UploadedFile.objects.filter(pk=file_id).update(status='failed')


def _is_image(name):
    """按扩展名判断是否为图片。"""
    ext = (name or '').rsplit('.', 1)[-1].lower() if '.' in (name or '') else ''
    return ext in {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}


def _generate_thumbnail(uploaded, size=(200, 200)):
    """为图片生成 JPEG 缩略图并写入 thumbnail 字段（失败则跳过，不影响状态）。"""
    import io

    from django.core.files.base import ContentFile
    from PIL import Image

    try:
        with Image.open(uploaded.file.path) as img:
            img = img.convert('RGB')
            img.thumbnail(size, Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=85)
    except Exception:
        return

    uploaded.thumbnail.save(
        f'thumb_{uploaded.pk}.jpg',
        ContentFile(buf.getvalue()),
        save=False,
    )
