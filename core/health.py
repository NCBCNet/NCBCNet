"""核心健康检查：探测各组件是否工作正常（M2：core 拥有健康检查）。

供 API 健康端点与运维使用。输出只包含「状态 + 友好说明 + 耗时」，
**绝不泄露**主机名、连接串、账号、错误堆栈等敏感内容。
"""
import time

from django.core.cache import cache
from django.db import connection


def _elapsed(probe):
    start = time.monotonic()
    ok, message = probe()
    latency_ms = round((time.monotonic() - start) * 1000, 1)
    return {'status': 'ok' if ok else 'error', 'message': message, 'latency_ms': latency_ms}


def check_database():
    """探测数据库连接。"""
    def _probe():
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
            return True, '数据库连接正常'
        except Exception:
            return False, '数据库连接异常'
    return _elapsed(_probe)


def check_cache():
    """探测缓存（Redis/LocMem）读写。"""
    def _probe():
        key = 'ncbcnet-health-check'
        try:
            cache.set(key, '1', timeout=5)
            ok = cache.get(key) == '1'
            cache.delete(key)
            return (True, '缓存读写正常') if ok else (False, '缓存读写异常')
        except Exception:
            return False, '缓存连接异常'
    return _elapsed(_probe)


def check_storage():
    """探测媒体存储可读写（写入临时对象后删除，自清理）。"""
    def _probe():
        import uuid
        from django.core.files.storage import default_storage

        key = f'health-check-{uuid.uuid4().hex}.tmp'
        try:
            with default_storage.open(key, 'wb') as fh:
                fh.write(b'ok')
            default_storage.delete(key)
            return True, '媒体存储读写正常'
        except Exception:
            return False, '媒体存储异常'
    return _elapsed(_probe)


def run_all_checks():
    """返回所有组件健康状态（脱敏）。"""
    components = {
        'database': check_database(),
        'cache': check_cache(),
        'storage': check_storage(),
    }
    overall = 'ok' if all(c['status'] == 'ok' for c in components.values()) else 'degraded'
    return {'status': overall, 'components': components}
