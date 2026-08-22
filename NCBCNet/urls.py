"""
URL configuration for NCBCNet project.

- `/api/v1/`  前后端分离 API（HttpOnly Cookie JWT 认证）
- `/admin/`   Django Admin（Session 认证，保留）
- 其余模板路由为旧 MVT 链路，M1 上线后由 Nginx 直接服务 SPA 静态资源而“冻结”，
  待 SPA 全功能验收后下线。
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.views import serve
from django.urls import include, path
from server import views

urlpatterns = [
    path('', views.index),
    path('favicon.ico', serve, {'path': 'server/favicon.ico'}),
    path('admin/', admin.site.urls),

    # 旧 MVT 模板链路（阶段一冻结，保留兼容）
    # 评论已并入 article 域（ADR-004）：兼容路由由 article.comment_urls 提供，
    # URL 前缀与 namespace 保持原样，模板与旧链路不受影响。
    path('server/', include('server.urls', namespace='server')),
    path('article/', include('article.urls', namespace='article')),
    path('usermanage/', include('usermanage.urls', namespace='usermanage')),
    path('comment/', include('article.comment_urls', namespace='comment')),
    path('file_up/', include('file_save.urls', namespace='file_save')),
    path('mdeditor/', include('mdeditor.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),

    # 前后端分离 API（v1）
    path('api/v1/', include('api.urls')),
]

# OpenAPI 文档（drf-spectacular，可选依赖）
try:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    ]
except ImportError:
    pass

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
