# NCBCNet 安全策略与安全模型

## 支持版本

| 版本 | 安全更新 |
| ---- | -------- |
| 当前开发分支（main / Deploy） | :white_check_mark: |
| 已归档的旧模板版本 | :x: |

## 报告漏洞

请勿在公开 issue 中披露漏洞。请通过私有渠道联系维护者，说明：

1. 受影响组件与版本；
2. 复现步骤（最小可复现样例）；
3. 影响范围与严重程度判断。

预期在 72 小时内确认收到，30 天内给出处置结论（修复 / 拒绝 / 需要更多信息）。

---

## 安全模型

### 1. 认证（HttpOnly Cookie JWT）

- access / refresh token 均由后端写入 **HttpOnly + Secure + SameSite** Cookie，前端 JavaScript 无法读取，
  从根上消除「localStorage 存 token 被 XSS 窃取」的风险。
- access Cookie `nc_access`（2h，path `/`），refresh Cookie `nc_refresh`（7d，path `/api/v1/auth/`，仅认证端点可见）。
- 刷新采用轮换机制（`ROTATE_REFRESH_TOKENS`）。
- 后端实现见 `api/authentication.py`、`api/views/auth.py`。

### 2. CSRF 防护

- 所有 `/api/` 写请求（POST/PUT/PATCH/DELETE）强制 CSRF 校验（复用 Django 内建 `CsrfViewMiddleware` 的
  Origin/Referer + token 校验），见 `api/middleware.py`。
- 前端在挂载时调用 `GET /api/v1/auth/csrf/` 获取 `csrftoken` Cookie，并在每个写请求回填 `X-CSRFToken` 头。
- 登录成功后轮换 CSRF token（防 login CSRF）。

### 3. 授权（对象级访问控制）

- 文章：仅作者可更新/删除（`get_queryset` 按 `author` 过滤）。
- 文件/文件夹：仅 `owner` 可见、可删除、可切换共享。
- 共享文件：`share=True` 的文件对登录用户可见、可下载。
- **私有文件下载**：不直接暴露媒体路径。前端先调用 `GET /api/v1/files/{id}/download-url/`
  （校验 owner 或 share），换取带 HMAC 签名 + 过期时间的短时下载链接，再以 `<a href>` 触发下载；
  `GET /api/v1/files/{id}/download/` 校验签名与过期后流式返回。见 `api/views/files.py`。
- Nginx 侧 `/media/uploads/` 直接 `403`，阻断绕过鉴权的原始路径访问。

### 4. 传输与内容安全

- TLS 由 Nginx 单点终止（TLSv1.2/1.3），内部 HTTP；`SECURE_SSL_REDIRECT` / HSTS / Secure Cookie 由环境变量控制。
- **CSP**：SPA 页面由 Nginx 下发 `Content-Security-Policy`（`script-src 'self'`，禁第三方脚本）；
  Django 服务的 Admin/旧模板由 `SECURE_CSP` 收紧。见 `nginx/nginx.conf` 与 `NCBCNet/settings.py`。
- **CORS**：同源部署，移除 `django-cors-headers` 与 `CORS_ALLOW_ALL_ORIGINS`，浏览器默认同源策略即最严白名单。
- 用户富文本/Markdown 内容在前端经 **DOMPurify** 消毒后再渲染。

### 5. 限流

- DRF throttle：登录 `5/min`、注册 `3/min`、上传 `30/min`（`api/throttles.py`），统一替代旧的 `django-ratelimit`。

### 6. 密钥与配置

- 密钥经环境变量 / `SECRET` 文件注入，`.env` 不入镜像、不入仓库；模板见 `.env.example`。
- 生产 `DEBUG=false`；`ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` 按域名白名单收紧。

## 已知待加强项（按优先级）

1. refresh token 未接入 blacklist（登出为客户端删 Cookie；旧 refresh 在到期前仍有效）——后续可启用 `rest_framework_simplejwt.token_blacklist`。
2. 大文件下载目前经 Django `FileResponse` 流式；更高吞吐可切 Nginx `X-Accel-Redirect`（`/protected/` 已保留）或对象存储签名 URL（阶段三）。
3. 头像等 `/media/` 资源为公开读，如需收紧可改签名访问。
