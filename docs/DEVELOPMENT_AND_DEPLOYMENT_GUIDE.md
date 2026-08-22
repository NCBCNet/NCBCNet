# NCBCNet 开发与部署说明

> ⚠️ 本文档已合并进 **[`GUIDE.md`](./GUIDE.md)（统一操作指南）**，请以 GUIDE.md 为准。
> 关联：`ARCHITECTURE_ROADMAP.md`（架构路线）、`FRONTEND_MIGRATION_PLAN.md`（前端计划）、`SECURITY.md`（安全模型）。

## 1. 总体原则

1. **本地开发**：宿主机直跑 Django + Vite，不使用 Docker。
2. **生产部署**：单机 Docker Compose，Nginx 终止 TLS 并直接服务 SPA 静态产物；Daphne 只提供内网 HTTP。
3. **前后端分离**：前端是纯 SPA（React + AntD），后端只暴露 `/api/v1/` 与 `/admin/`。

---

## 2. 本地开发工作流

### 2.1 组件

| 组件 | 作用 |
| --- | --- |
| Python 3.12 | Django 后端 |
| Node.js 20+ | Vite 前端 |
| MySQL 8 | 生产数据库（开发默认 SQLite，可跳过） |
| Redis 7 | 生产缓存/会话/队列（开发默认进程内缓存，可跳过） |

### 2.2 首次准备（开发零配置）

```bash
# 只需装依赖；无需 .env、无需 MySQL/Redis（开发默认 SQLite + 进程内缓存）
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

> 开发环境无需任何环境变量：`SECRET_KEY` 用开发默认值、数据库用 `db.sqlite3`、
> 缓存用进程内 `LocMemCache`、主机白名单与 CSRF 来源默认放行本地。
> 只有**生产**才需要 `.env`（见第 3 节），且缺失 `DJANGO_SECRET_KEY`/`ALLOWED_HOSTS` 会拒绝启动。

### 2.3 启动

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

cd frontend && npm run dev -- --host 0.0.0.0 --port 5173
```

前端 `http://localhost:5173`，后端 `http://localhost:8000`。Vite 代理 `/api`、`/media`、`/static` 到后端。

### 2.4 认证与 CSRF（重要）

- 认证为 **HttpOnly Cookie JWT**（`nc_access` / `nc_refresh`），前端不存 token。
- 写请求必须携带 `X-CSRFToken`（取自 `csrftoken` Cookie，前端挂载时调用 `GET /api/v1/auth/csrf/` 获取）。
- 开发环境 `CSRF_TRUSTED_ORIGINS` 已内置默认值（`http://localhost:5173` 等），无需手动配置；仅在自定义端口/域名时才需覆盖。

### 2.5 常用命令

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py test --settings=NCBCNet.test_settings
cd frontend && npm run build
```

---

## 3. 生产部署工作流

### 3.1 架构

```text
浏览器 ──HTTPS──> Nginx(SPA 静态 + TLS 终止 + /api 反代)
                    ├─ /assets/ /  → frontend/dist（镜像内置）
                    ├─ /api/ /admin/ /mdeditor/ /ckeditor5/ → web:8000 (Daphne)
                    └─ /static/ /media/ → 命名卷
web:8000 ──> MySQL、Redis
worker ──> Redis 队列（RQ）
```

### 3.2 部署前准备

1. 准备 `.env`（从 `.env.example` 复制）。
2. 准备证书目录：`./certs/ncnetstudent.top.pem` 与 `./certs/ncnetstudent.top.key`。
3. 确保 `SECRET` 文件存在（Django `SECRET_KEY`，挂载到 `/app/SECRET`）。

### 3.3 启动部署

```bash
docker compose up -d --build
```

服务：`nginx`（80/443）、`web`（Daphne 内网）、`db`（MySQL）、`redis`、`worker`（RQ，可选）。

- `web` 与 `nginx` 均为多阶段构建产物：`web` 用根 `Dockerfile`，`nginx` 用 `docker/nginx.Dockerfile`（构建期 `npm ci && npm run build`，运行时镜像自带 SPA）。
- `web` 通过 `/api/v1/health/` 健康检查；`nginx` 依赖 `web` 健康后才启动。
- `worker` 与 `web` 同一镜像，`command: rq worker --with-scheduler`；不跑 migrate/collectstatic。

### 3.4 镜像与 CI/CD

```bash
docker build -t ncbcnet-web:latest .
docker build -f docker/nginx.Dockerfile -t ncbcnet-nginx:latest .
```

GitHub Actions 流程：后端测试 + `lint-imports`（架构边界）→ 前端构建 → push 后构建并推送两个镜像到 GHCR（`ncbcnet-web`、`ncbcnet-nginx`）。

---

## 4. 对象存储（阶段三，可选）

生产建议把媒体迁到 S3 兼容对象存储（MinIO / 阿里云 OSS / 腾讯云 COS），解除“文件绑死单机”。

1. 在 `.env` 配置：
   ```env
   OSS_ENDPOINT_URL=https://oss-cn-xxx.aliyuncs.com
   OSS_ACCESS_KEY_ID=...
   OSS_SECRET_ACCESS_KEY=...
   OSS_BUCKET=ncbcnet-media
   OSS_QUERYSTRING_AUTH=true
   ```
2. 迁移存量文件（先 `--dry-run`，分批，校验通过后再 `--delete-local`）：
   ```bash
   docker compose exec web python manage.py migrate_media_to_oss --dry-run
   docker compose exec web python manage.py migrate_media_to_oss
   ```
3. 私有下载在阶段三改为对象存储签名 URL；未迁移前走本地签名下载端点。

---

## 5. 备份与恢复

### 5.1 备份

`deploy/backup.sh`（建议 cron / systemd timer 每日执行）：MySQL `mysqldump | gzip` + 媒体卷 `tar`，可上传对象存储，按保留天数清理。

```bash
# 环境变量：DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD
./deploy/backup.sh
```

备份矩阵见 `ARCHITECTURE_ROADMAP.md` 6.6（MySQL 托管自动备份 + 每周额外 dump、媒体 OSS 版本控制、Redis 快照、密钥离线备份）。

### 5.2 恢复

1. 数据库：`gunzip db_xxx.sql.gz | mysql -h ... -u ... -p ... <db>`
2. 媒体：`tar -xzf media_xxx.tar.gz -C <MEDIA_ROOT>`
3. 建议季度演练一次恢复流程。

---

## 6. 安全清单（部署前核对）

- [ ] `DEBUG=false`、`APP_ENV=production`
- [ ] `ALLOWED_HOSTS`、`CSRF_TRUSTED_ORIGINS` 为真实域名白名单
- [ ] `DJANGO_SECRET_KEY` 为随机密钥（非默认值）
- [ ] `ENABLE_HTTPS_REDIRECT=true`、`AUTH_COOKIE_SECURE=true`
- [ ] 证书已就位且 `nginx.conf` 的 `server_name` 正确
- [ ] `.env` / `SECRET` 未提交到仓库
- [ ] 数据库 `DB_PASSWORD` 非默认值；对象存储使用私有读 + 签名访问
- [ ] 已执行过 `deploy/backup.sh` 并验证可恢复

---

## 7. 目录与文件说明

| 文件 | 作用 |
| --- | --- |
| `docker-compose.yml` | 生产部署（nginx/web/db/redis/worker） |
| `Dockerfile` | web 镜像 |
| `docker/nginx.Dockerfile` | nginx + SPA 镜像（多阶段） |
| `docker/entrypoint.sh` | 容器启动初始化（migrate/collectstatic） |
| `nginx/nginx.conf` | TLS 终止、SPA 静态、/api 反代、CSP |
| `deploy/backup.sh` | 备份脚本 |
| `core/tasks.py` | RQ 后台任务模块 |
| `file_save/management/commands/migrate_media_to_oss.py` | 媒体迁移命令 |
| `requirements.docker.txt` | 镜像 / CI 依赖 |
| `.env.example` | 环境变量模板 |
| `SECURITY.md` | 安全模型与漏洞报告 |
