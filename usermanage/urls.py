from django.contrib import admin
from django.urls import path

from . import views

app_name = "usermanage"
urlpatterns = [
    path("login/",views.user_login,name="login"),
    path("logout/",views.user_logout,name="logout"),
    path("register/",views.user_register,name="register"),
    path("delete/<int:id>/",views.user_delete,name="delete"),
    path("edit/<int:id>/",views.edit_profile,name="edit_profile"),
    # JSON API endpoints for React frontend
    path("api/user/", views.user_info_api, name="api_user"),
    path("api/logout/", views.user_logout_api, name="api_logout"),
]
