# ---- Build Stage ----
FROM python:3.12-slim as builder

# 设置工作目录
WORKDIR /app

# 更新 apt 包列表并安装编译依赖
RUN apt-get update && apt-get install -y build-essential && apt-get clean

# 升级 pip
RUN python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

# 拷贝依赖文件并安装依赖，以便利用 Docker 缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple


# ---- Final Stage ----
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 创建一个非 root 用户来运行应用
RUN useradd -m -s /bin/bash appuser
USER appuser

# 从 builder 阶段拷贝虚拟环境
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 拷贝应用代码
COPY . .

# 收集静态文件
RUN python3 manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "NCBCNet.asgi:application"]