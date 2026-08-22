# NCBCNet Docker 部署与镜像构建指南

> 本文档说明 Docker 部署流程、镜像构建方法及常用运维操作。

---

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose                          │
├─────────────────────────────────────────────────────────────┤
│  nginx (TLS)  →  web (Daphne)  →  db (PostgreSQL)          │
│      ↓              ↓                   ↓                    │
│  SPA静态        REST API          数据存储                   │
│                                                              │
│  redis (缓存/队列)  ←  worker (RQ后台任务)                  │
└─────────────────────────────────────────────────────────────┘
```

### 服务说明

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| nginx | ncbcnet-nginx | 80, 443 | TLS终止 + SPA + API反代 |
| web | ncbcnet-web | 8000 | Django ASGI (Daphne) |
| db | postgres:16-alpine | 5432 | PostgreSQL 数据库 |
| redis | redis:7-alpine | 6379 | 缓存/会话/队列 |
| worker | ncbcnet-web | - | RQ 后台任务 |

---

## 2. 镜像构建

### 2.1 镜像清单

| 镜像 | Dockerfile | 用途 |
|------|------------|------|
| ncbcnet-web | ./Dockerfile | Django后端 + RQ worker |
| ncbcnet-nginx | ./docker/nginx.Dockerfile | Nginx + SPA静态 |

### 2.2 构建命令

```bash
# 手动构建
docker build -t ncbcnet-web:latest .
docker build -f docker/nginx.Dockerfile -t ncbcnet-nginx:latest .

# Compose 构建
docker compose build
docker compose up -d --build
```

### 2.3 ncbcnet-web 镜像要点

- 基础镜像: python:3.12-slim
- 依赖: psycopg[binary]==3.2.9 (预编译wheel，无需系统库)
- 用户: 非root用户 `app` 运行
- 入口: 自动执行 migrate + collectstatic
- 命令: daphne -b 0.0.0.0 -p 8000 NCBCNet.asgi:application

### 2.4 ncbcnet-nginx 镜像要点

- 多阶段构建: node:20-alpine 构建 → nginx:1.27-alpine 运行
- 最终镜像仅含 Nginx + SPA静态，约25MB
- 配置: SPA路由、API反代、TLS、CSP

---

## 3. 环境变量配置

### 3.1 必需变量 (.env)

```bash
# 基础
APP_ENV=production
DEBUG=false

# 安全密钥 (必须随机生成)
DJANGO_SECRET_KEY=<随机50字符>

# 域名
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# 数据库
DB_ENGINE=postgresql
DB_HOST=db
DB_PORT=5432
DB_NAME=ncnetdb
DB_USER=ncnet
DB_PASSWORD=<安全密码>

# Redis
REDIS_URL=redis://redis:6379/1

# HTTPS
ENABLE_HTTPS_REDIRECT=true
AUTH_COOKIE_SECURE=true
```

### 3.2 生成密钥

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 4. 部署流程

### 4.1 首次部署

```bash
# 1. 克隆代码
git clone https://github.com/NCBCNet/NCBCNet.git && cd NCBCNet

# 2. 配置环境
cp .env.example .env && vim .env

# 3. 准备证书
mkdir -p certs
# 放入: certs/yourdomain.com.pem, certs/yourdomain.com.key

# 4. 创建SECRET文件
python -c "import secrets; print(secrets.token_urlsafe(50))" > SECRET

# 5. 构建启动
docker compose up -d --build

# 6. 创建管理员
docker compose exec web python manage.py createsuperuser

# 7. 验证
curl https://yourdomain.com/api/v1/health/
```

### 4.2 更新部署

```bash
git pull
docker compose up -d --build
docker compose exec web python manage.py migrate  # 如有迁移
docker image prune -f
```

---

## 5. 常用运维命令

### 5.1 服务管理

```bash
docker compose ps                    # 状态
docker compose logs -f web          # 日志
docker compose restart web          # 重启
docker compose down                 # 停止
docker compose down -v              # 停止并删卷(危险)
```

### 5.2 数据库操作

```bash
docker compose exec db psql -U ncnet -d ncnetdb    # 进入PSQL
docker compose exec db pg_dump -U ncnet ncnetdb > backup.sql  # 备份
./deploy/backup.sh                                # 使用脚本备份
```

### 5.3 Django 命令

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
docker compose exec web python manage.py check --deploy
```

### 5.4 进入容器

```bash
docker compose exec web bash        # 后端容器
docker compose exec db sh           # 数据库容器
docker compose exec -u root web bash  # root用户
```

---

## 6. 数据持久化

| 卷名 | 路径 | 内容 |
|------|------|------|
| db_data | /var/lib/postgresql/data | PostgreSQL数据 |
| redis_data | /data | Redis持久化 |
| static_data | /app/staticfiles | Django静态文件 |
| media_data | /app/mediafiles | 用户上传文件 |

```bash
docker volume ls                    # 列出卷
docker volume inspect ncbcnet_db_data  # 详情
```

---

## 7. 备份与恢复

### 7.1 备份

```bash
# 数据库
docker compose exec db pg_dump -U ncnet ncnetdb | gzip > db.sql.gz

# 媒体文件
docker run --rm -v ncbcnet_media_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/media.tar.gz -C /data .

# 使用脚本
./deploy/backup.sh
```

### 7.2 恢复

```bash
gunzip -c db.sql.gz | docker compose exec -T db psql -U ncnet ncnetdb
docker run --rm -v ncbcnet_media_data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/media.tar.gz -C /data
```

---

## 8. CI/CD (GitHub Actions)

项目自动构建推送镜像到 GHCR:

```yaml
# .github/workflows/docker-image.yml
on: push: branches: [main]
jobs:
  build:
    - 后端测试
    - 前端构建
    - 构建推送 ncbcnet-web → ghcr.io/ncbcnet/ncbcnet-web:latest
    - 构建推送 ncbcnet-nginx → ghcr.io/ncbcnet/ncbcnet-nginx:latest
```

拉取预构建镜像:

```bash
docker pull ghcr.io/ncbcnet/ncbcnet-web:latest
docker pull ghcr.io/ncbcnet/ncbcnet-nginx:latest
```

---

## 9. 故障排查

### 常见问题

| 问题 | 排查命令 |
|------|----------|
| 容器无法启动 | docker compose logs web |
| 数据库连接失败 | docker compose exec db pg_isready -U ncnet |
| 静态文件404 | docker compose exec web python manage.py collectstatic |
| 健康检查失败 | docker compose exec web curl http://127.0.0.1:8000/api/v1/health/ |

### 调试

```bash
docker compose exec web env | grep DB_   # 检查环境变量
docker compose exec web ping db          # 测试网络
docker stats                             # 资源使用
```

---

## 10. 安全加固

- 镜像使用非root用户运行
- 仅nginx暴露端口，内部服务不对外
- .env 和 SECRET 不提交Git (.gitignore已配置)
- 生产必须配置真实 SECRET_KEY 和 ALLOWED_HOSTS

---

## 11. 快速参考

```bash
docker compose up -d --build     # 一键部署
docker compose ps                # 状态
docker compose logs -f           # 日志
docker compose restart           # 重启
docker compose down              # 停止
docker compose exec web bash     # 进入后端
docker compose exec db psql      # 进入数据库
```

---

## 相关文档

- [GUIDE.md](./GUIDE.md) - 统一操作指南
- [ARCHITECTURE_ROADMAP.md](./ARCHITECTURE_ROADMAP.md) - 架构路线图
- [SECURITY.md](../SECURITY.md) - 安全策略
