"""旧 MVT 评论链路兼容路由（ADR-004 评论并入文章域后保留）。

原 comment 应用已删除，但冻结的旧模板（templates/article/detail.html 等）
仍在渲染时以 namespace 'comment' 反向解析评论路由，故将两条兼容路由
放在 article 应用内，并由 NCBCNet/urls.py 以 /comment/ 前缀 + namespace='comment'
包含，保证旧链路 URL 与模板渲染不回归。
"""
from django.urls import path

from article import views

app_name = "comment"
urlpatterns = [
    path('post-comment/<int:article_id>/', views.post_comment, name='post_comment'),
    path('post-comment/<int:article_id>/<int:parent_comment_id>/', views.post_comment, name='comment_reply'),
]
