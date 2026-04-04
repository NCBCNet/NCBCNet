from django.urls import path

from article import views

app_name = "article"
urlpatterns = [
    path('', views.article_list, name='list'),
    path('article_detail/<int:id>/', views.article_detail, name='article_detail'),
    path('article_create/',views.article_create, name='article_create'),
    path('article_update/<int:id>/', views.article_update, name='article_update'),
    path('article_delete/<int:id>/', views.article_delete, name='article_delete'),
    path('increase_likes/<int:id>/',views.IncreaseLikesView.as_view(),name='increase_likes'),
    # JSON API endpoints for React frontend
    path('api/list/', views.article_list_api, name='api_list'),
    path('api/detail/<int:id>/', views.article_detail_api, name='api_detail'),
    path('api/create/', views.article_create_api, name='api_create'),
    path('api/like/<int:id>/', views.article_like_api, name='api_like'),
]
