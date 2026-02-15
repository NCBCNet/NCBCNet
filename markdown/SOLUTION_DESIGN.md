# Nginx + Daphne 异步大文件上传下载网盘方案

## 概述

本方案实现了一个基于 Django + Daphne + Nginx 的云盘系统，支持大文件的异步上传下载、文件夹管理和用户权限控制。

## 核心技术栈

- **后端框架**: Django 5.1.1
- **ASGI服务器**: Daphne 4.2.1
- **Web服务器**: Nginx (反向代理和静态文件服务)
- **数据库**: SQLite (开发) / MySQL (生产)
- **前端**: Bootstrap 5.3.3 + JavaScript

## 架构设计

```
客户端
  ↓
Nginx (端口 443/80)
  ↓ 反向代理
Daphne (端口 8000)
  ↓
Django 应用
  ↓
文件系统 + 数据库
```

## 主要功能

### 1. 文件夹管理
- **数据模型**: `Folder` 模型支持父子关系，实现无限层级文件夹
- **用户隔离**: 每个用户只能看到自己的文件夹和文件
- **操作功能**: 
  - 创建文件夹
  - 删除文件夹（级联删除子文件夹和文件）
  - 文件夹导航
  - 面包屑导航

### 2. 大文件上传

#### Nginx 配置
```nginx
server {
    client_max_body_size 2G;              # 支持最大2GB文件
    client_body_timeout 300s;             # 请求体超时
    client_body_buffer_size 128k;         # 缓冲区大小
    
    location / {
        proxy_pass https://0.0.0.0:8000;
        proxy_request_buffering off;      # 禁用缓冲，流式上传
        proxy_http_version 1.1;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

#### 前端实现
- **XMLHttpRequest Level 2**: 使用 `xhr.upload.progress` 事件监听上传进度
- **Bootstrap 模态框**: 美观的进度条显示界面
- **实时信息显示**:
  - 上传百分比
  - 实时上传速度
  - 预计剩余时间
  - 用户名和文件信息

#### 后端处理
```python
@login_required
def FileUpload(request):
    uploaded_file = form.save(commit=False)
    uploaded_file.owner = request.user  # 用户关联
    uploaded_file.original_name = request.FILES['file'].name
    uploaded_file.file_size = request.FILES['file'].size
    uploaded_file.save()
```

### 3. 高效文件下载

#### X-Accel-Redirect 方案
使用 Nginx 的内部重定向功能，实现零拷贝高效下载：

**Django 视图**:
```python
def FileDownload(request, id):
    file_instance = get_object_or_404(UploadedFile, id=id, owner=request.user)
    
    # 生产环境使用 X-Accel-Redirect
    internal_path = file_path.replace(settings.MEDIA_ROOT, '/protected')
    response = HttpResponse()
    response['X-Accel-Redirect'] = internal_path
    response['Content-Disposition'] = f'attachment; filename="{file.original_name}"'
    return response
```

**Nginx 配置**:
```nginx
location /protected/ {
    internal;                    # 仅允许内部访问
    alias /usr/mediafiles/;      # 实际文件路径
    sendfile on;                 # 高效传输
    sendfile_max_chunk 1m;
    tcp_nopush on;
    tcp_nodelay on;
}
```

**优势**:
- Nginx 直接发送文件，不经过 Python/Django
- 零拷贝技术，降低 CPU 和内存使用
- 支持断点续传
- 更高的并发处理能力

### 4. 优化的网页布局

#### 响应式卡片设计
- **网格布局**: CSS Grid 实现自适应布局
- **悬停效果**: 卡片悬停动画效果
- **图标系统**: Font Awesome 图标区分文件和文件夹
- **移动端优化**: 媒体查询适配小屏幕设备

#### UI 组件
- **渐变色头部**: 视觉吸引力强
- **统计卡片**: 显示文件夹数量、文件数量等
- **面包屑导航**: 清晰的路径指示
- **操作按钮**: 下载、删除等功能按钮

### 5. 用户权限控制

所有操作都经过用户认证和授权：
```python
@login_required(login_url='usermanage:login')
def FileList(request):
    # 只显示当前用户的文件
    files = UploadedFile.objects.filter(owner=request.user)
    folders = Folder.objects.filter(owner=request.user)
```

## 数据模型

### Folder 模型
```python
class Folder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, 
                              on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

### UploadedFile 模型
```python
class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    original_name = models.CharField(max_length=255)
    folder = models.ForeignKey(Folder, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField(default=0)
```

## 性能优化

### 1. Nginx 层面
- 静态文件缓存 (expires 30d)
- Gzip 压缩
- HTTP/2 支持
- SSL/TLS 优化

### 2. Django 层面
- 数据库查询优化
- 用户权限过滤
- 文件路径索引

### 3. 前端层面
- AJAX 异步上传
- 进度条实时更新
- 大文件提示优化

## 安全性

1. **用户隔离**: 每个用户只能访问自己的文件
2. **CSRF 保护**: Django CSRF 中间件
3. **SSL/TLS**: 强制 HTTPS
4. **路径保护**: X-Accel-Redirect 防止直接访问
5. **文件大小限制**: 防止恶意上传

## 部署建议

### 生产环境配置
1. 使用 systemd 管理 Daphne 服务
2. 配置 nginx 反向代理
3. 设置文件存储路径权限
4. 配置 SSL 证书
5. 启用日志记录

### 扩展性
- 可以集成对象存储 (如 AWS S3, 阿里云 OSS)
- 支持文件分享链接
- 添加文件预览功能
- 实现文件版本控制

## 总结

本方案提供了一个完整的、可扩展的云盘解决方案，充分利用了 Nginx、Daphne 和 Django 的优势：

- **Nginx**: 高效处理静态文件和大文件下载
- **Daphne**: ASGI 异步处理能力
- **Django**: 完善的 ORM 和用户管理系统
- **Bootstrap**: 现代化的响应式界面

通过合理的架构设计和性能优化，系统能够稳定处理大文件的上传下载，同时提供良好的用户体验。
