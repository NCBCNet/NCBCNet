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
