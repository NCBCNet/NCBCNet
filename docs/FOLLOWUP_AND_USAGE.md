# NCBCNet 后续工作与使用指南

> ⚠️ 本文档已合并进 **[`GUIDE.md`](./GUIDE.md)（统一操作指南）**，请以 GUIDE.md 为准。
> 本文档回答两件事：**改造完成后你还需要做什么**，以及**改造后的系统怎么用/怎么部署**。
> 关联：`ARCHITECTURE_ROADMAP.md`、`FRONTEND_MIGRATION_PLAN.md`、`SECURITY.md`。

---

## 1. 当前状态（已完成的改造）

| 维度 | 结果 |
| --- | --- |
| 前端 | 纯 React SPA（AntD 6），文件模块/评论组件/错误边界/懒加载/404·403·500 全部完成 |
| 认证 | **HttpOnly Cookie JWT**（`nc_access`/`nc_refresh`）+ CSRF，不再用 localStorage 存 token |
| API | 统一前缀 `/api/v1/`，统一错误格式 `{code,message,details}`，DRF 限流，`/api/v1/health/` |
| 授权 | 对象级权限 + 私有文件 **HMAC 签名短链**下载，`/media/uploads/` Nginx 403 |
| 架构 | M2 模块化单体：`core` + 各 app `services.py`，`comment` 已合入 `article`，`api` 零业务 model 依赖 |
| 部署 | Nginx 服务 SPA（多阶段镜像）、两镜像 CI、`worker`(RQ)、对象存储配置、备份脚本 |

---

## 2. 后续工作清单（按顺序做）

### 2.1 首次 push 到 GitHub，触发 CI 做最终确认

本仓库有 3 项验证**只能由 CI 出具最终凭证**（本机沙箱无法运行 esbuild/pip）：

1. `frontend-build` job：`npm ci && npm run build` 必须成功。
2. `backend-tests` job：新增了 `pip install import-linter` + `lint-imports` + `manage.py test`。
   - `lint-imports` 校验架构边界（`api` 不得 import 业务 models；分层契约，见 `pyproject.toml`）。
   - 测试在 Ubuntu CI 中应**全绿**（本机那 8 个 `file_save` 报 `WinError 5` 是沙箱临时目录限制，CI 无此问题）。
3. `docker-build-push` job：构建并推送 `ncbcnet-web`、`ncbcnet-nginx` 两个 GHCR 镜像。

> 若 CI 红灯：优先看 `frontend-build` 的构建错误（前端本地无法实跑 `vite build`，语法与 import 作用域已用 `@babel/parser` 静态校验过，但 CI 是最终裁决）。

### 2.2 在你自己的开发机做一次本地最终验证（无沙箱限制）

```bash
# 后端
pip install -r requirements.txt import-linter
python manage.py check
python manage.py test --settings=NCBCNet.test_settings
lint-imports                      # 应无违规

# 前端
cd frontend && npm install && npm run build
```

### 2.3 生产部署（单机 Docker Compose）

```bash
# 1) 准备环境与密钥
cp .env.example .env               # 改 DB 口令、ALLOWED_HOSTS、CSRF_TRUSTED_ORIGINS、DJANGO_SECRET_KEY
#    生成随机密钥：python -c "import secrets;print(secrets.token_urlsafe(50))"
# 2) 准备证书（目录 ./certs/）
#    certs/ncnetstudent.top.pem  certs/ncnetstudent.top.key
# 3) 准备 SECRET 文件（Django SECRET_KEY，挂载到 /app/SECRET）
# 4) 启动
docker compose up -d --build
```

验证清单：

- `https://你的域名/` 返回 SPA；刷新任意 SPA 路由（如 `/article/article_detail/1`）不 404。
- 登录 → 刷新页面保持登录 → 退出 全流程正常。
- 云盘：建文件夹 → 上传 → 下载 → 删除 → 共享切换。
- `https://你的域名/api/v1/health/` 返回 `{"status":"ok",...}`。
- `https://你的域名/admin/` 可用（Session 认证，与 SPA 的 JWT 相互独立）。

### 2.4 数据库迁移注意（重要，已处理好）

- 旧 `comment` 应用已删除，评论表物理名仍是 **`comment_comment`**（`article.Comment` 的 `db_table` 保留原名）。
- **既有库**：`migrate` 时 `article/0006`（只登记状态）+ `article/0007`（表已存在则跳过）——无 DDL、零数据风险。
- **全新库**：`article/0007` 会自动建出 `comment_comment` 表（已用全新 SQLite 实测通过）。
- 上线前建议先备份，再 `docker compose exec web python manage.py migrate --noinput`（entrypoint 默认已执行）。

### 2.5 对象存储（可选，阶段三）

```bash
# .env 增加
OSS_ENDPOINT_URL=https://oss-cn-xxx.aliyuncs.com
OSS_ACCESS_KEY_ID=...
OSS_SECRET_ACCESS_KEY=...
OSS_BUCKET=ncbcnet-media
OSS_QUERYSTRING_AUTH=true

# 迁移存量（先 dry-run，分批，校验通过后再 --delete-local）
docker compose exec web python manage.py migrate_media_to_oss --dry-run
docker compose exec web python manage.py migrate_media_to_oss
```

### 2.6 备份（强烈建议）

```bash
# 用 cron / systemd timer 每日执行 deploy/backup.sh
# 需环境变量 DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD
./deploy/backup.sh
```

建议季度做一次**恢复演练**（gunzip DB dump + 解压 media tar），确认备份可用。

### 2.7 安全加固待办（按需，来自 SECURITY.md）

1. **refresh token 黑名单**：当前登出为客户端删 Cookie，旧 refresh 到期前仍有效；如需服务端撤销，启用 `rest_framework_simplejwt.token_blacklist`。
2. **大文件下载优化**：当前走 Django `FileResponse` 流式；更高吞吐可切 Nginx `X-Accel-Redirect`（`/protected/` 已保留）或对象存储签名 URL。
3. **`/media/` 隐私**：头像等公开读；如需收紧可改签名访问。

---

## 3. 使用指南

### 3.1 本地开发

```bash
# 终端 1（后端）
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# 终端 2（前端）
cd frontend && npm install && npm run dev -- --host 0.0.0.0 --port 5173
```

- 前端 `http://localhost:5173`（Vite 代理 `/api` `/media` `/static` 到 8000）。
- **认证/CSRF 关键点**：token 在 HttpOnly Cookie 里，前端 JS 读不到；挂载时前端会自动调 `GET /api/v1/auth/csrf/` 拿 `csrftoken`，写请求自动回填 `X-CSRFToken`。开发环境 `.env` 的 `CSRF_TRUSTED_ORIGINS` 需包含 `http://localhost:5173`。

### 3.2 认证 API 速查（前缀 `/api/v1`）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/auth/csrf/` | 下发 `csrftoken` |
| POST | `/auth/login/` | 登录（写 HttpOnly Cookie） |
| POST | `/auth/refresh/` | 刷新 access（轮换） |
| POST | `/auth/logout/` | 登出（清 Cookie） |
| POST | `/auth/register/` | 注册并自动登录 |
| GET/PATCH | `/auth/me/` | 获取/更新当前用户 |
| DELETE | `/auth/delete/` | 删除账号 |
| GET | `/auth/check/` | 检查登录态 |
| GET | `/health/` | 健康检查 |

### 3.3 业务 API 速查（前缀 `/api/v1`）

- **文章**：`GET/POST /articles/`、`GET /articles/{id}/`、`POST /articles/create/`、`PUT /articles/{id}/update/`、`DELETE /articles/{id}/delete/`、`POST /articles/{id}/like/`、`GET /articles/columns/`
- **评论**：`POST /articles/{id}/comments/`、`POST /articles/{id}/comments/{cid}/reply/`
- **文件**：`GET/POST /folders/`、`DELETE /folders/{id}/delete/`、`GET /files/`、`POST /files/upload/`、`DELETE /files/{id}/delete/`、`POST /files/{id}/share/`、`GET /files/shared/`
- **私有下载（签名短链）**：
  1. `GET /files/{id}/download-url/`（登录 + 对象级授权）→ `{url, expires_in}`
  2. 用 `<a href={url}>` 触发下载（服务端校验 HMAC 签名 + 过期）

### 3.4 运维命令

```bash
# 后台任务 worker（消费 Redis 队列，core/tasks.py）
docker compose up -d worker

# 查看服务健康
docker compose ps

# 日志（应用已改为 stdout，直接 docker logs）
docker compose logs -f web
docker compose logs -f worker
```

---

## 4. 常见问题（FAQ）

- **登录成功但写操作报 403**：CSRF 未生效。确认前端已加载（会先调 `/auth/csrf/`），且 `CSRF_TRUSTED_ORIGINS` 包含当前来源。
- **下载报「下载链接已过期/无效」**：签名短链默认 300 秒（`DOWNLOAD_LINK_TTL` 可调），过期后重新点下载即可。
- **本机跑测试出现 `PermissionError [WinError 5]`**：这是 DSH 沙箱禁止写平台临时目录所致（Django 测试把 `MEDIA_ROOT` 指向临时目录）；在正常开发机 / CI 中不会出现。
- **`admin` 登录与 SPA 登录相互独立**：`/admin/` 用 Django Session，SPA 用 Cookie JWT，两边需各自登录。
