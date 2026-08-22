# NCBCNet 统一操作指南

> 本文档是 NCBCNet 的**唯一可操作入口**：覆盖从「本地跑起来」到「生产上线」到「日常运维」的全部步骤。
> 设计决策见 `ARCHITECTURE_ROADMAP.md`；安全细节见 `SECURITY.md`；历史迁移记录见 `FRONTEND_MIGRATION_PLAN.md`。

---

## 1. 项目概览

南城网 —— 校园/社区综合服务平台（论坛 + 云盘 + 学习）。

| 层 | 技术 |
| --- | --- |
| 前端 | React 19 + Ant Design 6 + Vite 7 + React Router 7（纯 SPA） |
| 后端 | Django 6.0.2 + DRF 3.16 + SimpleJWT（Cookie 认证） |
| 数据库 | 开发 SQLite / 生产 PostgreSQL 16 |
| 缓存/队列 | 开发进程内缓存 / 生产 Redis 7 + RQ |
| 部署 | 单机 Docker Compose（nginx + web + db + redis + worker） |

```
浏览器 ──HTTPS──> Nginx(SPA 静态 + TLS + /api 反代)
                    ├─ / /assets/  → SPA（镜像内置）
                    ├─ /api/ /admin/ /mdeditor/ /ckeditor5/ → web:8000 (Daphne)
                    └─ /static/ /media/ → 命名卷
web:8000 ──> PostgreSQL、Redis
worker(RQ) ──> Redis 队列
```

---

## 2. 快速开始

### 2.1 本地开发（零配置，不需要 .env / PostgreSQL / Redis）

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# 另一个终端
cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 5173
```

- 前端 `http://localhost:5173`（Vite 代理 `/api` `/media` `/static` `/admin` `/mdeditor` `/ckeditor5`）。
- 后端 `http://localhost:8000`。
- 默认：SQLite + 进程内缓存 + 开发密钥 + localhost 白名单，**无需任何环境变量**。

> 可选：开发环境要用 RQ 异步后处理，需 `pip install rq`、启动 Redis、另开 `rq worker`；
> 不装也不影响（后处理自动「同步兜底」，缩略图与校验和照常生成）。

### 2.2 生产部署（Docker Compose）

```bash
# 1) 环境与密钥
cp .env.example .env          # 填 DJANGO_SECRET_KEY / ALLOWED_HOSTS / DB_* 等（见第 4 节）
# 2) 证书
#    ./certs/ncnetstudent.top.pem   ./certs/ncnetstudent.top.key
# 3) SECRET 文件（Django SECRET_KEY）
# 4) 启动
docker compose up -d --build
```

- `web` 通过 `/api/v1/health/` 健康检查；`nginx` 等其健康后才启动。
- `worker`（RQ）随 Compose 启动，消费 Redis 队列。

---

## 3. 架构与目录

### 3.1 已完成改造（M1/M2/M3）

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| M1 | 纯 SPA 前后端分离 + 安全加固（Nginx 服务 SPA、`/api/v1/`、CSP、限流、统一错误、健康检查） | ✅ |
| M2 | 模块化单体（`core` + 各 app `services.py`、comment 合入 article、`api` 零业务 model 依赖、AST 边界测试） | ✅ |
| M3 | 配置/脚本（对象存储、备份、RQ worker、日志 stdout） | ✅ |

### 3.2 关键目录

| 路径 | 作用 |
| --- | --- |
| `NCBCNet/settings.py` | 全局配置（环境变量驱动） |
| `core/` | 共享内核（`models.py` 时间戳、`health.py` 健康探测、`tasks.py` RQ 任务） |
| `api/` | DRF 表现层（薄适配：只调 services，不碰 models） |
| `article/` | 文章 + 评论域（`services.py` / `serializers.py`） |
| `file_save/` | 文件域（`services.py` / `serializers.py` / `management/commands/migrate_media_to_oss.py`） |
| `usermanage/` | 用户域 |
| `frontend/src/` | SPA（`pages/`、`components/`、`services/`、`store/`） |
| `nginx/nginx.conf` | TLS 终止 + SPA + 反代 + CSP |
| `docker/nginx.Dockerfile` | nginx + SPA 多阶段镜像 |
| `deploy/backup.sh` | 备份脚本 |
| `pyproject.toml` | import-linter 架构边界契约 |

---

## 4. 配置说明

完整模板见 `.env.example`。要点：

| 变量 | 开发（默认） | 生产（必填） |
| --- | --- | --- |
| `APP_ENV` / `DEBUG` | `development` / `true` | `production` / `false` |
| `DJANGO_SECRET_KEY` | 开发默认 | **必填**（否则拒绝启动） |
| `ALLOWED_HOSTS` | `*` | **必填**（不允许 `*`） |
| `CSRF_TRUSTED_ORIGINS` | 自动 localhost:5173/8000 | 填真实域名 |
| `DB_ENGINE` / `DB_*` | `sqlite`（无需配置） | `postgresql`（必填） |
| `REDIS_URL` | 进程内缓存 | 默认 `redis://redis:6379/1` |
| `ENABLE_HTTPS_REDIRECT` / `AUTH_COOKIE_SECURE` | `false` | `true` |
| `OSS_*` | 本地磁盘 | 可选（对象存储） |

> 生产校验：`DJANGO_SECRET_KEY` 为开发默认值、或 `ALLOWED_HOSTS` 含 `*` 时，**启动直接报错**。

---

## 5. API 契约

统一前缀 **`/api/v1/`**。错误统一为 `{code, message, details}`。

### 5.1 认证（HttpOnly Cookie）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/auth/csrf/` | 下发 `csrftoken` |
| POST | `/auth/login/` | 登录（写 HttpOnly Cookie） |
| POST | `/auth/refresh/` | 刷新（轮换） |
| POST | `/auth/logout/` | 登出（清 Cookie） |
| POST | `/auth/register/` | 注册并自动登录 |
| GET/PATCH | `/auth/me/` | 获取/更新当前用户 |
| DELETE | `/auth/delete/` | 删除账号 |
| GET | `/auth/check/` | 检查登录态 |

### 5.2 健康检查

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/health/` | 存活探测（`{"status":"ok"}`） |
| GET | `/health/components/` | 组件级状态（database/cache/storage，脱敏） |

### 5.3 文章 / 评论

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/articles/` | 列表（分页 `results`/`count`；参数 search/column/tag/order/page） |
| GET | `/articles/columns/` | 栏目（纯数组，不分页） |
| POST | `/articles/create/` | 创建（返回含 `id`） |
| GET | `/articles/{id}/` | 详情 |
| PUT | `/articles/{id}/update/` | 更新（仅作者） |
| DELETE | `/articles/{id}/delete/` | 删除（仅作者） |
| POST | `/articles/{id}/like/` | 点赞 |
| POST | `/articles/{id}/comments/` | 发表评论 |
| POST | `/articles/{id}/comments/{cid}/reply/` | 回复评论 |

### 5.4 文件 / 下载

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET/POST | `/folders/` | 文件夹列表/创建（纯数组） |
| DELETE | `/folders/{id}/delete/` | 删文件夹 |
| GET | `/files/` | 文件列表（纯数组；参数 folder / shared=true） |
| POST | `/files/upload/` | 上传（multipart `file` + 可选 `folder`） |
| DELETE | `/files/{id}/delete/` | 删文件 |
| POST | `/files/{id}/share/` | 切换共享 |
| GET | `/files/shared/` | 共享文件列表 |
| GET | `/files/{id}/download-url/` | 获取签名下载链接（登录 + 对象级授权） |
| GET | `/files/{id}/download/` | 签名校验后下载（`?exp=&sig=`，免登录） |

---

## 6. 认证与安全

- **认证**：access/refresh 存 **HttpOnly + Secure + SameSite Cookie**（`nc_access` / `nc_refresh`），前端 JS 读不到。
- **CSRF**：所有 `/api/` 写请求需携带 `X-CSRFToken`（取自 `csrftoken` Cookie）；前端挂载时自动调 `/auth/csrf/`。
- **私有文件下载**：先 `/files/{id}/download-url/` 换取 **HMAC 签名 + 过期** 的短链，再 `<a href>` 触发；`/media/uploads/` 在 Nginx 直接 403。
- **对象级授权**：文章仅作者可改/删；文件仅 owner 可删/共享；共享文件对登录用户可见。
- **CSP**：SPA 由 Nginx 下发；Django 页面由 `SECURE_CSP`；移除 CORS（同源部署）。
- **限流**：DRF throttle（登录 5/min、注册 3/min、上传 30/min）。

---

## 7. 功能与运维

### 7.1 网站状态页

- SPA：`/health`（页脚「网站状态」）。
- API：`/api/v1/health/components/`（database/cache/storage 三组件状态 + 耗时，公开脱敏）。

### 7.2 上传任务中心（RQ）

- 上传后，`process_uploaded_file` 任务在 worker 里生成**缩略图** + 计算 **SHA256**，文件标记 processing→done/failed。
- 右上角上传图标（带角标）→ 抽屉集中查看：状态/进度/速度/剩余时间/失败原因/清除已完成。
- 文件网格显示图片缩略图 + 「处理中」标签。
- 开发无 RQ 时自动同步兜底。

### 7.3 后台 worker

```bash
docker compose up -d worker     # 生产（Compose 已含）
rq worker                       # 开发（需本机 Redis）
```

### 7.4 备份

```bash
./deploy/backup.sh              # PostgreSQL dump + 媒体 tar + 可选对象存储上传
# 建议 cron / systemd timer 每日执行；季度做一次恢复演练
```

### 7.5 对象存储（可选，S3 兼容）

```bash
# .env 配置 OSS_ENDPOINT_URL / OSS_ACCESS_KEY_ID / OSS_SECRET_ACCESS_KEY / OSS_BUCKET
docker compose exec web python manage.py migrate_media_to_oss --dry-run
docker compose exec web python manage.py migrate_media_to_oss
```

---

## 8. 部署检查清单（上线前逐项核对）

- [ ] `DEBUG=false`、`APP_ENV=production`
- [ ] `DJANGO_SECRET_KEY` 为随机密钥、`ALLOWED_HOSTS` 为真实域名
- [ ] 证书已就位、`nginx.conf` 的 `server_name` 正确
- [ ] `.env` / `SECRET` 未提交到仓库
- [ ] `python manage.py migrate` 已执行（含 `0004` 上传后处理字段、`article/0007` 评论表）
- [ ] `/api/v1/health/` 返回 ok；SPA 刷新路由不 404；登录→刷新→退出全流程通过
- [ ] 上传→缩略图/SHA256→下载→共享 全链路通过
- [ ] `deploy/backup.sh` 已跑通并可恢复

---

## 9. 常见问题（FAQ）

- **写操作 403**：CSRF 未生效。确认前端已加载（会先调 `/auth/csrf/`），且 `CSRF_TRUSTED_ORIGINS` 含当前来源。
- **下载「链接无效/已过期」**：签名短链默认 300 秒（`DOWNLOAD_LINK_TTL`），过期后重新点下载即可。
- **本机测试报 `WinError 5`**：DSH 沙箱禁止写平台临时目录（测试把 MEDIA_ROOT 指向临时目录）；正常开发机/CI 无此问题。
- **admin 与 SPA 登录独立**：`/admin/` 用 Session，SPA 用 Cookie JWT，需分别登录。
- **上传后一直「处理中」**：worker 未运行或 Redis 不可用。生产 `docker compose ps` 确认 worker 在跑；开发未装 rq 时走同步兜底应很快完成。
- **架构边界如何守护**：「api 不得导入业务 models」由 `api/tests.py` 的 `ApiBoundaryTests`（AST 扫描）在 Django 测试中强制执行。曾尝试用 import-linter，但本项目应用为顶层平级包、无根包，import-linter 无法适配，已弃用。

---

## 10. 文档索引

| 文档 | 内容 |
| --- | --- |
| `ARCHITECTURE_ROADMAP.md` | 架构路线与实现规范（M1/M2/M3 决策、ADR） |
| `SECURITY.md` | 安全模型与漏洞报告 |
| `FRONTEND_MIGRATION_PLAN.md` | 前端迁移历史（阶段一至六，已全部完成） |
| `.env.example` | 环境变量模板 |
