[![](https://img.shields.io/badge/python-3.12-orange.svg)](https://www.python.org/downloads/release/python-3120/)
[![](https://img.shields.io/badge/django-5.1.1-green.svg)](https://docs.djangoproject.com/en/5.1/releases/5.1/)
[![](https://img.shields.io/badge/vite-7.x-blue.svg)](https://vitejs.dev/)
[![](https://img.shields.io/badge/license-AGPL_3.0-000000.svg)](https://www.gnu.org/licenses/agpl-3.0.html)

# NCBCNet
[简体中文](README.md) | [English](README_EN.md)

## 目标
当前版本已重构为更简洁的开发与部署链路，核心原则：
1. **开发环境本地直跑**：后端、前端、MySQL、Redis 在宿主机直接运行，不需要 Docker。
2. **生产环境单点 TLS**：仅 Nginx 处理 HTTPS，Nginx 与 Daphne 间走内网 HTTP。
3. **容器只用于部署**：Docker 镜像和 GitHub Actions 只服务于生产部署与发布。

## 服务映射关系
### 本地开发环境
| 服务 | 端口 | 说明 |
| --- | --- | --- |
| frontend (Vite) | 5173 | 前端开发服务，代理后端 API |
| backend (Django) | 8000 | Django 开发服务 |
| db (MySQL) | 3306 | 本机 MySQL 服务 |
| redis | 6379 | 本机 Redis 服务 |

### 生产环境 (`docker-compose.yml`)
| 服务 | 暴露端口 | 说明 |
| --- | --- | --- |
| nginx | 80 / 443 | TLS 终止、反向代理、静态文件 |
| web (Daphne) | 不对宿主暴露 | 仅内网被 Nginx 转发 |
| db (MySQL) | 不对宿主暴露 | 仅容器网络内可访问 |
| redis | 不对宿主暴露 | 仅容器网络内可访问 |

## 配置方式
1. 复制环境变量模板：
```bash
cp .env.example .env
```
2. 按需修改 `.env` 中数据库账号、主机白名单等配置。
3. 生产环境准备证书目录：
```text
./certs/ncnetstudent.top.pem
./certs/ncnetstudent.top.key
```

## 本地开发（推荐）
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

另开一个终端：

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

- 前端访问：`http://localhost:5173`
- 后端访问：`http://localhost:8000`

## 生产部署
```bash
docker compose up -d --build
```
- Nginx 接收公网流量并处理 TLS。
- Daphne 仅作为内部 ASGI 服务。

## 镜像构建
```bash
docker build -t ncbcnet-web:latest .
```

## GitHub CI/CD
`.github/workflows/docker-image.yml` 已更新为：
1. 后端测试（Django tests）
2. 前端构建（Vite build）
3. 主分支/Deploy 分支 push 后构建并推送镜像到 GHCR

镜像地址格式：
```text
ghcr.io/<your-org-or-user>/ncbcnet
```

## 说明
- Django 配置已改为环境变量优先（`APP_ENV/DEBUG/DB_*/REDIS_URL/...`）。
- 旧的 Daphne 端到端 TLS 模式已改为 Nginx 单点 TLS，降低证书管理复杂度。
- 详细流程见 `docs/DEVELOPMENT_AND_DEPLOYMENT_GUIDE.md`。
