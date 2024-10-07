from django.contrib import admin
from django.urls import path

from server import views

app_name = "server"
urlpatterns = [
    path('', views.index, name='index'),
    path('easter_egg/114514/1/',views.easter_egg_1,name='easter_egg_1'),
]
