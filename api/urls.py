from django.urls import path

from api.views.auth import (
    CheckAuthView,
    CsrfCookieView,
    LoginView,
    LogoutView,
    RefreshView,
    RegisterView,
    UserDeleteView,
    UserDetailView,
)
from api.views.articles import (
    ArticleColumnListView,
    ArticleCreateView,
    ArticleDeleteView,
    ArticleDetailView,
    ArticleListView,
    ArticleUpdateView,
    IncreaseLikesView,
)
from api.views.files import (
    FileDeleteView,
    FileDownloadUrlView,
    FileDownloadView,
    FileListView,
    FileShareToggleView,
    FileUploadView,
    FolderDeleteView,
    FolderListView,
    SharedFileListView,
)
from api.views.comments import (
    CommentCreateView,
    CommentReplyView,
)
from api.views.health import HealthView

urlpatterns = [
    # 健康检查
    path('health/', HealthView.as_view(), name='api_health'),

    # 认证（HttpOnly Cookie JWT）
    path('auth/csrf/', CsrfCookieView.as_view(), name='api_csrf'),
    path('auth/login/', LoginView.as_view(), name='api_login'),
    path('auth/logout/', LogoutView.as_view(), name='api_logout'),
    path('auth/refresh/', RefreshView.as_view(), name='api_refresh'),
    path('auth/register/', RegisterView.as_view(), name='api_register'),
    path('auth/me/', UserDetailView.as_view(), name='api_user_detail'),
    path('auth/delete/', UserDeleteView.as_view(), name='api_user_delete'),
    path('auth/check/', CheckAuthView.as_view(), name='api_check_auth'),

    # 文章
    path('articles/', ArticleListView.as_view(), name='api_article_list'),
    path('articles/columns/', ArticleColumnListView.as_view(), name='api_article_columns'),
    path('articles/create/', ArticleCreateView.as_view(), name='api_article_create'),
    path('articles/<int:pk>/', ArticleDetailView.as_view(), name='api_article_detail'),
    path('articles/<int:pk>/update/', ArticleUpdateView.as_view(), name='api_article_update'),
    path('articles/<int:pk>/delete/', ArticleDeleteView.as_view(), name='api_article_delete'),
    path('articles/<int:pk>/like/', IncreaseLikesView.as_view(), name='api_article_like'),

    # 评论
    path('articles/<int:article_id>/comments/', CommentCreateView.as_view(), name='api_comment_create'),
    path('articles/<int:article_id>/comments/<int:parent_comment_id>/reply/', CommentReplyView.as_view(), name='api_comment_reply'),

    # 文件
    path('folders/', FolderListView.as_view(), name='api_folder_list'),
    path('folders/<int:pk>/delete/', FolderDeleteView.as_view(), name='api_folder_delete'),
    path('files/', FileListView.as_view(), name='api_file_list'),
    path('files/upload/', FileUploadView.as_view(), name='api_file_upload'),
    path('files/shared/', SharedFileListView.as_view(), name='api_shared_files'),
    path('files/<int:pk>/delete/', FileDeleteView.as_view(), name='api_file_delete'),
    path('files/<int:pk>/share/', FileShareToggleView.as_view(), name='api_file_share'),
    path('files/<int:pk>/download-url/', FileDownloadUrlView.as_view(), name='api_file_download_url'),
    path('files/<int:pk>/download/', FileDownloadView.as_view(), name='api_file_download'),
]
