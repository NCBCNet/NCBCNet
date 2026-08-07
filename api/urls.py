from django.urls import path

from api.views.auth import (
    RegisterView,
    UserDetailView,
    UserDeleteView,
    CheckAuthView,
)
from api.views.articles import (
    ArticleListView,
    ArticleDetailView,
    ArticleCreateView,
    ArticleUpdateView,
    ArticleDeleteView,
    IncreaseLikesView,
    ArticleColumnListView,
)
from api.views.files import (
    FolderListView,
    FolderDeleteView,
    FileListView,
    FileUploadView,
    FileDeleteView,
    FileShareToggleView,
    SharedFileListView,
)
from api.views.comments import (
    CommentCreateView,
    CommentReplyView,
)

urlpatterns = [
    # 认证
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
]
