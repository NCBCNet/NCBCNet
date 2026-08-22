[![](https://img.shields.io/badge/python-3.12-orange.svg)](https://www.python.org/downloads/release/python-3120/)
[![](https://img.shields.io/badge/django-6.0.2-green.svg)](https://docs.djangoproject.com/en/6.0/releases/6.0/)
[![](https://img.shields.io/badge/vite-7.x-blue.svg)](https://vitejs.dev/)
[![](https://img.shields.io/badge/react-19.x-61dafb.svg)](https://react.dev/)
[![](https://img.shields.io/badge/license-AGPL_3.0-000000.svg)](https://www.gnu.org/licenses/agpl-3.0.html)

# NCBCNet
[简体中文](README.md) | [English](README_EN.md)

南城网 —— 校园/社区综合服务平台（论坛 + 云盘 + 学习）。

## 架构

前后端分离：React 19 + Ant Design 6 SPA（Vite 7 构建），Django + DRF 提供 `/api/v1/` REST API。
认证采用 **HttpOnly Cookie JWT + CSRF**，私有文件下载采用 **HMAC 签名短链**。详见：

- 📖 **[`docs/GUIDE.md`](docs/GUIDE.md) —— 统一操作指南（从这里开始）**
- [`docs/ARCHITECTURE_ROADMAP.md`](docs/ARCHITECTURE_ROADMAP.md) —— 架构路线（M1/M2/M3）
- [`docs/FRONTEND_MIGRATION_PLAN.md`](docs/FRONTEND_MIGRATION_PLAN.md) —— 前端改造计划（历史）
- [`SECURITY.md`](SECURITY.md) —— 安全模型

### 服务映射

| 环境 | 服务 | 端口 | 说明 |
| --- | --- | --- | --- |
| 本地开发 | frontend (Vite) | 5173 | 代理 `/api` `/media` `/static` 到后端 |
| 本地开发 | backend (Django) | 8000 | 开发服务 |
| 生产 | nginx | 80/443 | TLS 终止 + SPA 静态 + `/api` 反代 |
| 生产 | web (Daphne) | 内网 | Django ASGI |
| 生产 | worker (RQ) | 内网 | 后台异步任务（可选） |
| 生产 | db (MySQL) / redis | 内网 | 数据 / 缓存会话队列 |

## 配置

1. 复制环境变量模板并填写：
   ```bash
   cp .env.example .env
   ```
2. 生产环境准备证书目录：`./certs/ncnetstudent.top.pem`、`./certs/ncnetstudent.top.key`。
3. 确保 `SECRET` 文件存在（Django `SECRET_KEY`）。

## 本地开发

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

另开终端：

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`

## 生产部署

```bash
docker compose up -d --build
```

- Nginx 直接服务构建后的 SPA（`docker/nginx.Dockerfile` 多阶段构建），并反代 `/api/`、`/admin/`。
- `web` 通过 `/api/v1/health/` 健康检查；`nginx` 依赖其健康后启动。
- `worker`（RQ）随 Compose 可选启动，消费 Redis 队列。

## 镜像与 CI/CD

```bash
docker build -t ncbcnet-web:latest .
docker build -f docker/nginx.Dockerfile -t ncbcnet-nginx:latest .
```

GitHub Actions（`.github/workflows/docker-image.yml`）：后端测试 + `lint-imports`（架构边界）→ 前端构建 →
push 后构建并推送两个镜像到 GHCR（`ncbcnet-web`、`ncbcnet-nginx`）。

## 对象存储与备份（可选，阶段三）

- 媒体可迁移到 S3 兼容对象存储：配置 `OSS_*` 环境变量后执行
  `python manage.py migrate_media_to_oss --dry-run`。
- 备份：`deploy/backup.sh`（MySQL dump + 媒体 tar + 可选对象存储上传）。

## 说明

- Django 配置环境变量优先（`APP_ENV/DEBUG/DB_*/REDIS_URL/...`）。
- CORS 已移除（同源部署）；CSP 由 Nginx（SPA）与 `SECURE_CSP`（Django 页面）双层下发。
- 详细流程见 `docs/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md`。
