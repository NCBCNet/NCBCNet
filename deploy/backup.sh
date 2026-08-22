#!/usr/bin/env bash
# NCBCNet 备份脚本（ARCHITECTURE_ROADMAP 6.6）
# 用法：在部署主机上以 cron 或 systemd timer 定期执行，例如每日 03:00。
#   ./deploy/backup.sh
# 需要环境变量：DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD，
# 可选（上传到 OSS 时）：OSS_ENDPOINT_URL / OSS_ACCESS_KEY_ID / OSS_SECRET_ACCESS_KEY / OSS_BUCKET。
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/backup}"
STAMP="$(date +%F_%H%M%S)"
KEEP_DAYS="${KEEP_DAYS:-14}"

mkdir -p "${BACKUP_DIR}"

# ---------- PostgreSQL 备份 ----------
DB_DUMP="${BACKUP_DIR}/db_${STAMP}.sql.gz"
echo "[backup] dumping PostgreSQL ${DB_NAME}..."
# pg_dump 通过 PGPASSWORD 环境变量读取口令（无内联密码参数）
PGPASSWORD="${DB_PASSWORD}" pg_dump \
  -h "${DB_HOST}" -p "${DB_PORT:-5432}" \
  -U "${DB_USER}" \
  --format=plain --no-owner --no-privileges "${DB_NAME}" \
  | gzip > "${DB_DUMP}"

# ---------- 媒体文件备份（本地卷 tar） ----------
MEDIA_DIR="${MEDIA_DIR:-/app/mediafiles}"
MEDIA_TAR="${BACKUP_DIR}/media_${STAMP}.tar.gz"
echo "[backup] archiving media ${MEDIA_DIR}..."
tar -czf "${MEDIA_TAR}" -C "${MEDIA_DIR}" . 2>/dev/null || true

# ---------- 上传到对象存储（可选） ----------
if [[ -n "${OSS_ENDPOINT_URL:-}" && -n "${OSS_BUCKET:-}" ]]; then
  echo "[backup] uploading to object storage..."
  # 依赖 ossutil / s3cmd 等 CLI；按实际对象存储替换。
  # 示例（阿里云 ossutil）：
  # ossutil cp "${DB_DUMP}" "oss://${OSS_BUCKET}/db/" -f
  # ossutil cp "${MEDIA_TAR}" "oss://${OSS_BUCKET}/media/" -f
  echo "[backup] （对象存储上传命令请按实际 CLI 启用，见脚本注释）"
fi

# ---------- 清理过期备份 ----------
echo "[backup] cleaning backups older than ${KEEP_DAYS} days..."
find "${BACKUP_DIR}" -type f -mtime "+${KEEP_DAYS}" -delete

echo "[backup] done: ${DB_DUMP} ${MEDIA_TAR}"
