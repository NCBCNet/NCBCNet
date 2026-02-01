from django.urls import path

from . import views

app_name = "file_save"
urlpatterns = [
    path('file_list/', views.FileList, name='file_list'),
    path('file_del/<int:id>/',views.FileDelete,name='file_delete'),
]
