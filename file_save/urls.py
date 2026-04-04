from django.urls import path

from . import views

app_name = "file_save"
urlpatterns = [
    path('file_list/', views.FileList, name='file_list'),
    path('file_upload/', views.FileUpload, name='file_upload'),
    path('file_delete/<int:id>/', views.FileDelete, name='file_delete'),
    path('file_download/<int:id>/', views.FileDownload, name='file_download'),
    path('folder_create/', views.FolderCreate, name='folder_create'),
    path('folder_delete/<int:id>/', views.FolderDelete, name='folder_delete'),
    # JSON API endpoints for React frontend
    path('api/list/', views.file_list_api, name='api_list'),
    path('api/delete/<int:id>/', views.file_delete_api, name='api_delete'),
]
