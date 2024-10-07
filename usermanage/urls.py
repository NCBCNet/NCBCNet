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
]
