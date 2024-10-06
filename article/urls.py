from django.contrib import admin
from django.urls import path

from article import views

app_name = "article"
urlpatterns = [
    path('', views.article_list, name='list'),
    path('article_detail/<int:id>/', views.article_detail, name='article_detail'),
    path('article_create/',views.article_create, name='article_create'),
    path('article_update/<int:id>/', views.article_update, name='article_update'),
    path('article_delete/<int:id>/', views.article_delete, name='article_delete'),
]
