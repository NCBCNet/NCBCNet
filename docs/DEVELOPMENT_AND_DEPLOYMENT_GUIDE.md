# NCBCNet 开发与部署说明

## 1. 总体原则

当前项目分成两条完全不同的路径：

1. **本地开发**：直接在宿主机运行 Django 和 Vite，不使用 Docker。
2. **生产部署**：使用 Docker 镜像和 Compose 部署，Nginx 负责 HTTPS，Daphne 只提供内网 HTTP。

这样做的目标是让开发更快、排障更简单，同时让部署更标准。

---

## 2. 本地开发工作流

### 2.1 需要的组件

本地开发时建议准备：

| 组件 | 作用 |
| --- | --- |
| Python 3.12 | 运行 Django 后端 |
| Node.js 20+ | 运行 Vite 前端 |
| MySQL 8 | 业务数据库 |
| Redis 7 | 缓存、会话 |

> 开发阶段不需要 Docker。数据库和 Redis 直接安装在本机即可，或者使用你自己的本机服务管理方式。

### 2.2 首次准备

1. 复制环境变量模板：

```bash
cp .env.example .env
```

2. 按本地环境修改 `.env`：

```env
DEBUG=true
APP_ENV=development
DB_ENGINE=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=ncnetdb
DB_USER=ncnet
DB_PASSWORD=your_db_password
REDIS_URL=redis://127.0.0.1:6379/1
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost
ENABLE_HTTPS_REDIRECT=false
```

3. 安装 Python 依赖：

```bash
pip install -r requirements.txt
```

4. 安装前端依赖：

```bash
cd frontend
npm install
```

### 2.3 启动顺序

建议顺序如下：

1. 启动 MySQL
2. 启动 Redis
3. 启动 Django 后端
4. 启动 Vite 前端

### 2.4 后端启动

在项目根目录执行：

```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

后端默认监听：

- `http://127.0.0.1:8000`

### 2.5 前端启动

进入 `frontend/` 后执行：

```bash
npm run dev -- --host 0.0.0.0 --port 5173
```

前端默认监听：

- `http://127.0.0.1:5173`

### 2.6 前后端联调

前端通过 Vite 代理访问后端 API。  
如果你的后端运行在本地 `8000` 端口，默认代理目标就是：

```text
http://127.0.0.1:8000
```

如果你改了后端端口，可以设置：

```env
VITE_PROXY_TARGET=http://127.0.0.1:8000
```

### 2.7 常用开发命令

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py test --settings=NCBCNet.test_settings
cd frontend && npm run build
```

### 2.8 本地开发注意事项

1. 本地开发不使用 Nginx。
2. 本地开发不使用 Docker。
3. 本地开发不需要构建镜像。
4. 生产相关的 TLS、证书挂载、镜像推送，仅在部署阶段使用。

---

## 3. 生产部署工作流

### 3.1 使用场景

生产环境使用：

- Docker 镜像
- Docker Compose
- Nginx TLS
- Daphne 内网 HTTP

### 3.2 部署前准备

1. 准备 `.env`
2. 准备证书文件：

```text
./certs/ncnetstudent.top.pem
./certs/ncnetstudent.top.key
```

3. 确保数据库、Redis 配置正确

### 3.3 启动部署

```bash
docker compose up -d --build
```

### 3.4 服务职责

| 服务 | 职责 |
| --- | --- |
| nginx | 对外 HTTPS 入口、反代、静态文件 |
| web | Django ASGI 应用 |
| db | MySQL |
| redis | 缓存与会话 |

### 3.5 生产请求链路

```text
浏览器 -> Nginx(HTTPS) -> Daphne(HTTP) -> Django
```

静态文件和媒体文件都由 Nginx 直接读取挂载卷。

---

## 4. 镜像与 CI/CD

### 4.1 镜像构建

```bash
docker build -t ncbcnet-web:latest .
```

如果 Docker Hub 拉取慢或受限，可以覆盖基础镜像：

```bash
docker build --build-arg PYTHON_BASE_IMAGE=m.daocloud.io/docker.io/library/python:3.12-slim -t ncbcnet-web:latest .
```

### 4.2 GitHub Actions

CI 流程包含：

1. 后端测试
2. 前端构建
3. push 后构建并推送 GHCR 镜像

---

## 5. 目录与文件说明

| 文件 | 作用 |
| --- | --- |
| `docker-compose.dev.yml` | 旧式容器开发方案，当前推荐不作为日常开发入口 |
| `docker-compose.yml` | 生产部署方案 |
| `Dockerfile` | 生产镜像构建文件 |
| `docker/entrypoint.sh` | 容器启动初始化脚本 |
| `requirements.docker.txt` | 镜像/CI 专用依赖 |
| `README.md` | 中文入口说明 |

---

## 6. 推荐实践

1. 本地调试优先走宿主机直跑。
2. 只在部署时使用镜像。
3. 把数据库、Redis、证书、域名、缓存地址全部放进环境变量。
4. 生产环境只保留 Nginx 对外暴露。

